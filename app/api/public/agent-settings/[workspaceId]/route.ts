import { NextResponse } from 'next/server';
import { getActiveAgentForWorkspace } from '@/lib/db/queries';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ workspaceId: string }> }
) {
  try {
    const { workspaceId } = await params;
    const { searchParams } = new URL(request.url);
    const translate = searchParams.get('translate') === 'true';

    // Get the active agent for this workspace
    const agent = await getActiveAgentForWorkspace(workspaceId);
    
    // Fallback settings if no agent is found
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

    // TODO: Implement translation logic here if required (using a translation service)
    // For now, we return settings as-is.

    return NextResponse.json({
        welcome_message: settings.welcome_message || settings.welcomeGreeting,
        language: settings.language,
        voice_id: settings.voice_id,
        use_tavus_avatar: settings.use_tavus_avatar || settings.useTavusAvatar || false,
        tavus_replica_id: settings.tavus_replica_id || settings.tavusReplicaId,
        anam_persona_id: settings.anam_persona_id || settings.anamPersonaId,
        avatar_provider: settings.avatar_provider || settings.avatarProvider || "tavus",
    });

  } catch (error: any) {
    console.error('Error fetching public agent settings:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
