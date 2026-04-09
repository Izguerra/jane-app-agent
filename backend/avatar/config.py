import os
import logging
# LiveKit plugin imports moved inside functions for lazy loading and easier testing

logger = logging.getLogger("avatar-agent")

ELEVENLABS_VOICE_MAP = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Chris": "iP95p4xoKVk53GoZ742B",
    "Emily": "LcfcDJNUP1GQjkzn1xUU",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Leo": "IlPhMts77q4KnhTULU2v",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Nicole": "piTKgcLEGmPE4e6mEKli",
    "Sam": "yoZ06aMxZJJ28mfd3POQ"
}

def resolve_settings(metadata, participant_metadata):
    settings = {}
    if metadata:
        settings.update(metadata)
    if participant_metadata:
        settings.update(participant_metadata)
    
    # Unify keys
    settings["tavus_replica_id"] = settings.get("tavus_replica_id") or settings.get("tavusReplicaId")
    settings["tavus_persona_id"] = settings.get("tavus_persona_id") or settings.get("tavusPersonaId")
    settings["anam_persona_id"] = settings.get("anam_persona_id") or settings.get("anamPersonaId") or settings.get("persona_id")
    # Smart provider resolution: prioritize explicitly set, then infer from IDs
    provider = settings.get("avatar_provider") or settings.get("avatarProvider")
    if not provider:
        if settings.get("anam_persona_id"):
            provider = "anam"
        elif settings.get("tavus_replica_id"):
            provider = "tavus"
    settings["avatar_provider"] = provider
    
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
            return google_plugin.LLM(model="gemini-1.5-flash", api_key=gemini_key, temperature=0.7)
        except Exception as e:
            logger.warning(f"Gemini LLM init failed: {e}")
    
    if openai_key:
        return openai.LLM(model="gpt-4o-mini", api_key=openai_key, temperature=0.7)
    
    logger.error("No LLM API key found for avatar agent!")
    return openai.LLM(model="gpt-4o-mini", temperature=0.7)

def get_tts(voice_id, workspace_id: str = None, settings: dict = None):
    from backend.services.integration_service import IntegrationService
    from livekit.plugins import openai, deepgram, elevenlabs

    # 1. Explicit Deepgram Aura check
    if voice_id.startswith("aura-"):
        deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
        if deepgram_key:
            logger.info(f"Initializing Deepgram Aura TTS ({voice_id}) for avatar")
            return deepgram.TTS(model=voice_id, api_key=deepgram_key)

    # 2. OpenAI Voices (with speed optimization)
    clean_voice_id = voice_id.split('(')[0].strip().lower()
    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "ballad", "coral", "sage", "verse"]
    if clean_voice_id in openai_voices:
        logger.info(f"Initializing OpenAI TTS ({clean_voice_id}) with 1.15x speed for avatar")
        return openai.TTS(voice=clean_voice_id, speed=1.15)
    
    # 3. ElevenLabs
    eleven_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="elevenlabs", env_fallback="ELEVENLABS_API_KEY")
    if eleven_key:
        mapped_id = ELEVENLABS_VOICE_MAP.get(voice_id, ELEVENLABS_VOICE_MAP.get(voice_id.title(), voice_id))
        logger.info(f"Initializing ElevenLabs TTS ({voice_id}) for avatar")
        return elevenlabs.TTS(voice_id=mapped_id, api_key=eleven_key)
        
    # 4. Fallback to Deepgram if key exists but no explicit voice matched above
    deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
    if deepgram_key:
        logger.info("Initializing Deepgram Aura TTS (aura-asteria-en) as second-tier fallback for avatar")
        return deepgram.TTS(model="aura-asteria-en", api_key=deepgram_key)

    # Global Fallback
    logger.info("Initializing OpenAI Fallback TTS (alloy) with 1.15x speed for avatar")
    return openai.TTS(voice="alloy", speed=1.15)
