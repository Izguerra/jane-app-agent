import { desc, and, eq, isNull, count } from 'drizzle-orm';
import { db } from './drizzle';
import { activityLogs, teamMembers, teams, users, workspaces, agents, customers, communications } from './schema';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth/session';

export async function getUser() {
  const sessionCookie = (await cookies()).get('session');
  if (!sessionCookie || !sessionCookie.value) {
    return null;
  }

  let sessionData;
  try {
    sessionData = await verifyToken(sessionCookie.value);
  } catch (error) {
    return null;
  }

  if (
    !sessionData ||
    !sessionData.user ||
    typeof sessionData.user.id !== 'string'
  ) {
    return null;
  }

  if (new Date(sessionData.expires) < new Date()) {
    return null;
  }

  try {
    const user = await db
      .select()
      .from(users)
      .where(and(eq(users.id, sessionData.user.id), isNull(users.deletedAt)))
      .limit(1);

    if (user.length === 0) {
      return null;
    }

    return user[0];
  } catch (error) {
    console.error('Failed to fetch user from DB:', error);
    return null;
  }
}

export async function getTeamByStripeCustomerId(customerId: string) {
  const result = await db
    .select()
    .from(teams)
    .where(eq(teams.stripeCustomerId, customerId))
    .limit(1);

  return result.length > 0 ? result[0] : null;
}

export async function updateTeamSubscription(
  teamId: string,
  subscriptionData: {
    stripeSubscriptionId: string | null;
    stripeProductId: string | null;
    planName: string | null;
    subscriptionStatus: string;
  }
) {
  await db
    .update(teams)
    .set({
      ...subscriptionData,
      updatedAt: new Date()
    })
    .where(eq(teams.id, teamId));
}

export async function getUserWithTeam(userId: string) {
  const result = await db
    .select({
      user: users,
      teamId: teamMembers.teamId,
      role: teamMembers.role
    })
    .from(users)
    .leftJoin(teamMembers, eq(users.id, teamMembers.userId))
    .where(eq(users.id, userId))
    .limit(1);

  if (result.length === 0) return null;
  return result[0];
}

export async function getActivityLogs() {
  const user = await getUser();
  if (!user) {
    throw new Error('User not authenticated');
  }

  return await db
    .select({
      id: activityLogs.id,
      action: activityLogs.action,
      timestamp: activityLogs.timestamp,
      ipAddress: activityLogs.ipAddress,
      userName: users.name
    })
    .from(activityLogs)
    .leftJoin(users, eq(activityLogs.userId, users.id))
    .where(eq(activityLogs.userId, user.id))
    .orderBy(desc(activityLogs.timestamp))
    .limit(10);
}

export async function getTeamForUser() {
  const user = await getUser();
  if (!user) {
    return null;
  }

  try {
    const result = await db.query.teamMembers.findFirst({
      where: eq(teamMembers.userId, user.id),
      with: {
        team: {
          with: {
            teamMembers: {
              with: {
                user: {
                  columns: {
                    id: true,
                    name: true,
                    email: true
                  }
                }
              }
            }
          }
        }
      }
    });

    return result?.team || null;
  } catch (error) {
    console.error('Failed to fetch team from DB:', error);
    return null;
  }
}

export async function getWorkspaceForUser() {
  const user = await getUser();
  if (!user) {
    return null;
  }

  try {
    const userTeam = await db
      .select({ teamId: teamMembers.teamId })
      .from(teamMembers)
      .where(eq(teamMembers.userId, user.id))
      .limit(1);

    if (userTeam.length === 0) {
      return null;
    }

    // Get ALL workspaces for this team
    const allWorkspaces = await db
      .select()
      .from(workspaces)
      .where(eq(workspaces.teamId, userTeam[0].teamId));

    if (allWorkspaces.length === 0) {
      return null;
    }

    // If only one workspace, return it
    if (allWorkspaces.length === 1) {
      return allWorkspaces[0];
    }

    // Multiple workspaces: select the one with the most data
    // This matches the backend workspace resolution logic
    const workspaceScores = await Promise.all(
      allWorkspaces.map(async (workspace) => {
        // Count agents, customers, and communications for this workspace
        const agentCountResult = await db
          .select({ count: count() })
          .from(agents)
          .where(eq(agents.workspaceId, workspace.id));

        const customerCountResult = await db
          .select({ count: count() })
          .from(customers)
          .where(eq(customers.workspaceId, workspace.id));

        const commCountResult = await db
          .select({ count: count() })
          .from(communications)
          .where(eq(communications.workspaceId, workspace.id));

        const score =
          (agentCountResult[0]?.count || 0) +
          (customerCountResult[0]?.count || 0) +
          (commCountResult[0]?.count || 0);

        return { workspace, score };
      })
    );

    // Sort by score descending and return the workspace with most data
    workspaceScores.sort((a, b) => Number(b.score) - Number(a.score));
    const primaryWorkspace = workspaceScores[0].workspace;

    console.log(`[getWorkspaceForUser] Found ${allWorkspaces.length} workspaces for team ${userTeam[0].teamId}`);
    console.log(`[getWorkspaceForUser] Selected primary workspace ${primaryWorkspace.id} with score ${workspaceScores[0].score}`);

    return primaryWorkspace;
  } catch (error) {
    console.error('Failed to fetch workspace from DB:', error);
    return null;
  }
}
