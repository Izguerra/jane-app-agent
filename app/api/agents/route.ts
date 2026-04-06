import { NextResponse } from 'next/server';
import { getAgentsForWorkspace, createAgent, getUser } from '@/lib/db/queries';

export async function GET(request: Request) {
  try {
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

    const agents = await getAgentsForWorkspace(workspaceId);
    
    // Flatten agents for the frontend
    const flattenedList = agents.map((agent: any) => ({
      ...agent,
      ...(agent.settings as object || {}),
    }));

    return NextResponse.json(flattenedList);
  } catch (error: any) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
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

    const createData: any = {
      workspaceId,
      id: `agnt_${Math.random().toString(36).substring(2, 15)}`,
    };
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
        createData[standardizedKey] = value;
      } else {
        settings[standardizedKey] = value;
      }
    }

    createData.settings = settings;

    const newAgent = await createAgent(createData);

    // Return flattened version
    const responseData = {
      ...newAgent,
      ...(newAgent.settings as object || {}),
    };

    return NextResponse.json(responseData);
  } catch (error: any) {
    console.error('Error creating agent:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
