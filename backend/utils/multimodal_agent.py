import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable, Union
from livekit.agents import llm, stt, tts
from livekit import rtc
from livekit.agents.voice import Agent as VoiceAgent, AgentSession
from livekit.plugins import silero

logger = logging.getLogger("multimodal-agent-bridge")

def fix_timestamp(raw_seconds: float) -> float:
    """
    FIX: Corrects the 22% progressive drift in Gemini 3.1 Live.
    If the model says 100s, it actually means ~78s.
    Coefficient 0.7804 determined for 3.1 Flash-Lite / Live Preview.
    """
    DRIFT_COEFFICIENT = 0.7804
    return raw_seconds * DRIFT_COEFFICIENT

class MultimodalAgent(rtc.EventEmitter):
    """
    A high-performance bridge that provides a unified MultimodalAgent interface 
    for LiveKit 1.5.x, wrapping either a RealtimeModel or a standard LLM/STT/TTS pipeline.
    
    Includes the Gemini 3.1 Flash Live compatibility patch to work around the upstream
    livekit-plugins-google==1.5.1 bug where generate_reply() uses send_client_content
    (rejected by Gemini 3.1 with WebSocket error 1007).
    """
    def __init__(
        self,
        model: Union[llm.RealtimeModel, llm.LLM],
        *,
        workspace_id: str,
        voice_id: str,
        prompt: str = "",
        chat_ctx: Optional[llm.ChatContext] = None,
        fnc_ctx: Optional[Any] = None,
        vad: Optional[silero.VAD] = None,
        stt_instance: Optional[stt.STT] = None,
        tts_instance: Optional[tts.TTS] = None,
    ):
        super().__init__()
        self._model = model
        self._chat_ctx = chat_ctx or llm.ChatContext()
        self._fnc_ctx = fnc_ctx
        self._vad = vad or silero.VAD.load()
        self._session: Any = None
        self._room: Optional[rtc.Room] = None
        self._say_buffer = []
        self._started_event = asyncio.Event()
        self._first_say_executed = False
        self._closing = False
        
        # Flag: True when the LLM is a native multimodal model (Gemini Live)
        self._is_native_audio = isinstance(model, llm.RealtimeModel)

        # Tools extraction
        self._tools = []
        if self._fnc_ctx:
            self._tools.extend(llm.find_function_tools(self._fnc_ctx))
                
        # Apply the Gemini 3.1 compatibility patch BEFORE creating the VoiceAgent
        if self._is_native_audio:
            try:
                from backend.utils.gemini_31_patch import patch_realtime_session
                patch_applied = patch_realtime_session(self._model)
                if patch_applied:
                    logger.info("🔧 Gemini 3.1 compatibility patch active.")
            except Exception as e:
                logger.warning(f"Could not apply Gemini 3.1 patch: {e}")

        # In LiveKit 1.5.1, passing stt=None and tts=None to the VoiceAgent 
        # (with a RealtimeModel) triggers the native audio-to-audio path.
        # Adding Dummy objects here will BREAK the native modality.
        current_stt = stt_instance
        current_tts = tts_instance
        
        if self._is_native_audio:
            current_stt = None
            current_tts = None

        from livekit.agents.voice import Agent as VoiceAgent
        from livekit.agents import TurnHandlingOptions
        
        self._turn_handling = TurnHandlingOptions(
            allow_interruptions=True,
            intents_threshold=0.5
        )
        
        self._voice_agent = VoiceAgent(
            vad=self._vad,
            stt=current_stt,
            tts=current_tts,
            instructions=prompt,
            llm=self._model,
            chat_ctx=self._chat_ctx,
            tools=self._tools,
            turn_handling=self._turn_handling
        )

        # The session will be initialized on start()
        self._session = None

    async def start(self, room: rtc.Room, participant: Optional[rtc.RemoteParticipant] = None):
        """Starts the multimodal session in the given room."""
        self._room = room
        
        from livekit.agents.voice import AgentSession

        # In LiveKit 1.5.1, we initialize the AgentSession on-demand during start()
        # triggering the multimodal path if stt/tts are None.
        self._session = AgentSession(
            llm=self._model,
            vad=self._vad,
            stt=self._voice_agent.stt,
            tts=self._voice_agent.tts,
            tools=self._tools,
            turn_handling=self._turn_handling
        )

        # Forward events from the session to the bridge
        event_names = [
            "agent_transcript", "user_transcript", "agent_speech_committed",
            "user_speech_committed", "agent_started_speaking", "agent_stopped_speaking",
            "user_started_speaking", "user_stopped_speaking", "function_calls_collected",
            "function_calls_finished",
        ]

        def _make_forwarder(name):
            def _forwarder(*args, **kwargs):
                self.emit(name, *args, **kwargs)
                # Also forward to the internal voice agent for internal state matching
                if hasattr(self, '_voice_agent'):
                    self._voice_agent.emit(name, *args, **kwargs)
            return _forwarder

        for name in event_names:
            self._session.on(name, _make_forwarder(name))
            
        @self._session.on("user_stopped_speaking")
        def _on_user_stopped_speaking():
            # FIX: Gemini 3.1 requires audioStreamEnd to correctly flush Turn 2.
            if hasattr(self._session, 'send_audio_stream_end'):
                self._session.send_audio_stream_end()
            
        @self._session.on("error")
        def _on_error(error: Exception):
            logger.error(f"Multimodal agent session error: {error}")
            self.emit("error", error)

        # Start the session with our voice_agent config
        try:
            logger.info(f"Starting AgentSession in room {room.name}...")
            # HANDSHAKE GUARD: Gemini 3.1 requires a clean setup before interaction.
            # AgentSession.start() initializes the model and waits for the first track.
            await self._session.start(self._voice_agent, room=room, participant=participant)
            
            # Additional safety: Wait for the underlying Google session to be "active"
            # This helps avoid the "Turn 1" 1011 errors.
            await asyncio.sleep(0.5) 
            
            logger.info("✅ AgentSession started and confirmed active.")
        except Exception as e:
            logger.error(f"❌ Failed to start AgentSession: {e}", exc_info=True)
            self.emit("error", e)
        finally:
            # ALWAYS mark as started so say() doesn't buffer forever
            self._started_event.set()
            logger.info("📌 _started_event SET.")
            # Flush any greetings that were buffered before start() completed
            if self._say_buffer:
                asyncio.create_task(self._deliver_buffered_greetings())

    async def _deliver_buffered_greetings(self):
        """
        Delivers any buffered greetings after a short stabilization delay.
        Called from start()'s finally block once the session exists.
        """
        # FIX: The 3.1 model will fail if you send audio/text before setupComplete.
        # We give it a generous 2.0s buffer to ensure the handshake is strictly finished.
        await asyncio.sleep(2.0)
        
        if self._closing or not self._session:
            logger.warning("Greeting buffer delivery aborted - session context missing.")
            return

        while self._say_buffer:
            msg = self._say_buffer.pop(0)
            logger.info(f"📢 Delivering buffered greeting: {msg['text'][:60]}...")
            try:
                if hasattr(self._session, 'say'):
                    self._session.say(msg["text"], add_to_chat_ctx=True)
                elif hasattr(self._voice_agent, 'say'):
                    self._voice_agent.say(msg["text"], add_to_chat_ctx=True)
                else:
                    logger.error("No valid 'say' method found on session or agent.")
                    
                self._first_say_executed = True
            except Exception as e:
                logger.error(f"say() failed for greeting: {e}", exc_info=True)

    def say(self, text: str, allow_interruptions: bool = True, add_to_chat_ctx: bool = True):
        """Standard 'say' method with improved resilience for Gemini Live."""
        if not self._started_event.is_set():
            logger.info(f"Session not yet ready, buffering greeting: {text[:60]}...")
            self._say_buffer.append({"text": text})
            return

        logger.debug(f"Executing say(): is_native={self._is_native_audio}, has_session={self._session is not None}")

        try:
            # Native Multimodal / Gemini Live path (RealtimeSession)
            if self._is_native_audio and self._session:
                if hasattr(self._session, 'say'):
                    self._session.say(text, add_to_chat_ctx=add_to_chat_ctx)
                elif hasattr(self._session, 'generate_reply'):
                    # In Gemini 3.1 Live, we use generate_reply with instructions to speak
                    self._session.generate_reply(instructions=text)
                else:
                    logger.error("RealtimeSession has neither 'say' nor 'generate_reply'")
                self._first_say_executed = True
            # Pipeline fallback path (VoiceAgent + VoicePipeline)
            elif self._voice_agent and hasattr(self._voice_agent, 'say'):
                self._voice_agent.say(text, allow_interruptions=allow_interruptions, add_to_chat_ctx=add_to_chat_ctx)
                self._first_say_executed = True
            # Final desperate fallback to session if it has say but wasn't marked native
            elif self._session and hasattr(self._session, 'say'):
                 self._session.say(text, add_to_chat_ctx=add_to_chat_ctx)
                 self._first_say_executed = True
            else:
                logger.error(f"CRITICAL: Could not execute say('{text[:30]}...') - No valid method found.")
        except Exception as e:
            logger.error(f"Failed to execute say on agent: {e}", exc_info=True)

    async def stop(self):
        """Stops the agent session asynchronously."""
        if self._session and not self._closing:
            self._closing = True
            logger.info("Stopping multimodal agent session...")
            try:
                await self._session.aclose()
                logger.info("✅ Session closed successfully.")
            except Exception as e:
                logger.error(f"Error during aclose: {e}")

    @property
    def session(self) -> Any:
        return self._session or self._voice_agent

    def done(self) -> bool:
        """Returns True if the session is not yet setup or if it's already closed."""
        if self._session:
            return self._closing or not self._session._started
        return not self._started_event.is_set()
