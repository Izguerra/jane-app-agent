import { NextResponse } from 'next/server';
import { getAgentById, updateAgent, getUser } from '@/lib/db/queries';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;
    const { searchParams } = new URL(request.url);
    const workspaceId = searchParams.get('workspaceId') || searchParams.get('workspace_id');

    if (!workspaceId) {
      return NextResponse.json({ error: 'Missing workspaceId' }, { status: 400 });
    }

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const agent = await getAgentById(agentId, workspaceId);
    if (!agent) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 });
    }

    // Flatten agent settings for the frontend (matches Python backend behavior)
    const flattened = {
      ...agent,
      ...(agent.settings as object || {}),
    };

    return NextResponse.json(flattened);
  } catch (error: any) {
    console.error('Error fetching agent:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;
    const { searchParams } = new URL(request.url);
    const workspaceId = searchParams.get('workspaceId') || searchParams.get('workspace_id');

    if (!workspaceId) {
      return NextResponse.json({ error: 'Missing workspaceId' }, { status: 400 });
    }

    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();

    // Define base fields that go into the top-level agents table
    const baseFields = [
      'name', 'voice_id', 'language', 'prompt_template', 
      'welcome_message', 'is_orchestrator', 'description', 'is_active'
    ];

    const updateData: any = {};
    const settings: any = {};

    // Standardize keys (camelCase to snake_case transition)
    const keyMap: { [key: string]: string } = {
      'openClawInstanceId': 'open_claw_instance_id',
      'tavusReplicaId': 'tavus_replica_id',
      'anamPersonaId': 'anam_persona_id',
      'avatarProvider': 'avatar_provider',
      'avatarVoiceId': 'avatar_voice_id',
      'useTavusAvatar': 'use_tavus_avatar',
      'ownerName': 'owner_name',
      'personalLocation': 'personal_location',
      'personalTimezone': 'personal_timezone',
      'favoriteFoods': 'favorite_foods',
      'favoriteRestaurants': 'favorite_restaurants',
      'favoriteMusic': 'favorite_music',
      'favoriteActivities': 'favorite_activities',
      'otherInterests': 'other_interests',
      'personalLikes': 'personal_likes',
      'personalDislikes': 'personal_dislikes',
    };

    for (const [key, value] of Object.entries(body)) {
      const standardizedKey = keyMap[key] || key;
      if (baseFields.includes(standardizedKey)) {
        updateData[standardizedKey] = value;
      } else {
        settings[standardizedKey] = value;
      }
    }

    // Fetch current agent to merge settings
    const currentAgent = await getAgentById(agentId, workspaceId);
    if (!currentAgent) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 });
    }

    const mergedSettings = {
      ...(currentAgent.settings as object || {}),
      ...settings,
    };

    updateData.settings = mergedSettings;

    const updated = await updateAgent(agentId, workspaceId, updateData);
    if (!updated) {
      return NextResponse.json({ error: 'Failed to update agent' }, { status: 500 });
    }

    // Return flattened version
    const responseData = {
      ...updated,
      ...(updated.settings as object || {}),
    };

    return NextResponse.json(responseData);
  } catch (error: any) {
    console.error('Error updating agent:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
