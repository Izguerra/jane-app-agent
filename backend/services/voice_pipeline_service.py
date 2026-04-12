import logging
import os
from livekit.agents import llm, stt, vad, tts
from livekit.plugins import deepgram, openai, elevenlabs, silero
from backend.services.integration_service import IntegrationService

logger = logging.getLogger("voice-pipeline-service")

class VoicePipelineService:
    @staticmethod
    def get_llm(workspace_id, settings):
        creativity = settings.get("creativity_level")
        temperature = float(creativity) / 100.0 if creativity is not None else 0.7
        
        openai_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="openai", env_fallback="OPENAI_API_KEY")
        gemini_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="gemini", env_fallback="GOOGLE_API_KEY") # Minimal mapping for now
        mistral_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="mistral", env_fallback="MISTRAL_API_KEY")
        openrouter_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="openrouter", env_fallback="OPENROUTER_API_KEY")

        # ENABLED: Google Gemini 1.5 Flash (Gemini 3)
        if gemini_key:
            try:
                from livekit.plugins import google as google_plugin
                logger.info("Initializing Google Gemini 1.5 Flash LLM (Standard Pipeline)")
                return google_plugin.LLM(model="gemini-1.5-flash", api_key=gemini_key, temperature=temperature)
            except ImportError:
                logger.warning("livekit-plugins-google not installed — falling through to OpenAI")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini LLM: {e} — falling through to OpenAI")

        if openai_key:
            logger.info("Initializing OpenAI gpt-4o-mini LLM (Standard Pipeline)")
            return openai.LLM(model="gpt-4o-mini", api_key=openai_key, temperature=temperature, _strict_tool_schema=False)
        
        if mistral_key:
            logger.info("Initializing Mistral LLM (Standard Pipeline)")
            return openai.LLM(model="mistral-large-latest", base_url="https://api.mistral.ai/v1", api_key=mistral_key)
        
        logger.info("Initializing OpenRouter LLM (Standard Pipeline)")
        return openai.LLM(model="deepseek/deepseek-chat", base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)

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

    @staticmethod
    def get_tts(workspace_id, voice_id, settings):
        # 1. Explicit Deepgram Aura check
        if voice_id.startswith("aura-"):
            deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
            if deepgram_key:
                logger.info(f"Initializing Deepgram Aura TTS ({voice_id})")
                return deepgram.TTS(model=voice_id, api_key=deepgram_key)

        # 2. OpenAI Voices
        clean_voice_id = voice_id.split('(')[0].strip().lower()
        openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "ballad", "coral", "sage", "verse"]
        if clean_voice_id in openai_voices:
            logger.info(f"Initializing OpenAI TTS ({clean_voice_id}) with 1.15x speed")
            return openai.TTS(voice=clean_voice_id, speed=1.15)
        
        # 3. ElevenLabs
        eleven_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="elevenlabs", env_fallback="ELEVENLABS_API_KEY")
        if eleven_key:
            mapped_id = VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id, VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id.title(), voice_id))
            logger.info(f"Initializing ElevenLabs TTS ({voice_id})")
            return elevenlabs.TTS(voice_id=mapped_id, api_key=eleven_key)
            
        # 4. Fallback to Deepgram if key exists but no explicit voice matched above (Legacy/Default)
        deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
        if deepgram_key:
            logger.info("Initializing Deepgram Aura TTS (aura-asteria-en) as second-tier fallback")
            return deepgram.TTS(model="aura-asteria-en", api_key=deepgram_key)

        logger.info("Initializing OpenAI Fallback TTS (alloy) with 1.15x speed")
        return openai.TTS(voice="alloy", speed=1.15)

    @staticmethod
    def get_stt(workspace_id):
        deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
        if deepgram_key:
            return deepgram.STT(model="nova-2", api_key=deepgram_key)
        return openai.STT()

    @staticmethod
    async def get_multimodal_agent(workspace_id, voice_id, prompt, tools):
        """
        Multimodal agents are currently handled via AgentSession in this SDK version.
        We return None here to trigger the stable fallback in the entrypoint.
        """
        return None
