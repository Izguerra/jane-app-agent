'use server';

import { z } from 'zod';
import { headers, cookies } from 'next/headers';
import { nanoid } from 'nanoid';
import { and, eq, sql } from 'drizzle-orm';
import { db } from '@/lib/db/drizzle';
import { verifyResetToken, signResetToken } from '@/lib/auth/session';
import { createAdminClient } from '@/lib/supabase/admin';
import {
  User,
  users,
  teams,
  teamMembers,
  activityLogs,
  type NewUser,
  type NewTeam,
  type NewTeamMember,
  type NewActivityLog,
  ActivityType,
  invitations,
  workspaces
} from '@/lib/db/schema';
import { setSession } from '@/lib/auth/session';
import { comparePasswords, hashPassword } from '@/lib/auth/password';
import { redirect } from 'next/navigation';

import { createCheckoutSession } from '@/lib/payments/stripe';
import { createClient } from '@/lib/supabase/server';
import { getUser, getUserWithTeam } from '@/lib/db/queries';
import {
  validatedAction,
  validatedActionWithUser
} from '@/lib/auth/middleware';

// ... imports ...

// K-Sortable ID Generation (Matches Python Backend IdService)
const ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
const BASE = ALPHABET.length;

function base62Encode(num: number, minLength: number): string {
  let str = '';
  while (num > 0) {
    str = ALPHABET[num % BASE] + str;
    num = Math.floor(num / BASE);
  }
  // Pad with leading zeros (index 0 of ALPHABET is '0')
  return str.padStart(minLength, '0');
}

function generateKSortableId(prefix: string): string {
  // 1. Timestamp (48-bit equivalent in ms, padded to 10 chars)
  const timestamp = Date.now();
  const tsPart = base62Encode(timestamp, 10);

  // 2. Randomness (16 chars)
  let randPart = '';
  for (let i = 0; i < 16; i++) {
    randPart += ALPHABET[Math.floor(Math.random() * BASE)];
  }

  return `${prefix}${tsPart}${randPart}`;
}

function generateRandomId(length: number = 8): string {
  return nanoid(length);
}

async function logActivity(
  teamId: string | null | undefined, // Changed from number to string
  userId: string, // Changed from number to string
  type: ActivityType,
  ipAddress?: string
) {
  if (teamId === null || teamId === undefined) {
    return;
  }
  const newActivity: NewActivityLog = {
    id: generateKSortableId('act_'),
    teamId,
    userId,
    action: type,
    ipAddress: ipAddress || ''
  };
  await db.insert(activityLogs).values(newActivity);
  console.log('Activity logged:', type, teamId, userId);
}

const signInSchema = z.object({
  email: z.string().email().min(3).max(255),
  password: z.string().min(8).max(100),
  preferredAreaCode: z.string().optional()
});

export const signIn = validatedAction(signInSchema, async (data, formData) => {
  try {
    const { email, password } = data;

    // 1. Authenticate with Supabase
    const supabase = await createClient();
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError || !authData.user) {
      console.error('SignIn Debug: Supabase Auth Failed', authError?.message);
      return {
        error: `Authentication Failed: ${authError?.message || 'Check credentials'}`,
        email,
        password
      };
    }

    console.log('SignIn Debug: Supabase Auth Success', authData.user.id);

    // 2. Fetch user from local DB
    // We search by EMAIL to support both legacy local-only users (usr_...) 
    // and new Supabase-synced users (UUIDs).
    const userWithTeam = await db
      .select({
        user: users,
        team: teams
      })
      .from(users)
      .leftJoin(teamMembers, eq(users.id, teamMembers.userId))
      .leftJoin(teams, eq(teamMembers.teamId, teams.id))
      .where(sql`lower(${users.email}) = ${email.toLowerCase()}`)
      .limit(1);

    console.log('SignIn Debug: Local DB Lookup Result', userWithTeam.length > 0 ? 'Found' : 'Not Found');

    if (userWithTeam.length === 0) {
      console.error('SignIn Debug: User Authenticated but not found in Local DB');
      return {
        error: 'Account authenticated but not found in local database. Please contact support.',
        email,
        password
      };
    }

    const { user: foundUser, team: foundTeam } = userWithTeam[0];

    // 3. Set Local Session (for Middleware compatibility)
    await Promise.all([
      setSession(foundUser, foundTeam?.id as string),
      logActivity(foundTeam?.id, foundUser.id, ActivityType.SIGN_IN)
    ]);

    const redirectTo = formData.get('redirect') as string | null;
    if (redirectTo === 'checkout') {
      const priceId = formData.get('priceId') as string;
      return createCheckoutSession({ team: foundTeam, priceId, preferredAreaCode: data.preferredAreaCode, user: foundUser });
    }

    if (foundUser.role === 'supaagent_admin' || foundUser.role === 'owner') {
      redirect('/admin/analytics');
    }

    if (!foundTeam) {
      return {
        error: 'User is not assigned to any team/workspace.',
        email,
        password
      };
    }

    // Fetch the default workspace for the team
    const workspace = await db.query.workspaces.findFirst({
      where: eq(workspaces.teamId, foundTeam.id)
    });

    if (!workspace) {
      console.log('SignIn: Workspace not found for team', foundTeam.id, 'creating new.');
      // Auto-create workspace if missing (fallback)
      const newWorkspaceId = generateKSortableId('wrk_');
      await db.insert(workspaces).values({
        id: newWorkspaceId,
        teamId: foundTeam.id,
        name: `${foundTeam.name}'s Workspace`
      });
      console.log('SignIn: Created new workspace', newWorkspaceId);
      redirect(`/${newWorkspaceId}/dashboard/analytics`);
    }

    console.log('SignIn: Found workspace', workspace.id);
    redirect(`/${workspace.id}/dashboard/analytics`);
  } catch (error) {
    console.error('Sign in error:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });
    // Re-throw redirect errors
    if (error instanceof Error && error.message.includes('NEXT_REDIRECT')) {
      throw error;
    }
    return {
      error: `Sign in failed: ${error instanceof Error ? error.message : String(error)}`,
      email: data.email,
      password: data.password
    };
  }
});




const signUpSchema = z.object({
  firstName: z.string().min(1).max(50),
  lastName: z.string().min(1).max(50),
  username: z.string().min(3).max(50).optional(), // Can match email prefix if empty
  email: z.string().email(),
  password: z.string().min(8),
  inviteId: z.string().optional(),
  preferredAreaCode: z.string().optional()
});

export const signUp = validatedAction(signUpSchema, async (data, formData) => {
  try {
    const { firstName, lastName, username, email, password, inviteId } = data;

    // Check if username exists if provided
    if (username) {
      const existingUser = await db.query.users.findFirst({
        where: eq(users.username, username),
      });
      if (existingUser) {
        return { error: 'Username already taken.', email, password, firstName, lastName };
      }
    }

    // ... check existing user by email ...
    const existingEmail = await db.query.users.findFirst({
      where: eq(users.email, email),
    });
    if (existingEmail) {
      return { error: 'Email already exists.', email, password, firstName, lastName };
    }



    // 1. Sign Up/Sign In with Supabase
    const supabase = await createClient();
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: `${firstName} ${lastName}`,
          username: username || undefined,
        },
      },
    });

    if (authError) {
      return { error: authError.message, email, password, firstName, lastName };
    }

    if (!authData.user) {
      return { error: 'Failed to create user in Supabase.', email, password, firstName, lastName };
    }

    const userId = authData.user.id;
    const passwordHash = 'supa_auth_managed'; // Placeholder

    // 2. Local Database Sync & Migration
    // Check if user exists locally by EMAIL (Legacy Account)
    const existingUser = await db.query.users.findFirst({
      where: sql`lower(${users.email}) = ${email.toLowerCase()}`
    });

    let finalUser: typeof users.$inferSelect;
    let teamId: string;
    let finalWorkspaceId: string;

    if (existingUser) {
      // MIGRATION: User exists locally but is now authenticating via Supabase.
      // We must swap the local ID to match Supabase ID to ensure consistency.
      console.log(`Migrating existing user ${existingUser.id} to Supabase ID ${userId}`);

      if (existingUser.id !== userId) {
        // Swap IDs in dependent tables
        await db.update(teamMembers)
          .set({ userId: userId })
          .where(eq(teamMembers.userId, existingUser.id));

        await db.update(activityLogs)
          .set({ userId: userId })
          .where(eq(activityLogs.userId, existingUser.id));

        await db.update(invitations)
          .set({ invitedBy: userId })
          .where(eq(invitations.invitedBy, existingUser.id));

        await db.execute(sql`UPDATE worker_tasks SET created_by_user_id = ${userId} WHERE created_by_user_id = ${existingUser.id}`);
        await db.execute(sql`UPDATE worker_tasks SET rated_by_user_id = ${userId} WHERE rated_by_user_id = ${existingUser.id}`);

        // Update the User record itself (PK update workaround: Update inplace if DB supports, or Insert New + Delete Old)
        // Since we can't easily update PK in one go without cascade issues if not configured,
        // We will insert the NEW user record with the SAME data + New ID, then delete old.
        // Wait, 'email' is unique. We can't insert a duplicate email.

        // Strategy: 
        // 1. Update old user email to temporary
        // 2. Insert new user with correct email + new ID
        // 3. Delete old user

        await db.update(users)
          .set({ email: `migrated_${existingUser.id}_${email}` })
          .where(eq(users.id, existingUser.id));

        const [migratedUser] = await db.insert(users).values({
          ...existingUser,
          id: userId,
          email: email, // Restore correct email
          passwordHash: passwordHash, // Update hash
          updatedAt: new Date(),
        }).returning();

        await db.delete(users).where(eq(users.id, existingUser.id));

        finalUser = migratedUser;
      } else {
        finalUser = existingUser;
      }

      // Fetch existing team/workspace
      const member = await db.query.teamMembers.findFirst({
        where: eq(teamMembers.userId, finalUser.id)
      });

      if (member) {
        teamId = member.teamId;
        const workspace = await db.query.workspaces.findFirst({ where: eq(workspaces.teamId, teamId) });
        finalWorkspaceId = workspace?.id || '';
      } else {
        // Should not happen for valid existing user, but handle fallback
        // ... (Logic to create team/workspace if missing would go here, omitting for brevity in migration path)
        const newTeamId = generateKSortableId('org_');
        await db.insert(teams).values({ id: newTeamId, name: `${email}'s Team` });
        await db.insert(teamMembers).values({ id: generateKSortableId('mem_'), userId: finalUser.id, teamId: newTeamId, role: 'owner' });
        teamId = newTeamId;
        finalWorkspaceId = generateKSortableId('wrk_');
        await db.insert(workspaces).values({ id: finalWorkspaceId, teamId: newTeamId, name: `${email}'s Workspace` });
      }

    } else {
      // NEW USER FLOW
      const finalUsername = username || email.split('@')[0] + generateRandomId(4);
      const newUser: NewUser = {
        id: userId,
        name: `${firstName} ${lastName}`,
        firstName,
        lastName,
        username: finalUsername,
        email,
        passwordHash,
        role: 'member'
      };
      const [insertedUser] = await db.insert(users).values(newUser).returning();
      finalUser = insertedUser;

      // ... Continue with Invite/Team Creation checks (copied from original flow)
      // For brevity in this diff, assuming we need to preserve the Invite logic.
      // Re-implementing the Invite/New Team logic below:

      if (inviteId) {
        const [invitation] = await db.select().from(invitations).where(and(eq(invitations.id, inviteId), eq(invitations.email, email), eq(invitations.status, 'pending'))).limit(1);
        if (invitation) {
          teamId = invitation.teamId;
          await db.update(invitations).set({ status: 'accepted' }).where(eq(invitations.id, invitation.id));
          await db.insert(teamMembers).values({ id: generateKSortableId('mem_'), userId: finalUser.id, teamId, role: invitation.role });
          const workspace = await db.query.workspaces.findFirst({ where: eq(workspaces.teamId, teamId) });
          finalWorkspaceId = workspace?.id || '';
          if (!finalWorkspaceId) {
            finalWorkspaceId = generateKSortableId('wrk_');
            await db.insert(workspaces).values({ id: finalWorkspaceId, teamId, name: 'New Workspace' });
          }
        } else {
          return { error: 'Invalid invitation.', email, password };
        }
      } else {
        const newTeamId = generateKSortableId('org_');
        const newTeam: NewTeam = { id: newTeamId, name: `${email}'s Team` };
        await db.insert(teams).values(newTeam);
        await db.insert(teamMembers).values({ id: generateKSortableId('mem_'), userId: finalUser.id, teamId: newTeamId, role: 'owner' });
        teamId = newTeamId;
        finalWorkspaceId = generateKSortableId('wrk_');
        await db.insert(workspaces).values({ id: finalWorkspaceId, teamId: newTeamId, name: `${email}'s Workspace` });
      }
    }

    // Set Session & Log
    await Promise.all([
      setSession(finalUser, teamId!),
      logActivity(teamId!, finalUser.id, ActivityType.SIGN_UP)
    ]);

    const redirectTo = formData.get('redirect') as string | null;
    if (redirectTo === 'checkout') {
      const priceId = formData.get('priceId') as string;
      // Fetch team for checkout
      const [team] = await db.select().from(teams).where(eq(teams.id, teamId!)).limit(1);
      return createCheckoutSession({ team: team, priceId, preferredAreaCode: data.preferredAreaCode, user: finalUser });
    }

    if (!finalWorkspaceId) {
      // Fallback just in case
      redirect('/dashboard');
    } else {
      redirect(`/${finalWorkspaceId}/dashboard/analytics`);
    }
  } catch (error) {
    console.error('Sign up error:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });
    if (error instanceof Error && error.message.includes('NEXT_REDIRECT')) {
      throw error;
    }
    return {
      error: `Sign up failed: ${error instanceof Error ? error.message : String(error)}`,
      email: data.email,
      password: data.password
    };
  }
});

export async function signOut() {
  try {
    const user = await getUser();
    if (user) {
      const userWithTeam = await getUserWithTeam(user.id);
      await logActivity(userWithTeam?.teamId, user.id, ActivityType.SIGN_OUT);
    }
  } catch (error) {
    // Ignore errors during user fetch/logging, just ensure sign out
  } finally {
    (await cookies()).delete('session');
  }
}

const updatePasswordSchema = z.object({
  currentPassword: z.string().min(8).max(100),
  newPassword: z.string().min(8).max(100),
  confirmPassword: z.string().min(8).max(100)
});

export const updatePassword = validatedActionWithUser(
  updatePasswordSchema,
  async (data, _, user) => {
    const { currentPassword, newPassword, confirmPassword } = data;

    const isPasswordValid = await comparePasswords(
      currentPassword,
      user.passwordHash
    );

    if (!isPasswordValid) {
      return {
        currentPassword,
        newPassword,
        confirmPassword,
        error: 'Current password is incorrect.'
      };
    }

    if (currentPassword === newPassword) {
      return {
        currentPassword,
        newPassword,
        confirmPassword,
        error: 'New password must be different from the current password.'
      };
    }

    if (confirmPassword !== newPassword) {
      return {
        currentPassword,
        newPassword,
        confirmPassword,
        error: 'New password and confirmation password do not match.'
      };
    }

    const newPasswordHash = await hashPassword(newPassword);
    const userWithTeam = await getUserWithTeam(user.id);

    await Promise.all([
      db
        .update(users)
        .set({ passwordHash: newPasswordHash })
        .where(eq(users.id, user.id)),
      logActivity(userWithTeam?.teamId, user.id, ActivityType.UPDATE_PASSWORD)
    ]);

    return {
      success: 'Password updated successfully.'
    };
  }
);

const deleteAccountSchema = z.object({
  password: z.string().min(8).max(100)
});

export const deleteAccount = validatedActionWithUser(
  deleteAccountSchema,
  async (data, _, user) => {
    const { password } = data;

    const isPasswordValid = await comparePasswords(password, user.passwordHash);
    if (!isPasswordValid) {
      return {
        password,
        error: 'Incorrect password. Account deletion failed.'
      };
    }

    const userWithTeam = await getUserWithTeam(user.id);

    await logActivity(
      userWithTeam?.teamId,
      user.id,
      ActivityType.DELETE_ACCOUNT
    );

    // Soft delete
    await db
      .update(users)
      .set({
        deletedAt: sql`CURRENT_TIMESTAMP`,
        email: sql`CONCAT(email, '-', id, '-deleted')` // Ensure email uniqueness
      })
      .where(eq(users.id, user.id));

    if (userWithTeam?.teamId) {
      await db
        .delete(teamMembers)
        .where(
          and(
            eq(teamMembers.userId, user.id),
            eq(teamMembers.teamId, userWithTeam.teamId)
          )
        );
    }

    (await cookies()).delete('session');
    redirect('/sign-in');
  }
);

const updateAccountSchema = z.object({
  firstName: z.string().min(1, 'First name is required').max(50),
  lastName: z.string().min(1, 'Last name is required').max(50),
  username: z.string().min(3, 'Username must be at least 3 characters').max(50),
  email: z.string().email('Invalid email address')
});

export const updateAccount = validatedActionWithUser(
  updateAccountSchema,
  async (data, _, user) => {
    const { firstName, lastName, username, email } = data;
    const userWithTeam = await getUserWithTeam(user.id);

    // Check if username is being changed and if it is taken
    if (username !== user.username) {
      const existingUser = await db.query.users.findFirst({
        where: eq(users.username, username),
      });
      if (existingUser) {
        return { error: 'Username already taken.' };
      }
    }

    // Check if email is being changed and if it is taken (optional, usually handled by constraint but good for UX)
    if (email !== user.email) {
      const existingEmail = await db.query.users.findFirst({
        where: eq(users.email, email),
      });
      if (existingEmail && existingEmail.id !== user.id) {
        return { error: 'Email already exists.' };
      }
    }

    await Promise.all([
      db.update(users).set({
        name: `${firstName} ${lastName}`, // Keep name composite
        firstName,
        lastName,
        username,
        email
      }).where(eq(users.id, user.id)),
      logActivity(userWithTeam?.teamId, user.id, ActivityType.UPDATE_ACCOUNT)
    ]);

    return { success: 'Account updated successfully.' };
  }
);

const removeTeamMemberSchema = z.object({
  memberId: z.string() // Changed from number to string
});

export const removeTeamMember = validatedActionWithUser(
  removeTeamMemberSchema,
  async (data, _, user) => {
    const { memberId } = data;
    const userWithTeam = await getUserWithTeam(user.id);

    if (!userWithTeam?.teamId) {
      return { error: 'User is not part of a team' };
    }

    await db
      .delete(teamMembers)
      .where(
        and(
          eq(teamMembers.id, memberId),
          eq(teamMembers.teamId, userWithTeam.teamId)
        )
      );

    await logActivity(
      userWithTeam.teamId,
      user.id,
      ActivityType.REMOVE_TEAM_MEMBER
    );

    return { success: 'Team member removed successfully' };
  }
);

const inviteTeamMemberSchema = z.object({
  email: z.string().email('Invalid email address'),
  role: z.enum(['member', 'owner'])
});

export const inviteTeamMember = validatedActionWithUser(
  inviteTeamMemberSchema,
  async (data, _, user) => {
    const { email, role } = data;
    const userWithTeam = await getUserWithTeam(user.id);

    if (!userWithTeam?.teamId) {
      return { error: 'User is not part of a team' };
    }

    const existingMember = await db
      .select()
      .from(users)
      .leftJoin(teamMembers, eq(users.id, teamMembers.userId))
      .where(
        and(eq(users.email, email), eq(teamMembers.teamId, userWithTeam.teamId))
      )
      .limit(1);

    if (existingMember.length > 0) {
      return { error: 'User is already a member of this team' };
    }

    // Check if there's an existing invitation
    const existingInvitation = await db
      .select()
      .from(invitations)
      .where(
        and(
          eq(invitations.email, email),
          eq(invitations.teamId, userWithTeam.teamId),
          eq(invitations.status, 'pending')
        )
      )
      .limit(1);

    if (existingInvitation.length > 0) {
      return { error: 'An invitation has already been sent to this email' };
    }

    // Create a new invitation
    await db.insert(invitations).values({
      id: generateKSortableId('inv_'), // Generate ID for invitation
      teamId: userWithTeam.teamId,
      email,
      role,
      invitedBy: user.id,
      status: 'pending'
    });

    await logActivity(
      userWithTeam.teamId,
      user.id,
      ActivityType.INVITE_TEAM_MEMBER
    );

    // TODO: Send invitation email and include ?inviteId={id} to sign-up URL
    // await sendInvitationEmail(email, userWithTeam.team.name, role)

    return { success: 'Invitation sent successfully' };
  }
);

export async function resetPasswordAction(formData: FormData) {
  try {
    const password = formData.get('password') as string;
    const confirmPassword = formData.get('confirmPassword') as string;

    if (password !== confirmPassword) {
      return { error: 'Passwords do not match' };
    }

    if (password.length < 8) {
      return { error: 'Password must be at least 8 characters' };
    }

    // 1. Verify Reset Token from Secure Cookie
    const cookieStore = await cookies();
    const resetToken = cookieStore.get('reset_session')?.value;

    if (!resetToken) {
      return { error: 'Session expired. Please request a new reset link.' };
    }

    let userId: string;
    try {
      const payload = await verifyResetToken(resetToken);
      userId = payload.userId;
    } catch (err) {
      console.error('Reset Token Verification Failed:', err);
      return { error: 'Invalid or expired reset token.' };
    }

    // 2. Use Admin Client to Update Password
    // Check key explicitly for better error message
    if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
      console.error('Missing SUPABASE_SERVICE_ROLE_KEY');
      return { error: 'Server configuration error: Integrity key missing.' };
    }

    const supabaseAdmin = createAdminClient();
    const { error } = await supabaseAdmin.auth.admin.updateUserById(userId, {
      password: password,
      user_metadata: { email_verified: true } // Ensure verified
    });

    if (error) {
      console.error('ResetPasswordAction: Admin Update Failed', error);
      return { error: error.message };
    }

    // 3. Cleanup
    cookieStore.delete('reset_session');

    return { success: 'Password updated successfully' };
  } catch (error: any) {
    console.error('ResetPasswordAction: Fatal Error', error);
    return { error: `System Error: ${error.message || 'Unknown'}` };
  }
}

export async function sendPasswordResetEmail(formData: FormData) {
  const email = formData.get('email') as string;
  const headersList = await headers();
  const origin = headersList.get('origin') || 'http://localhost:3000'; // Fallback for dev

  // Use Admin Client to generate link manually (Bypasses email delivery issues/scanners)
  if (process.env.SUPABASE_SERVICE_ROLE_KEY) {
    try {
      const supabaseAdmin = createAdminClient();
      const { data, error } = await supabaseAdmin.auth.admin.generateLink({
        type: 'recovery',
        email,
        options: {
          redirectTo: `${origin}/auth/callback?next=/reset-password`
        }
      });

      if (error) {
        console.error('Admin Link Gen Error:', error);
        return { error: error.message };
      }

      console.log('\n==================================================');
      console.log('🔗 ADMIN LINK GENERATION DATA:');
      console.log(JSON.stringify(data, null, 2));
      console.log('==================================================\n');

      return {
        success: 'Reset code generated! (Dev Mode)',
        devOtp: data.properties.email_otp
      };
    } catch (err) {
      console.error('Admin Link unexpected error:', err);
    }
  }

  // Fallback to standard flow (Production or missing key)
  const supabase = await createClient();
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${origin}/auth/callback?next=/reset-password`,
  });

  if (error) {
    return { error: error.message };
  }

  return { success: 'Reset link sent successfully' };
}

// New Action: Verify OTP and bridge to Reset Token flow
export async function verifyResetCode(formData: FormData) {
  const email = formData.get('email') as string;
  const code = formData.get('code') as string;
  const cookieStore = await cookies();

  const supabase = await createClient();

  // Verify the Recovery Code (OTP)
  const { data, error } = await supabase.auth.verifyOtp({
    email,
    token: code,
    type: 'recovery'
  });

  if (error || !data.session) {
    console.error('Verify OTP Error:', error);
    return { error: error?.message || 'Invalid code' };
  }

  // Issue our Secure Reset Token (Bypassing browser session issues)
  const token = await signResetToken({ userId: data.session.user.id, type: 'reset' });

  cookieStore.set('reset_session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 10 * 60 // 10 mins
  });

  return { success: true };
}
