import asyncio
import logging
from typing import Optional, List
from livekit import rtc
from livekit.agents import llm, vad
from livekit.agents.llm import RealtimeModel
from livekit.agents.llm.tool_context import ToolContext
from livekit.agents.voice import Agent as VoiceAgent, AgentSession
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream

logger = logging.getLogger("multimodal-agent-bridge")

class DummyTTS(TTS):
    def __init__(self):
        super().__init__(capabilities=TTSCapabilities(streaming=False), sample_rate=24000, num_channels=1)
    def synthesize(self, text: str, **kwargs) -> ChunkedStream:
        raise NotImplementedError("Not used by Multimodal models")

class MultimodalAgent(rtc.EventEmitter):
    """
    A bridge for Gemini Multimodal Live and standard VoiceAgent parity.
    Wraps the LiveKit Agent to provide a consistent interface for the SupaAgent dashboard.
    """
    def __init__(
        self,
        model: RealtimeModel,
        fnc_ctx: Optional[ToolContext] = None,
        vad: Optional[vad.VAD] = None,
        instructions: str = "",
    ):
        super().__init__()
        self._model = model
        self._fnc_ctx = fnc_ctx
        self._vad = vad
        self._instructions = instructions
        
        # Tools in LiveKit can be passed as a single ToolContext or list of FunctionTools
        # We wrap it for the VoiceAgent
        chat_ctx = llm.ChatContext()
        if self._instructions:
            chat_ctx.add_message(role="system", content=self._instructions)
            
        # VoiceAgent natively supports RealtimeModel in 1.5.1
        # But there is a bug where it requires a TTS object to be present for the .say() method,
        # even if the model generates its own audio.
        self._voice_agent = VoiceAgent(
            llm=self._model,
            tts=DummyTTS(),
            tools=[self._fnc_ctx] if self._fnc_ctx else None,
            vad=self._vad,
            instructions=self._instructions,
            chat_ctx=chat_ctx
        )
        
        self._session: Optional[AgentSession] = None
        self._room: Optional[rtc.Room] = None
        self._participant: Optional[rtc.RemoteParticipant] = None
        self._say_buffer: List[str] = []
        self._is_native_audio = isinstance(model, RealtimeModel)

        # Setup internal event forwarding from the VoiceAgent
        self._setup_agent_events()

    def _setup_agent_events(self):
        """Forward core events from the underlying agent to this bridge."""
        @self._voice_agent.on("user_transcript")
        def on_user_transcript(transcript: llm.ChatItem):
            text = transcript.text_content() if hasattr(transcript, 'text_content') else getattr(transcript, 'content', "")
            self.emit("user_transcript", text)

        @self._voice_agent.on("agent_transcript")
        def on_agent_transcript(transcript: llm.ChatItem):
            text = transcript.text_content() if hasattr(transcript, 'text_content') else getattr(transcript, 'content', "")
            self.emit("agent_transcript", text)

        @self._voice_agent.on("user_speech_committed")
        def on_user_speech(msg: str):
            self.emit("user_speech_committed", msg)

        @self._voice_agent.on("agent_speech_committed")
        def on_agent_speech(msg: str):
            self.emit("agent_speech_committed", msg)

    async def start(self, room: rtc.Room, participant: rtc.RemoteParticipant):
        """Starts the agent session and flushes any buffered greetings."""
        self._room = room
        self._participant = participant
        
        logger.info(f"Starting MultimodalAgent for participant {participant.identity}")
        
        try:
            # Start the agent and capture the resulting session
            # Note: VoiceAgent.start returns an AgentSession object
            self._session = await self._voice_agent.start(self._room, self._participant)
            logger.info("Agent session started successfully")
            
            # Setup session-level event handlers
            self._setup_session_events()
            
            # Additional observability for multimodal sync
            @self._session.on("agent_started_speaking")
            def _on_speaking():
                logger.debug("Multimodal pipeline: Agent started recording/streaming audio")

            # Flush buffered say() calls (e.g., greetings)
            if self._say_buffer:
                for text in self._say_buffer:
                    logger.info(f"Flushing buffered greeting: {text}")
                    self.say(text)
                self._say_buffer.clear()
                
            return self._session
                
        except Exception as e:
            logger.error(f"Failed to start agent session: {e}", exc_info=True)
            raise

    def _setup_session_events(self):
        """Setup event handlers on the active session."""
        if not self._session:
            return

        @self._session.on("user_started_speaking")
        def _user_start():
            self.emit("user_started_speaking")

        @self._session.on("user_stopped_speaking")
        def _user_stop():
            self.emit("user_stopped_speaking")

        @self._session.on("agent_started_speaking")
        def _agent_start():
            self.emit("agent_started_speaking")

        @self._session.on("agent_stopped_speaking")
        def _agent_stop():
            self.emit("agent_stopped_speaking")

    def say(self, text: str):
        """
        Triggers the agent to speak. 
        If the session is not yet active, the text is buffered.
        """
        if self._session:
            logger.info(f"Agent saying via session: {text}")
            # If using RealtimeModel, we ideally want to bypass traditional TTS and use generate_reply()
            # but AgentSession.say() in 1.5.x handles RealtimeModel injection automatically
            self._session.say(text)
        else:
            logger.info(f"Buffering agent message: {text}")
            self._say_buffer.append(text)

    @property
    def session(self) -> Optional[AgentSession]:
        return self._session

    @property
    def voice_agent(self) -> VoiceAgent:
        return self._voice_agent
