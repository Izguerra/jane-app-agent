import os
import logging
from livekit.plugins import openai

logger = logging.getLogger("avatar-agent")

def resolve_settings(metadata, participant_metadata):
    settings = {}
    if metadata:
        settings.update(metadata)
    if participant_metadata:
        settings.update(participant_metadata)
    
    # Unify keys
    settings["tavus_replica_id"] = settings.get("tavus_replica_id") or settings.get("tavusReplicaId")
    settings["tavus_persona_id"] = settings.get("tavus_persona_id") or settings.get("tavusPersonaId")
    settings["anam_persona_id"] = settings.get("anam_persona_id") or settings.get("anamPersonaId")
    settings["avatar_provider"] = settings.get("avatar_provider") or settings.get("avatarProvider") or "tavus"
    
    settings["voice_id"] = (
        settings.get("avatarVoiceId") or 
        settings.get("avatar_voice_id") or 
        settings.get("voiceId") or 
        settings.get("voice_id") or 
        "Josh"
    )
    return settings

def get_llm(workspace_id: str = None):
    from backend.services.integration_service import IntegrationService
    
    gemini_key = None
    openai_key = None
    
    if workspace_id:
        gemini_key = IntegrationService.get_provider_key(workspace_id, "gemini", "GOOGLE_API_KEY")
        openai_key = IntegrationService.get_provider_key(workspace_id, "openai", "OPENAI_API_KEY")
    
    # Fallback to env vars
    if not gemini_key:
        gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not openai_key:
        openai_key = os.getenv("OPENAI_API_KEY")
    
    if gemini_key:
        try:
            from livekit.plugins import google as google_plugin
            return google_plugin.LLM(model="gemini-2.0-flash", api_key=gemini_key, temperature=0.7)
        except Exception as e:
            logger.warning(f"Gemini LLM init failed: {e}")
    
    if openai_key:
        return openai.LLM(model="gpt-4o-mini", api_key=openai_key, temperature=0.7)
    
    logger.error("No LLM API key found for avatar agent!")
    return openai.LLM(model="gpt-4o-mini", temperature=0.7)

def get_tts(voice_id, workspace_id: str = None):
    from backend.services.integration_service import IntegrationService
    
    clean_voice_id = voice_id.split('(')[0].strip()
    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    if clean_voice_id.lower() in openai_voices:
        return openai.TTS(voice=clean_voice_id.lower())
    
    eleven_key = None
    if workspace_id:
        eleven_key = IntegrationService.get_provider_key(workspace_id, "elevenlabs", "ELEVENLABS_API_KEY")
    if not eleven_key:
        eleven_key = os.getenv("ELEVENLABS_API_KEY")
    
    if eleven_key:
        from livekit.plugins import elevenlabs
        from livekit.agents.tts import FallbackAdapter
        tts = elevenlabs.TTS(voice_id=clean_voice_id, api_key=eleven_key)
        return FallbackAdapter(tts=[tts, openai.TTS(voice="alloy")])
        
    return openai.TTS(voice="alloy")

