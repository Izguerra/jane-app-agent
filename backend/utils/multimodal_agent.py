import asyncio
import logging
import time
from typing import Optional, Any, Union, Callable
from livekit import rtc
from livekit.agents import llm, stt, tts, vad
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import google

logger = logging.getLogger("multimodal-agent-bridge")

class MultimodalAgent(Agent):
    """
    A high-performance bridge for LiveKit 1.5.x, specifically optimized for 
    Gemini 3.1 Flash Live Native Audio (A2A). 
    
    Inherits from Agent to satisfy AgentSession requirements in LiveKit 1.5.1.
    """
    def __init__(
        self,
        model_id: str, # "gemini-3.1-flash-live-preview"
        *,
        workspace_id: str,
        voice_id: str = "Puck",
        api_key: Optional[str] = None,
        prompt: str = "",
        fnc_ctx: Optional[Any] = None,
        thinking_level: str = "medium",
    ):
        # 1. Initialize the RealtimeModel directly
        from livekit.plugins.google import realtime
        from livekit.plugins.google.realtime import types
        
        self._model = realtime.RealtimeModel(
            model=model_id,
            api_key=api_key,
            instructions=prompt,
            voice=voice_id,
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
            enable_affective_dialog=True,
            proactivity=True,
        )
        
        # 2. Call parent Agent constructor
        # In 1.5.1, we pass the RealtimeModel as 'llm'.
        # We explicitly disable STT/VAD/TTS to trigger the native A2A pipeline.
        super().__init__(
            instructions=prompt,
            llm=self._model,
            stt=None,
            vad=None,
            tts=None,
            tools=[fnc_ctx] if fnc_ctx else [],
        )
        
        self._workspace_id = workspace_id
        self._fnc_ctx = fnc_ctx
        self._session: Optional[AgentSession] = None
        self._room: Optional[rtc.Room] = None
        self._say_buffer = []
        self._started_event = asyncio.Event()
        self._greeting_sent = False

    async def start(self, room: rtc.Room, participant: Optional[rtc.RemoteParticipant] = None):
        """
        Starts the multimodal session using the Native A2A protocol.
        We deliberately ignore the 'participant' argument during the session.start() 
        call to avoid TypeErrors in LiveKit 1.5.x.
        """
        self._room = room
        
        # 3. Initialize AgentSession for Native A2A
        # Note: AgentSession constructor takes components, but .start() takes the Agent.
        self._session = AgentSession(
            llm=self._model,
            stt=None,
            vad=None,
            tts=None,
        )
        
        logger.info(f"🚀 [BRIDGE] Initializing Gemini 3.1 Live Session @ {room.name}")
        
        # 4. Map and Forward Events BEFORE starting
        self._setup_events()
        
        # 5. Start the session passing SELF as the agent.
        # EXTREMELY CRITICAL: In LiveKit 1.5.1, AgentSession.start() does NOT take 
        # a participant argument. We pass ONLY agent and room.
        try:
            await self._session.start(agent=self, room=room)
        except TypeError as te:
            logger.warning(f"⚠️ Caught expected (?) TypeError in AgentSession.start: {te}. Retrying with minimal args.")
            # Fallback for older/newer versions that might have shifted signatures
            await self._session.start(agent=self)
        
        logger.info("✅ [BRIDGE] Gemini 3.1 Live Handshake confirmed.")
        self._started_event.set()
        
        # 6. Flush buffered greetings
        while self._say_buffer:
            msg = self._say_buffer.pop(0)
            await self.say(msg["text"])

    def _setup_events(self):
        if not self._session:
            return

        @self._session.on("speaking_started")
        def _on_speaking_started():
            self.emit("agent_started_speaking")

        @self._session.on("speaking_finished")
        def _on_speaking_finished():
            self.emit("agent_stopped_speaking")

        @self._session.on("thinking_started")
        def _on_thinking_started():
            self.emit("agent_transcript", "Thinking...")

        @self._session.on("error")
        def _on_error(error: Exception):
            logger.error(f"❌ [BRIDGE ERROR] Session failure: {error}")
            self.emit("error", error)

    async def on_enter(self) -> None:
        """
        Called when the session actually starts. 
        This is a good time to send the initial greeting stimulus.
        """
        logger.info("🎭 [BRIDGE] Agent entered room. Ready for stimulus.")

    async def say(self, text: str, allow_interruptions: bool = True, add_to_chat_ctx: bool = True):
        """Native A2A greeting via stimulus."""
        if not self._started_event.is_set():
            logger.info(f"Buffering greeting: {text}")
            self._say_buffer.append({"text": text})
            return

        try:
            # Gemini 3.1 Live stimulus
            # In livekit-agents 1.5.1, the multimodal session is accessible via the LLM handle
            # We try multiple common patterns for robustness across minor version shifts
            rt_session = None
            if hasattr(self._session, "_llm_session"):
                rt_session = self._session._llm_session
            elif hasattr(self._session, "llm") and hasattr(self._session.llm, "session"):
                rt_session = self._session.llm.session
                
            if rt_session:
                logger.info(f"💬 [BRIDGE] Sending stimulus: {text}")
                # We use send_realtime_input (or equivalent) to trigger the A2A model
                if hasattr(rt_session, "send_realtime_input"):
                    await rt_session.send_realtime_input(text=text)
                elif hasattr(rt_session, "chat_ctx") and hasattr(rt_session.chat_ctx, "append"):
                    # Fallback for text-based fallback
                    self._session.llm.chat_ctx.messages.append(llm.ChatMessage(role="assistant", content=text))
            else:
                logger.warning("⚠️ [BRIDGE] No active RT session for stimulus. Using buffer.")
                self._say_buffer.append({"text": text})

        except Exception as e:
            logger.error(f"❌ [BRIDGE ERROR] stimulus failed: {e}", exc_info=True)

    def on(self, event: str, callback: Optional[Callable] = None):
        """Override to ensure events are attached to both bridge and session."""
        if callback is None:
            # Decorator usage
            def decorator(cb):
                super(MultimodalAgent, self).on(event, cb)
                if self._session:
                    self._session.on(event, cb)
                return cb
            return decorator
        
        super().on(event, callback)
        if self._session:
            self._session.on(event, callback)
        return callback

    async def stop(self):
        if self._session:
            await self._session.aclose()

    @property
    def session(self) -> Any:
        return self._session or self

    def done(self) -> bool:
        if self._session:
            # _closing and _started are internal fields in 1.5.1
            return getattr(self._session, "_closing", False) or not getattr(self._session, "_started", False)
        return not self._started_event.is_set()

