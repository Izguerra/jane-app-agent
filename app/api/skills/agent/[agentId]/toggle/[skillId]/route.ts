import { NextResponse } from 'next/server';
import { toggleAgentSkill, getUser } from '@/lib/db/queries';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ agentId: string, skillId: string }> }
) {
  try {
    const { agentId, skillId } = await params;
    const { searchParams } = new URL(request.url);
    const enabled = searchParams.get('enabled') === 'true';
    const workspaceId = searchParams.get('workspaceId');

    if (!workspaceId) {
      return NextResponse.json({ error: 'Missing workspaceId' }, { status: 400 });
    }

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const result = await toggleAgentSkill(agentId, skillId, workspaceId, enabled);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Error toggling agent skill:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
