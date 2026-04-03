import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable, Union
from livekit.agents import llm, stt, tts
from livekit import rtc
from livekit.agents.voice import Agent as VoiceAgent, AgentSession
from livekit.plugins import silero

logger = logging.getLogger("multimodal-agent-bridge")

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
        tools = []
        if self._fnc_ctx:
            tools.extend(llm.find_function_tools(self._fnc_ctx))
                
        # Apply the Gemini 3.1 compatibility patch BEFORE creating the VoiceAgent
        if self._is_native_audio:
            try:
                from backend.utils.gemini_31_patch import patch_realtime_session
                patch_applied = patch_realtime_session(self._model)
                if patch_applied:
                    logger.info("🔧 Gemini 3.1 compatibility patch active.")
            except Exception as e:
                logger.warning(f"Could not apply Gemini 3.1 patch: {e}")

        # TTS handling for RealtimeModels
        if self._is_native_audio:
            from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream
            class DummyTTS(TTS):
                """Placeholder TTS for RealtimeModel — audio comes from the model itself."""
                def __init__(self):
                    super().__init__(capabilities=TTSCapabilities(streaming=False), sample_rate=24000, num_channels=1)
                def synthesize(self, text: str, **kwargs) -> ChunkedStream:
                    raise NotImplementedError("Not used by Multimodal models")
            
            self._tts = DummyTTS()
            self._stt = None
        else:
            self._tts = tts_instance
            self._stt = stt_instance

        from livekit.agents import TurnHandlingOptions
        self._voice_agent = VoiceAgent(
            vad=self._vad,
            stt=self._stt,
            tts=self._tts,
            instructions=prompt,
            llm=self._model,
            chat_ctx=self._chat_ctx,
            tools=tools,
            turn_handling=TurnHandlingOptions(interruption={"mode": "adaptive"})
        )

    async def start(self, room: rtc.Room, participant: Optional[rtc.RemoteParticipant] = None):
        """Starts the multimodal session in the given room."""
        self._room = room
        
        # FIX: AgentSession should NOT receive llm/tts/stt/tools —
        # those are carried by the VoiceAgent and AgentSession inherits from it.
        # Passing them to both causes double-initialization of the Gemini WebSocket.
        self._session = AgentSession()
        
        # Start the session with our voice_agent config
        try:
            logger.info(f"Starting AgentSession with voice_agent in room {room.name}...")
            await self._session.start(self._voice_agent, room=room)
            logger.info("✅ AgentSession started successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to start AgentSession: {e}", exc_info=True)
            self.emit("error", e)
            return

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
            return _forwarder

        for name in event_names:
            self._session.on(name, _make_forwarder(name))
            
        @self._session.on("error")
        def _on_error(error: Exception):
            logger.error(f"Multimodal agent session error: {error}")
            self.emit("error", error)

        # Signal that we are 'started'
        self._started_event.set()
        
        # FIX: Launch async greeting delivery that waits for the Gemini WebSocket
        if self._say_buffer:
            asyncio.create_task(self._deliver_buffered_greetings())

    async def _deliver_buffered_greetings(self):
        """
        Waits for the Gemini WebSocket session to be fully connected,
        then delivers any buffered greetings.
        
        This fixes the race condition where say() is called before the
        Gemini session's WebSocket is ready, causing the greeting to be
        permanently lost.
        """
        max_attempts = 80  # 80 * 0.25s = 20s max wait
        for attempt in range(max_attempts):
            if self._closing:
                return
                
            # Check if the session has generate_reply available (means WebSocket is up)
            try:
                if self._session and hasattr(self._session, 'generate_reply'):
                    # The session is ready — deliver all buffered messages
                    while self._say_buffer:
                        msg = self._say_buffer.pop(0)
                        logger.info(f"📢 Delivering buffered greeting: {msg['text'][:60]}...")
                        try:
                            self._session.generate_reply(instructions=msg["text"])
                            self._first_say_executed = True
                        except Exception as e:
                            logger.warning(f"generate_reply failed for greeting: {e}")
                            # Fallback: try the VoiceAgent's say method
                            try:
                                self._voice_agent.say(msg["text"])
                            except Exception as e2:
                                logger.error(f"Fallback say also failed: {e2}")
                    return
            except Exception as e:
                logger.debug(f"Greeting delivery check #{attempt}: {e}")
            
            await asyncio.sleep(0.25)
        
        logger.warning("⚠️ Timed out waiting for session readiness. Greetings may not be delivered.")

    def say(self, text: str, allow_interruptions: bool = True, add_to_chat_ctx: bool = True):
        """Standard 'say' method with improved resilience for Gemini Live."""
        if not self._started_event.is_set():
            logger.info(f"Session not yet ready, buffering greeting: {text[:60]}...")
            self._say_buffer.append({"text": text})
            return

        try:
            if self._is_native_audio:
                # Use generate_reply which is now patched for Gemini 3.1
                if self._session and hasattr(self._session, 'generate_reply'):
                    self._session.generate_reply(instructions=text)
                    self._first_say_executed = True
                else:
                    logger.warning("Session not ready for say(). Buffering.")
                    self._say_buffer.append({"text": text})
                    if not self._first_say_executed:
                        asyncio.create_task(self._deliver_buffered_greetings())
            else:
                self._voice_agent.say(text, allow_interruptions=allow_interruptions, add_to_chat_ctx=add_to_chat_ctx)
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
