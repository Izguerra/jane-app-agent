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
        gemini_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="gemini", env_fallback="GOOGLE_API_KEY")
        mistral_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="mistral", env_fallback="MISTRAL_API_KEY")
        openrouter_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="openrouter", env_fallback="OPENROUTER_API_KEY")

        if gemini_key:
            try:
                from livekit.plugins import google as google_plugin
                return google_plugin.LLM(model="gemini-1.5-flash", api_key=gemini_key, temperature=temperature)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini 1.5 LLM: {e}")

        if openai_key:
            return openai.LLM(model="gpt-4o-mini", api_key=openai_key, temperature=temperature, _strict_tool_schema=False)
        
        if mistral_key:
            return openai.LLM(model="mistral-large-latest", base_url="https://api.mistral.ai/v1", api_key=mistral_key)
        
        return openai.LLM(model="deepseek/deepseek-chat", base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)

    @staticmethod
    def get_realtime_model(workspace_id, voice_id, prompt):
        """Initializes a Gemini 3.1 Flash Live RealtimeModel."""
        from livekit.plugins import google as google_plugin
        
        gemini_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="gemini", env_fallback="GOOGLE_GEMINI_API_KEY")
        if not gemini_key: gemini_key = os.getenv("GOOGLE_API_KEY")
            
        if not gemini_key:
            logger.warning("Gemini key missing, cannot start realtime model")
            return None
            
        try:
            from google.genai import types
            
            gemini_voice = "Aoede" # Default female
            if voice_id:
                v_lower = voice_id.lower()
                if any(v in v_lower for v in ["puck", "charon", "fenrir", "josh", "leo", "adam", "male", "guy", "echo", "onyx"]):
                    gemini_voice = "Puck"
                elif any(v in v_lower for v in ["kore", "aoede", "nova", "shimmer", "alloy", "female", "girl", "woman"]):
                    gemini_voice = "Aoede"
            
            # Use Gemini 2.5 Flash Native Audio (stable with LiveKit 1.5.1)
            # NOTE: gemini-3.1-flash-live-preview is INCOMPATIBLE with livekit-plugins-google==1.5.1
            # See docs/GEMINI_MODEL_COMPATIBILITY.md for details and upstream tracking.
            try:
                logger.info(f"🚀 Initializing Gemini 2.5 Flash Native Audio (A2A) with voice: {gemini_voice}")
                model = google_plugin.realtime.RealtimeModel(
                    model="gemini-2.5-flash-native-audio-preview",
                    api_key=gemini_key,
                    instructions=prompt,
                    modalities=["AUDIO"],
                    voice=gemini_voice,
                )
                logger.info("✅ Gemini 2.5 Flash Native Audio model instance created.")
                return model
            except Exception as e:
                logger.warning(f"⚠️ Gemini 2.5 initialization failed: {e}. Falling back to 2.0 Flash Exp.")
                
                model = google_plugin.realtime.RealtimeModel(
                    model="gemini-2.0-flash-exp",
                    api_key=gemini_key,
                    instructions=prompt,
                    modalities=["AUDIO"],
                    voice=gemini_voice,
                )
                logger.info("✅ Gemini 2.0 Flash Exp model instance created (Fallback).")
                return model
        except ImportError as ie:
            logger.error(f"❌ Missing dependency for Gemini Realtime: {ie}. Ensure google-genai is installed.")
            return None
        except Exception as e:
            logger.error(f"❌ Critical Gemini initialization failure: {e}", exc_info=True)
            return None

    @staticmethod
    def get_multimodal_agent(workspace_id, voice_id, prompt, vad=None, fnc_ctx=None, chat_ctx=None, settings=None):
        """
        Factory for the unified MultimodalAgent bridge.
        Returns a bridge that transparently handles Gemini Live or standard pipelines.
        """
        from backend.utils.multimodal_agent import MultimodalAgent
        
        # 1. Try for Native Gemini Multimodal Live (A2A)
        model = VoicePipelineService.get_realtime_model(workspace_id, voice_id, prompt)
        
        if model:
            logger.info("✅ MultiPipeline: Creating native Gemini Live bridge.")
            return MultimodalAgent(
                model=model,
                workspace_id=workspace_id,
                voice_id=voice_id,
                prompt=prompt,
                vad=vad,
                fnc_ctx=fnc_ctx,
                chat_ctx=chat_ctx
            )
            
        # 2. Fallback to standard STT/LLM/TTS Pipeline
        logger.info("⚠️ MultiPipeline: Falling back to standard text-based LLM.")
        if not settings:
            from backend.settings_store import get_settings
            settings = get_settings(workspace_id)
            
        llm_instance = VoicePipelineService.get_llm(workspace_id, settings)
        stt_instance = VoicePipelineService.get_stt(workspace_id)
        tts_instance = VoicePipelineService.get_tts(workspace_id, voice_id, settings)
        
        return MultimodalAgent(
            model=llm_instance,
            workspace_id=workspace_id,
            voice_id=voice_id,
            prompt=prompt,
            vad=vad,
            fnc_ctx=fnc_ctx,
            chat_ctx=chat_ctx,
            stt_instance=stt_instance,
            tts_instance=tts_instance
        )

    ELEVENLABS_VOICE_MAP = {
        "Rachel": "21m00Tcm4TlvDq8ikWAM", "Adam": "pNInz6obpgDQGcFmaJgB",
        "Bella": "EXAVITQu4vr4xnSDxMaL", "Chris": "iP95p4xoKVk53GoZ742B",
        "Emily": "LcfcDJNUP1GQjkzn1xUU", "Josh": "TxGEqnHWrfWFTfGW9XjX",
        "Leo": "IlPhMts77q4KnhTULU2v", "Matilda": "XrExE9yKIg1WjnnlVkGX",
        "Nicole": "piTKgcLEGmPE4e6mEKli", "Sam": "yoZ06aMxZJJ28mfd3POQ"
    }

    @staticmethod
    def get_tts(workspace_id, voice_id, settings):
        is_openai_voice = voice_id.lower() in ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "sage", "ash", "coral", "verse"]
        if is_openai_voice: return openai.TTS(voice=voice_id, speed=1.15)
        
        eleven_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="elevenlabs", env_fallback="ELEVENLABS_API_KEY")
        if eleven_key:
            mapped_id = VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id, VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id.title(), voice_id))
            return elevenlabs.TTS(voice_id=mapped_id, api_key=eleven_key)
            
        return openai.TTS(voice="alloy")

    @staticmethod
    def get_stt(workspace_id):
        deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
        if deepgram_key: return deepgram.STT(model="nova-2", api_key=deepgram_key)
        return openai.STT()
