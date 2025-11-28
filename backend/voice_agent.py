import logging
import os
import asyncio
import json
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from backend.settings_store import get_settings
from backend.agent_tools import AgentTools
from datetime import datetime, timezone
from backend.database import SessionLocal
from backend.models_db import CommunicationLog

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")
logger.info(f"Loaded LIVEKIT_URL: {os.getenv('LIVEKIT_URL')}")

# Preload VAD model globally to avoid reloading it for every session
# This prevents race conditions and improves connection speed
_vad_model = None

def get_vad_model():
    global _vad_model
    if _vad_model is None:
        try:
            logger.info("Loading Silero VAD model...")
            _vad_model = silero.VAD.load()
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise e
    return _vad_model

def log_call(duration: int, status: str, sentiment: str = "neutral"):
    db = SessionLocal()
    try:
        # TODO: Get actual clinic_id from context/metadata if available
        clinic_id = 1 
        
        log = CommunicationLog(
            clinic_id=clinic_id,
            type="call",
            direction="inbound",
            status=status,
            duration=duration,
            sentiment=sentiment,
            started_at=datetime.now(timezone.utc)
        )
        db.add(log)
        db.commit()
        logger.info(f"Logged call: duration={duration}s, status={status}")
    except Exception as e:
        logger.error(f"Failed to log call: {e}")
    finally:
        db.close()

async def entrypoint(ctx: JobContext):
    start_time = datetime.now(timezone.utc)
    try:
        logger.info(f"Entrypoint called for room {ctx.room.name}")
        
        # Connect to room first to ensure we're ready
        logger.info(f"connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        # Wait for the first participant to connect
        logger.info("Waiting for participant...")
        participant = await ctx.wait_for_participant()
        logger.info(f"starting voice assistant for participant {participant.identity}")

        # Fetch settings fresh for this session
        # Try to get settings from participant metadata first (lower latency propagation)
        try:
            if participant.metadata:
                settings = json.loads(participant.metadata)
                logger.info(f"Loaded settings from metadata: {settings}")
            else:
                settings = get_settings()
        except Exception:
            settings = get_settings()

        voice_id = settings.get("voice_id", "alloy")
        language = settings.get("language", "en")
        prompt_template = settings.get("prompt_template", "You are a helpful assistant.")
        
        logger.info(f"Agent configuration: voice={voice_id}, language={language}")
        
        # Determine TTS provider based on voice_id
        tts_provider = None
        valid_openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        if voice_id in valid_openai_voices:
            tts_provider = openai.TTS(voice=voice_id, model="tts-1")
            logger.info(f"Using OpenAI TTS with voice: {voice_id}")
        else:
            # Assume it's an ElevenLabs voice if not an OpenAI voice
            # Ensure ELEVENLABS_API_KEY is set in .env
            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
            if elevenlabs_api_key:
                try:
                    tts_provider = elevenlabs.TTS(
                        voice_id=voice_id,
                        api_key=elevenlabs_api_key,
                        model_id="eleven_turbo_v2"
                    )
                    logger.info(f"Using ElevenLabs TTS with voice: {voice_id}")
                except Exception as e:
                    logger.error(f"Failed to initialize ElevenLabs TTS with voice {voice_id}: {e}. Falling back to OpenAI 'alloy'.", exc_info=True)
                    tts_provider = openai.TTS(voice="alloy", model="tts-1")
                    voice_id = "alloy" # Update voice_id to reflect fallback
            else:
                logger.warning("ELEVENLABS_API_KEY not set. Falling back to OpenAI 'alloy' for ElevenLabs voice request.")
                tts_provider = openai.TTS(voice="alloy", model="tts-1")
                voice_id = "alloy" # Update voice_id to reflect fallback

        if tts_provider is None: # Fallback if something went wrong
            logger.error("No valid TTS provider initialized. Defaulting to OpenAI 'alloy'.")
            tts_provider = openai.TTS(voice="alloy", model="tts-1")
            voice_id = "alloy"

        # Configure STT and Prompt based on language setting
        stt_config = None
        
        if language == "auto":
            logger.info("Auto-detection enabled: Using multilingual prompt and STT")
            prompt_template = f"{prompt_template}\n\nCRITICAL INSTRUCTION: You are a multilingual assistant. You MUST wait for the user to speak first. Detect the language the user is speaking and reply in the SAME language. If the user speaks English, reply in English. If the user speaks Spanish, reply in Spanish. If the user switches language mid-conversation, you MUST switch immediately. Do NOT translate what the user said, just respond naturally in their language."
            stt_config = deepgram.STT(model="nova-2", detect_language=True)
        else:
            logger.info(f"Specific language enabled: {language}")
            # Map language codes to names for the prompt
            language_names = {
                "en": "English", "es": "Spanish", "fr": "French", "de": "German", 
                "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ja": "Japanese"
            }
            lang_name = language_names.get(language, "English")
            prompt_template = f"{prompt_template}\n\nCRITICAL INSTRUCTION: You MUST speak ONLY in {lang_name}. Do NOT speak any other language."
            stt_config = deepgram.STT(model="nova-2", language=language)
        
        # Create the agent configuration
        agent = Agent(
            instructions=prompt_template,
        )
        
        # Initialize tools
        tools = AgentTools()
        
        # Create the session with runtime components and tools
        # Use the preloaded VAD model
        session = AgentSession(
            vad=get_vad_model(),
            # turn_detection=MultilingualModel(), # Disabled for lower latency
            # Use Nova-2 model for better multilingual support
            stt=stt_config, 
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=tts_provider,
            tools=llm.find_function_tools(tools),
        )
        
        logger.info(f"Starting agent session for room {ctx.room.name}")
        await session.start(agent, room=ctx.room)
        logger.info("session.start() returned")
        
        # REMOVED: Initial greeting. Agent will wait for user input.
        # This ensures the first response is based on the user's actual language.
        logger.info("Agent ready. Waiting for user input...")
        
        # Keep the entrypoint alive while the room is connected
        # The session will automatically close when the participant disconnects
        # or the room is closed, but we need to prevent this function from returning.
        participant_disconnect_future = asyncio.Future()
        
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnect(p):
            if p.identity == participant.identity:
                logger.info(f"Participant {p.identity} disconnected, closing session")
                if not participant_disconnect_future.done():
                    participant_disconnect_future.set_result(None)

        @ctx.room.on("disconnected")
        def on_room_disconnect(reason):
            logger.info(f"Room disconnected: {reason}")
            if not participant_disconnect_future.done():
                participant_disconnect_future.set_result(None)

        try:
            await participant_disconnect_future
        except asyncio.CancelledError:
            logger.info("Main task cancelled")
        finally:
            logger.info("Session ending")
            # Calculate duration
            end_time = datetime.now(timezone.utc)
            duration = int((end_time - start_time).total_seconds())
            log_call(duration, "completed")
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)
        # Log failed call
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds())
        log_call(duration, "failed")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="jane-voice-agent",
        ),
    )
