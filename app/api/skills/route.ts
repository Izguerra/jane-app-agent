import { NextResponse } from 'next/server';
import { getSkillsCatalog, getUser, getWorkspaceForUser } from '@/lib/db/queries';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const workspaceId = searchParams.get('workspaceId') || searchParams.get('workspace_id');

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    let finalWorkspaceId = workspaceId;
    if (!finalWorkspaceId) {
        const workspace = await getWorkspaceForUser();
        if (workspace) {
            finalWorkspaceId = workspace.id;
        }
    }

    if (!finalWorkspaceId) {
      return NextResponse.json({ error: 'Missing workspaceId and no default workspace found' }, { status: 400 });
    }

    const catalog = await getSkillsCatalog(finalWorkspaceId);
    return NextResponse.json(catalog);
  } catch (error: any) {
    console.error('Error fetching skills catalog:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
