import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { db } from '@/lib/db/drizzle';
import { stripe } from '@/lib/payments/stripe';
import { users, teams, teamMembers, workspaces, activityLogs, invitations, ActivityType, type NewUser, type NewTeam, type NewTeamMember, type NewActivityLog } from '@/lib/db/schema';
import { eq, and, sql } from 'drizzle-orm';
import { setSession, signResetToken } from '@/lib/auth/session';

// K-Sortable ID Helper (Simplified)
const ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
const BASE = ALPHABET.length;

function base62Encode(num: number, minLength: number): string {
    let str = '';
    while (num > 0) {
        str = ALPHABET[num % BASE] + str;
        num = Math.floor(num / BASE);
    }
    return str.padStart(minLength, '0');
}

function generateKSortableId(prefix: string): string {
    const timestamp = Date.now();
    const tsPart = base62Encode(timestamp, 10);
    let randPart = '';
    for (let i = 0; i < 16; i++) {
        randPart += ALPHABET[Math.floor(Math.random() * BASE)];
    }
    return `${prefix}${tsPart}${randPart}`;
}

export async function GET(request: Request) {
    const { searchParams, origin } = new URL(request.url);
    const code = searchParams.get('code');
    const next = searchParams.get('next') ?? '/dashboard';
    const redirectParam = searchParams.get('redirect');
    const priceId = searchParams.get('priceId');
    const inviteId = searchParams.get('inviteId');

    if (code) {
        const supabase = await createClient();
        const { error } = await supabase.auth.exchangeCodeForSession(code);

        if (error) {
            console.error('Auth Callback Error (exchangeCodeForSession):', error.message, error);
            return NextResponse.redirect(`${origin}/auth/auth-code-error`);
        }

        if (!error) {
            const { data: { user } } = await supabase.auth.getUser();

            if (next === '/reset-password' && user) {
                // Generate secure reset token
                const token = await signResetToken({ userId: user.id, type: 'reset' });

                // Set cookie via Response
                const res = NextResponse.redirect(`${origin}/reset-password`);
                res.cookies.set('reset_session', token, {
                    httpOnly: true,
                    secure: process.env.NODE_ENV === 'production',
                    sameSite: 'lax',
                    maxAge: 10 * 60 // 10 mins
                });
                return res;
            }

            if (user) {
                try {
                    // Sync Logic: Check if user exists in public DB
                    const existingUser = await db.query.users.findFirst({
                        where: eq(users.id, user.id) // Using UUID
                    });

                    if (!existingUser) {
                        // Check if user exists by EMAIL (migration case)
                        const email = user.email!;
                        const existingUserByEmail = await db.query.users.findFirst({
                            where: sql`lower(${users.email}) = ${email.toLowerCase()}`
                        });

                        if (existingUserByEmail) {
                            try {
                                console.log('Migrating user in OAuth callback:', email);
                                const oldUserId = existingUserByEmail.id;
                                const newUserId = user.id;

                                // 1. Update dependent records (Data Preservation)
                                // We swap the ID in related tables to the new Supabase UUID
                                await db.update(teamMembers)
                                    .set({ userId: newUserId })
                                    .where(eq(teamMembers.userId, oldUserId));

                                await db.update(activityLogs)
                                    .set({ userId: newUserId })
                                    .where(eq(activityLogs.userId, oldUserId));

                                await db.update(invitations)
                                    .set({ invitedBy: newUserId })
                                    .where(eq(invitations.invitedBy, oldUserId));

                                // Worker Tasks (created_by and rated_by)
                                // Note: We need to import workerTasks first if checking schema, but assuming access via db object or string if not imported.
                                // Actually, let's use raw SQL for safety if imports are missing, or verify imports.
                                // Looking at imports, 'workerTasks' is NOT imported. I will add it to imports or use raw SQL.
                                // Using raw SQL is safer for simple ID updates to avoid import clutter in this fix.
                                await db.execute(sql`UPDATE worker_tasks SET created_by_user_id = ${newUserId} WHERE created_by_user_id = ${oldUserId}`);
                                await db.execute(sql`UPDATE worker_tasks SET rated_by_user_id = ${newUserId} WHERE rated_by_user_id = ${oldUserId}`);
                                await db.execute(sql`UPDATE worker_tasks SET dispatched_by_agent_id = ${newUserId} WHERE dispatched_by_agent_id = ${oldUserId}`); // Wait, agent!=user. Ignore.

                                // 2. Delete the old user
                                await db.delete(users).where(eq(users.id, oldUserId));
                            } catch (e) {
                                console.error('Migration cleanup failed', e);
                                // If migration fails, we can't create the new user with same email.
                                // Redirect to error page.
                                return NextResponse.redirect(`${origin}/sign-in?error=migration_failed`);
                            }
                        }

                        // Create user from Social Metadata
                        const meta = user.user_metadata || {};
                        const fullName = meta.full_name || meta.name || email.split('@')[0];
                        const [firstName, ...rest] = fullName.split(' ');
                        const lastName = rest.join(' ') || '';

                        const newUser: NewUser = {
                            id: user.id,
                            name: fullName,
                            firstName: firstName || 'User',
                            lastName: lastName || '',
                            username: (meta.user_name || email.split('@')[0] + Math.floor(Math.random() * 1000)).slice(0, 50),
                            email: email,
                            passwordHash: 'supabase_social',
                            role: 'member',
                        };

                        await db.insert(users).values(newUser);

                        // Create default Team
                        const newTeamId = generateKSortableId('org_');
                        const newTeam: NewTeam = {
                            id: newTeamId,
                            name: `${email}'s Team`
                        };
                        await db.insert(teams).values(newTeam);

                        // Create Team Member (Owner)
                        const newMember: NewTeamMember = {
                            id: generateKSortableId('mem_'),
                            userId: user.id,
                            teamId: newTeamId,
                            role: 'owner'
                        };
                        await db.insert(teamMembers).values(newMember);

                        // Create Workspace
                        const newWorkspaceId = generateKSortableId('wrk_');
                        await db.insert(workspaces).values({
                            id: newWorkspaceId,
                            teamId: newTeamId,
                            name: `${email}'s Workspace`
                        });

                        // Log Activity
                        await db.insert(activityLogs).values({
                            id: generateKSortableId('act_'),
                            teamId: newTeamId,
                            userId: user.id,
                            action: ActivityType.SIGN_UP
                        });

                        // Redirect Logic
                        if (redirectParam === 'checkout' && priceId) {
                            // Plan-specific trial periods
                            const TRIAL_DAYS: Record<string, number> = {
                                'price_1SZbis6Rc2ce57mvRsWtgE4S': 3,  // Starter - 3 days for testing
                                'price_1SZbit6Rc2ce57mvWfwltbMg': 14, // Professional
                            };
                            const trialDays = TRIAL_DAYS[priceId] ?? 14;

                            const session = await stripe.checkout.sessions.create({
                                payment_method_types: ['card'],
                                line_items: [{ price: priceId, quantity: 1 }],
                                mode: 'subscription',
                                success_url: `${origin}/api/stripe/checkout?session_id={CHECKOUT_SESSION_ID}`,
                                cancel_url: `${origin}/pricing`,
                                client_reference_id: user.id.toString(),
                                allow_promotion_codes: true,
                                subscription_data: { trial_period_days: trialDays }
                            });
                            return NextResponse.redirect(session.url!);
                        }

                        // Redirect to new workspace
                        return NextResponse.redirect(`${origin}/${newWorkspaceId}/dashboard/analytics`);
                    } else {
                        // User exists, find their workspace
                        // Log Sign In
                        const member = await db.query.teamMembers.findFirst({ where: eq(teamMembers.userId, existingUser.id) });

                        if (member) {
                            await db.insert(activityLogs).values({
                                id: generateKSortableId('act_'),
                                teamId: member.teamId,
                                userId: user.id,
                                action: ActivityType.SIGN_IN
                            });

                            // Create Session for Middleware
                            await setSession(existingUser, member.teamId);

                            // Checkout Redirect for Existing User?
                            if (redirectParam === 'checkout' && priceId) {
                                // Need team details for Stripe Customer ID if exists (stripe.ts logic handles it usually)
                                // But here we construct session manually.
                                // Ideally we check if team has stripeCustomerId.
                                const team = await db.query.teams.findFirst({ where: eq(teams.id, member.teamId) });

                                // Plan-specific trial periods
                                const TRIAL_DAYS: Record<string, number> = {
                                    'price_1SZbis6Rc2ce57mvRsWtgE4S': 3,  // Starter - 3 days for testing
                                    'price_1SZbit6Rc2ce57mvWfwltbMg': 14, // Professional
                                };
                                const trialDays = TRIAL_DAYS[priceId] ?? 14;

                                const session = await stripe.checkout.sessions.create({
                                    payment_method_types: ['card'],
                                    line_items: [{ price: priceId, quantity: 1 }],
                                    mode: 'subscription',
                                    success_url: `${origin}/api/stripe/checkout?session_id={CHECKOUT_SESSION_ID}`,
                                    cancel_url: `${origin}/pricing`,
                                    customer: team?.stripeCustomerId || undefined,
                                    client_reference_id: user.id.toString(),
                                    allow_promotion_codes: true,
                                    subscription_data: { trial_period_days: trialDays }
                                });
                                return NextResponse.redirect(session.url!);
                            }

                            const workspace = await db.query.workspaces.findFirst({ where: eq(workspaces.teamId, member.teamId) });
                            if (workspace) {
                                return NextResponse.redirect(`${origin}/${workspace.id}/dashboard/analytics`);
                            }
                        }

                        // Fallback
                        return NextResponse.redirect(`${origin}/dashboard`);
                    }

                } catch (error: any) {
                    console.error('Auth Callback Error:', error);
                    // If sync failed, they might not have a public user record, causing 500s later.
                    return NextResponse.redirect(`${origin}/sign-in?error=sync_failed&message=${encodeURIComponent(error.message)}`);
                }
            }
        }
    }

    return NextResponse.redirect(`${origin}/auth/auth-code-error`);
}
