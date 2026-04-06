import {
  and,
  eq,
  or,
  desc,
  isNull,
  asc,
} from 'drizzle-orm';
import { db } from './drizzle';
import {
  activityLogs,
  teamMembers,
  teams,
  users,
  workspaces,
  agents,
  customers,
  communications,
  invitations,
  skills,
  agentSkills,
  type User,
  type Team,
} from './schema';
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

    const allWorkspaces = await db
      .select()
      .from(workspaces)
      .where(eq(workspaces.teamId, userTeam[0].teamId))
      .orderBy(asc(workspaces.createdAt));

    if (allWorkspaces.length === 0) {
      return null;
    }

    // If only one workspace, return it
    if (allWorkspaces.length === 1) {
      return allWorkspaces[0];
    }

    // Multiple workspaces: just pick the first one to avoid expensive 60+ count queries.
    // This is much faster and prevents ECONNRESET on slow connections.
    const primaryWorkspace = allWorkspaces[0];

    console.log(`[getWorkspaceForUser] Found ${allWorkspaces.length} workspaces for team ${userTeam[0].teamId}. Selected first: ${primaryWorkspace.id}`);

    return primaryWorkspace;
  } catch (error) {
    console.error('Failed to fetch workspace from DB:', error);
    return null;
  }
}

export async function getAgentsForWorkspace(workspaceId: string) {
  return await db
    .select()
    .from(agents)
    .where(eq(agents.workspaceId, workspaceId))
    .orderBy(desc(agents.createdAt));
}

export async function getActiveAgentForWorkspace(workspaceId: string) {
  // Find active agent, prioritizing recently updated
  const result = await db
    .select()
    .from(agents)
    .where(and(eq(agents.workspaceId, workspaceId), eq(agents.isActive, true)))
    .orderBy(desc(agents.updatedAt))
    .limit(1);

  if (result.length > 0) return result[0];

  // If no active agent, try any agent
  const fallback = await db
    .select()
    .from(agents)
    .where(eq(agents.workspaceId, workspaceId))
    .limit(1);

  return fallback.length > 0 ? fallback[0] : null;
}

export async function getAgentById(agentId: string, workspaceId: string) {
  const result = await db
    .select()
    .from(agents)
    .where(and(eq(agents.id, agentId), eq(agents.workspaceId, workspaceId)))
    .limit(1);

  return result.length > 0 ? result[0] : null;
}

export async function createAgent(data: typeof agents.$inferInsert) {
  const result = await db
    .insert(agents)
    .values({
      ...data,
      id: data.id || `agnt_${Math.random().toString(36).substring(2, 15)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
    .returning();

  return result[0];
}

export async function updateAgent(agentId: string, workspaceId: string, data: Partial<typeof agents.$inferInsert>) {
  const result = await db
    .update(agents)
    .set({
      ...data,
      updatedAt: new Date(),
    })
    .where(and(eq(agents.id, agentId), eq(agents.workspaceId, workspaceId)))
    .returning();

  return result[0];
}

export async function getSkillsCatalog(workspaceId: string) {
  return await db
    .select()
    .from(skills)
    .where(or(eq(skills.isSystem, true), eq(skills.workspaceId, workspaceId)));
}

export async function getSkillsForAgent(agentId: string) {
  return await db
    .select({
      id: skills.id,
      name: skills.name,
      slug: skills.slug,
      category: skills.category,
      instructions: skills.instructions,
    })
    .from(skills)
    .innerJoin(agentSkills, eq(skills.id, agentSkills.skillId))
    .where(and(eq(agentSkills.agentId, agentId), eq(agentSkills.enabled, true)));
}

export async function toggleAgentSkill(agentId: string, skillId: string, workspaceId: string, enabled: boolean) {
  const existing = await db
    .select()
    .from(agentSkills)
    .where(
      and(
        eq(agentSkills.agentId, agentId),
        eq(agentSkills.skillId, skillId),
        eq(agentSkills.workspaceId, workspaceId)
      )
    )
    .limit(1);

  if (existing.length > 0) {
    const result = await db
      .update(agentSkills)
      .set({ enabled, updatedAt: new Date() })
      .where(eq(agentSkills.id, existing[0].id))
      .returning();
    return result[0];
  } else {
    const result = await db
      .insert(agentSkills)
      .values({
        id: `askl_${Math.random().toString(36).substring(2, 15)}`,
        agentId,
        skillId,
        workspaceId,
        enabled,
      })
      .returning();
    return result[0];
  }
}

export async function bulkSyncSkills(agentId: string, workspaceId: string, enabledSkillIds: string[]) {
  // First disable all existing skills for this agent in this workspace
  await db
    .update(agentSkills)
    .set({ enabled: false, updatedAt: new Date() })
    .where(and(eq(agentSkills.agentId, agentId), eq(agentSkills.workspaceId, workspaceId)));

  // Then enable or insert the specified ones
  for (const skillId of enabledSkillIds) {
    const existing = await db
      .select()
      .from(agentSkills)
      .where(
        and(
          eq(agentSkills.agentId, agentId),
          eq(agentSkills.skillId, skillId),
          eq(agentSkills.workspaceId, workspaceId)
        )
      )
      .limit(1);

    if (existing.length > 0) {
      await db
        .update(agentSkills)
        .set({ enabled: true, updatedAt: new Date() })
        .where(eq(agentSkills.id, existing[0].id));
    } else {
      await db.insert(agentSkills).values({
        id: `askl_${Math.random().toString(36).substring(2, 15)}`,
        agentId,
        skillId,
        workspaceId,
        enabled: true,
      });
    }
  }
}
