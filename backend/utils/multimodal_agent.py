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
    Fulfills the project's 'architectural parity' goal for Gemini 3.1 Flash Live.
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
        
        # Flag: True when the LLM is a native multimodal model (Gemini Live)
        self._is_native_audio = isinstance(model, llm.RealtimeModel)

        # Tools extraction
        tools = []
        if self._fnc_ctx:
            tools.extend(llm.find_function_tools(self._fnc_ctx))
                
        # Hack to bypass a LiveKit 1.5.1 bug for RealtimeModels
        if self._is_native_audio:
            from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream
            class DummyTTS(TTS):
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
        
        # 1. Initialize AgentSession for LiveKit 1.5.1
        self._session = AgentSession(
            stt=self._stt,
            vad=self._vad,
            llm=self._model,
            tts=self._tts,
            tools=self._voice_agent.tools, # Use tools already registered on voice_agent
        )
        
        # 2. Start the session with our voice_agent config
        await self._session.start(self._voice_agent, room=room)
        
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
        
        # Flush buffered greetings
        while self._say_buffer:
            msg = self._say_buffer.pop(0)
            self.say(msg["text"])

    def say(self, text: str, allow_interruptions: bool = True, add_to_chat_ctx: bool = True):
        """Standard 'say' method with improved resilience for Gemini Live."""
        if not self._started_event.is_set():
            logger.info(f"Session not yet ready, buffering greeting: {text}")
            self._say_buffer.append({"text": text})
            return

        try:
            if self._is_native_audio:
                # Gemini 3.1 Live Fix (PR #5238): Use current model's session if available
                if hasattr(self._model, "session") and self._model.session:
                    asyncio.create_task(self._model.session.send_realtime_input(text=text))
                else:
                    self._voice_agent.say(text, allow_interruptions=allow_interruptions, add_to_chat_ctx=add_to_chat_ctx)
                self._first_say_executed = True
            else:
                self._voice_agent.say(text, allow_interruptions=allow_interruptions, add_to_chat_ctx=add_to_chat_ctx)
        except Exception as e:
            logger.error(f"Failed to execute say on agent: {e}", exc_info=True)

    def stop(self):
        """Stops the agent session."""
        if self._session:
            self._session.aclose()

    @property
    def session(self) -> Any:
        return self._session or self._voice_agent

    def done(self) -> bool:
        """Returns True if the session is not yet setup or if it's already closed."""
        # For simplicity, if session is active we check its state
        if self._session:
            return self._session._closing or not self._session._started
        return not self._started_event.is_set()
