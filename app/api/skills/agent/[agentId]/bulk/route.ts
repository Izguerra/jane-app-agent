import { NextResponse } from 'next/server';
import { bulkSyncSkills, getUser } from '@/lib/db/queries';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;
    const { searchParams } = new URL(request.url);
    const workspaceId = searchParams.get('workspaceId');

    if (!workspaceId) {
      return NextResponse.json({ error: 'Missing workspaceId' }, { status: 400 });
    }

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { enabled_skill_ids } = await request.json();
    if (!Array.isArray(enabled_skill_ids)) {
      return NextResponse.json({ error: 'Invalid enabled_skill_ids' }, { status: 400 });
    }

    await bulkSyncSkills(agentId, workspaceId, enabled_skill_ids);
    
    return NextResponse.json({ status: 'success' });
  } catch (error: any) {
    console.error('Error bulk syncing skills:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
