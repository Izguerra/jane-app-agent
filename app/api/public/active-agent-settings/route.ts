import { NextResponse } from 'next/server';
import { getActiveAgentForWorkspace, getUser, getWorkspaceForUser } from '@/lib/db/queries';

export async function GET(request: Request) {
  try {
    // Authenticate user
    const user = await getUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get the user's workspace
    const workspace = await getWorkspaceForUser();
    if (!workspace) {
      return NextResponse.json({ error: 'Workspace not found' }, { status: 404 });
    }

    // Get the active agent for this workspace
    const agent = await getActiveAgentForWorkspace(workspace.id);
    
    const settings: any = {};
    if (agent) {
      // Base fields
      if (agent.welcomeMessage) settings["welcome_message"] = agent.welcomeMessage;
      if (agent.language) settings["language"] = agent.language;
      if (agent.voiceId) settings["voice_id"] = agent.voiceId;
      
      // Merge extended settings
      if (agent.settings) {
        Object.assign(settings, agent.settings);
      }
    }

    // Format for the frontend (matches Python backend's get_active_agent_settings)
    return NextResponse.json({
      welcome_message: settings.welcome_message || settings.welcomeGreeting,
      language: settings.language,
      voice_id: settings.voice_id,
      agent_id: agent?.id || null,
      use_tavus_avatar: settings.use_tavus_avatar || settings.useTavusAvatar || false,
      tavus_replica_id: settings.tavus_replica_id || settings.tavusReplicaId,
      anam_persona_id: settings.anam_persona_id || settings.anamPersonaId,
      avatar_provider: settings.avatar_provider || settings.avatarProvider || "tavus",
    });
  } catch (error: any) {
    console.error('Error fetching active agent settings:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
