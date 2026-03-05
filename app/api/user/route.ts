import { getUser, getWorkspaceForUser, getUserWithTeam } from '@/lib/db/queries';

export async function GET() {
  const user = await getUser();

  if (!user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userData = await getWorkspaceForUser();
  // Wait, getWorkspaceForUser returns workspace. 
  // I need to use getUserWithTeam for the role, or update getWorkspaceForUser.
  // Converting to:
  const userWithTeam = await getUserWithTeam(user.id);
  const workspace = await getWorkspaceForUser();

  const effectiveRole = user.role === 'supaagent_admin' ? 'supaagent_admin' : (userWithTeam?.role || 'member');

  return Response.json({
    ...user,
    workspaceId: workspace?.id,
    role: effectiveRole
  });
}
