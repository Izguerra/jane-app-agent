import { NextResponse } from 'next/server';
import { getSkillsForAgent, getUser } from '@/lib/db/queries';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const agentSkills = await getSkillsForAgent(agentId);
    return NextResponse.json(agentSkills);
  } catch (error: any) {
    console.error('Error fetching agent skills:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
