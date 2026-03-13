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

        if gemini_key:
            try:
                from livekit.plugins import google as google_plugin
                return google_plugin.LLM(model="gemini-3-flash-preview", api_key=gemini_key, temperature=temperature)
            except: pass

        if openai_key:
            return openai.LLM(model="gpt-4o-mini", api_key=openai_key, temperature=temperature, _strict_tool_schema=False)
        
        if mistral_key:
            return openai.LLM(model="mistral-large-latest", base_url="https://api.mistral.ai/v1", api_key=mistral_key)
        
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
        is_openai_voice = voice_id.lower() in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if is_openai_voice:
            return openai.TTS(voice=voice_id)
        
        eleven_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="elevenlabs", env_fallback="ELEVENLABS_API_KEY")
        if eleven_key:
            mapped_id = VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id, VoicePipelineService.ELEVENLABS_VOICE_MAP.get(voice_id.title(), voice_id))
            return elevenlabs.TTS(voice_id=mapped_id, api_key=eleven_key)
            
        return openai.TTS(voice="alloy")

    @staticmethod
    def get_stt(workspace_id):
        deepgram_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="deepgram", env_fallback="DEEPGRAM_API_KEY")
        if deepgram_key:
            return deepgram.STT(model="nova-2", api_key=deepgram_key)
        return openai.STT()

    @staticmethod
    async def get_multimodal_agent(workspace_id, voice_id, prompt, tools):
        xai_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="xai", env_fallback="XAI_API_KEY")
        if not xai_key: return None

        from livekit.plugins.xai.realtime import RealtimeModel
        from livekit.agents.multimodal import MultimodalAgent
        import livekit.agents.vad as vad

        voice_map = {"Ara": "Ara", "Eve": "Eve", "Leo": "Leo", "Sal": "Sal", "Rex": "Rex"}
        final_voice = voice_map.get(voice_id.title(), "Ara")

        model = RealtimeModel(
            instructions=prompt,
            voice=final_voice,
            turn_detection=vad.EOU(threshold=0.6, silence_threshold_ms=200)
        )
        return MultimodalAgent(model=model, fnc_ctx=tools)
