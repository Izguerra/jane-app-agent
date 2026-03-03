import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Ensure project root is in sys.path to allow 'backend' imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
import asyncio
from datetime import datetime, timezone

from livekit.rtc import ConnectionState
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    tts,
)
from livekit import rtc
from livekit.plugins import silero
# Lazy import voice components
# from livekit.agents.voice import AgentSession, Agent
# from livekit.plugins import deepgram, google, silero, tavus, openai, elevenlabs

# Map Gemini Key if present
if os.getenv("GOOGLE_GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_GEMINI_API_KEY")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-agent")

def prewarm(proc: JobProcess):
    try:
        from livekit.plugins import silero
        logger.info("Avatar Agent Prewarm: Loading VAD model...")
        proc.userdata["vad"] = silero.VAD.load()
        logger.info("Avatar Agent Prewarm: VAD Loaded Successfully.")
    except Exception as e:
        logger.error(f"Avatar Agent Prewarm Failed: {e}")
        # We probably shouldn't kill the process here if possible, but VAD is critical.
        # But logging it is the first step.

# RobustTTS is now defined inside entrypoint for local import compatibility

async def entrypoint(ctx: JobContext):
    # File-based debug logging (survives crashes)
    def log_debug(msg):
        try:
            with open("backend/debug_avatar.log", "a") as f:
                f.write(f"DEBUG [{datetime.now(timezone.utc).isoformat()}]: {msg}\n")
        except: pass

    log_debug(f"ENTRYPOINT START | Room: {ctx.room.name} | JobID: {ctx.job.id}")

    try:
        from livekit.agents.voice import AgentSession, Agent
        from livekit.agents.voice.turn import TurnHandlingConfig
        from livekit.agents import llm
        from livekit.plugins import deepgram, openai, elevenlabs, tavus, silero
        from livekit.agents import tts
        from backend.agent_tools import AgentTools
        from backend.tools.worker_tools import WorkerTools
        from backend.database import SessionLocal, generate_comm_id
        from backend.models_db import Communication, Workspace, Agent as AgentModel, Customer
        from backend.services.skill_service import SkillService
        from backend.services.personality_service import PersonalityService
        # datetime already at top
        import json
    except Exception as e:
        import traceback
        msg = f"CRITICAL INITIALIZATION ERROR: {e}\n{traceback.format_exc()}"
        logger.error(msg)
        try:
            with open("backend/debug_avatar.log", "a") as f: 
                f.write(f"{msg}\n")
                f.flush()
        except: pass
        return

    # RobustTTS class remains...
    class RobustTTS(tts.TTS): 
        def __init__(self, primary: tts.TTS, fallback: tts.TTS):
            super().__init__(
                capabilities=primary.capabilities,
                sample_rate=primary.sample_rate,
                num_channels=primary.num_channels
            )
            self.primary = primary
            self.fallback = fallback
            self.use_fallback = False

        def synthesize(self, text: str, *args, **kwargs):
            if self.use_fallback:
                return self.fallback.synthesize(text, *args, **kwargs)
            try:
                return self.primary.synthesize(text, *args, **kwargs)
            except Exception as e:
                logger.error(f"TTS Synthesis Failed: {e}")
                self.use_fallback = True
                return self.fallback.synthesize(text, *args, **kwargs)

        def stream(self, *args, **kwargs):
            if self.use_fallback:
                return self.fallback.stream(*args, **kwargs)
            try:
                return self.primary.stream(*args, **kwargs)
            except Exception as e:
                logger.error(f"TTS Stream Failed: {e}")
                self.use_fallback = True
                return self.fallback.stream(*args, **kwargs)
    
    try:
        logger.info(f"Avatar Agent Entrypoint: Room {ctx.room.name}")
        
        # 1. Connect to Room (CRITICAL FIX)
        logger.info(f"Connecting to room {ctx.room.name}...")
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
             await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        logger.info(f"Connected to room {ctx.room.name}")
        
        # Set participant attributes to identify as assistant
        # This allows the frontend useVoiceAssistant hook to discover the agent
        asyncio.create_task(ctx.room.local_participant.set_attributes({"agent": "true"}))
        logger.info("Set 'agent' attribute on participant")
        with open("backend/debug_avatar.log", "a") as f: 
            f.write(f"Connected to room {ctx.room.name}\n")
            f.flush()

        # 2. Resolve Participant
        logger.info(f"Resolving participants in room {ctx.room.name}...")
        participant = None
        
        # Check existing participants first
        for p in ctx.room.remote_participants.values():
            if p.identity != "agent": # Skip other agents if any
                participant = p
                logger.info(f"Found existing participant: {p.identity}")
                break

        if not participant:
            logger.info("Waiting for participant join...")
            with open("backend/debug_avatar.log", "a") as f: 
                f.write("No existing participant. Waiting...\n")
                f.flush()
            try:
                participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=45.0)
                logger.info(f"PARTICIPANT JOINED: {participant.identity}")
                with open("backend/debug_avatar.log", "a") as f: 
                     f.write(f"PARTICIPANT JOINED: {participant.identity}\n")
                     f.flush()
            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for participant")
                with open("backend/debug_avatar.log", "a") as f: 
                    f.write("Timeout waiting for participant (45s)\n")
                    f.flush()
                return

    
        # 3. Settings
        import json
        # 3. Settings & Communication Tracking
        settings = {}
        workspace_id = None
        agent_id = None
        customer_id = None
        log_id = None
        start_time = datetime.now(timezone.utc)
        conversation_transcript = []

        if ctx.room.metadata:
            try:
                meta = json.loads(ctx.room.metadata)
                settings.update(meta)
                workspace_id = meta.get("workspace_id")
                agent_id = meta.get("agent_id")
                # Handle camelCase and snake_case unification
                settings["tavus_replica_id"] = meta.get("tavus_replica_id") or meta.get("tavusReplicaId")
                settings["tavus_persona_id"] = meta.get("tavus_persona_id") or meta.get("tavusPersonaId")
                
                # CRITICAL FIX: Check for avatarVoiceId and avatar_voice_id first (avatar mode)
                # Then fallback to voiceId/voice_id (voice mode)
                settings["voice_id"] = (
                    meta.get("avatarVoiceId") or 
                    meta.get("avatar_voice_id") or 
                    meta.get("voiceId") or 
                    meta.get("voice_id") or 
                    "Josh"
                )
                
                logger.info(f"Loaded Settings from Metadata: {list(settings.keys())}")
                with open("backend/debug_avatar.log", "a") as f: 
                     f.write(f"Settings: {json.dumps(settings, default=str)}\n")
            except Exception as e:
                logger.error(f"Failed to load settings from metadata: {e}")

        # Fallback: Check Participant Metadata (Frontend usually sends it here)
        if not settings.get("tavus_replica_id") or not workspace_id:
             logger.info("No Tavus ID or Workspace ID in Room Metadata. Checking Participant...")
             try:
                 # Use the 'participant' we just waited for or resolved
                 if participant and participant.metadata:
                     try:
                         meta = json.loads(participant.metadata)
                         logger.info(f"Found participant metadata: {meta}")
                         settings.update(meta)
                         if not workspace_id: workspace_id = meta.get("workspace_id")
                         if not agent_id: agent_id = meta.get("agent_id")
                         
                         # Handle camelCase
                         if meta.get("tavusReplicaId"): settings["tavus_replica_id"] = meta.get("tavusReplicaId")
                         if meta.get("tavusPersonaId"): settings["tavus_persona_id"] = meta.get("tavusPersonaId")
                         
                         # CRITICAL FIX: Check for avatarVoiceId and avatar_voice_id first
                         if meta.get("avatarVoiceId"): 
                             settings["voice_id"] = meta.get("avatarVoiceId")
                         elif meta.get("avatar_voice_id"): 
                             settings["voice_id"] = meta.get("avatar_voice_id")
                         elif meta.get("voiceId"): 
                             settings["voice_id"] = meta.get("voiceId")
                         elif meta.get("voice_id"):
                             settings["voice_id"] = meta.get("voice_id")
                         
                         with open("backend/debug_avatar.log", "a") as f: 
                             f.write(f"Updated Settings from Participant: {json.dumps(settings, default=str)}\n")
                     except Exception as pe:
                         logger.warning(f"Failed to parse participant metadata: {pe}")
             except Exception as e:
                 logger.error(f"Error checking participant metadata: {e}")

        # --- Skill & Personality Injection ---
        enabled_skills = []
        personality_prompt = None
        
        if agent_id:
            db_skills = SessionLocal()
            try:
                skill_service = SkillService()
                personality_service = PersonalityService()
                
                # 1. Fetch Enabled Skills
                enabled_skills = skill_service.get_skills_for_agent(db_skills, agent_id)
                
                # 2. Fetch Personality Prompt
                personality = personality_service.get_personality(db_skills, agent_id)
                personality_prompt = personality_service.generate_personality_prompt(personality)
                logger.info(f"Fetched {len(enabled_skills)} skills and { 'a' if personality_prompt else 'no' } personality for agent {agent_id}")
            except Exception as e:
                logger.error(f"Error fetching skills/personality for avatar agent {agent_id}: {e}")
            finally:
                db_skills.close()

        # INITIALIZE COMMUNICATION LOGGING
        if workspace_id:
            try:
                db = SessionLocal()
                # Find customer if possible
                user_email = settings.get("user_email") or settings.get("email")
                if user_email:
                    cust = db.query(Customer).filter(Customer.workspace_id == workspace_id, Customer.email == user_email).first()
                    if cust:
                        customer_id = cust.id

                # Construct user identifier
                base_identifier = customer_id if customer_id else (user_email or participant.identity or "unknown_visitor")
                final_user_identifier = f"{base_identifier}#{settings.get('session_id')}" if settings.get("session_id") else base_identifier

                log_entry = Communication(
                    id=generate_comm_id(),
                    type="call",
                    direction="inbound", # Standard for web avatar calls
                    status="ongoing",
                    started_at=start_time,
                    workspace_id=workspace_id,
                    channel="avatar_call",
                    user_identifier=final_user_identifier,
                    agent_id=agent_id,
                    customer_id=customer_id,
                    metadata={"mode": "avatar", "replica_id": settings.get("tavus_replica_id")}
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                log_id = log_entry.id
                logger.info(f"Logged Avatar Call Start: {log_id}")
                db.close()
            except Exception as log_err:
                logger.error(f"Failed to log avatar call start: {log_err}")
    
        tavus_replica_id = settings.get("tavus_replica_id")
        tavus_persona_id = settings.get("tavus_persona_id")
        
        # ... (Fallback logic for resolving persona) ...
        if tavus_replica_id and not tavus_persona_id:
             # Just quick log here, keeping logic minimal for replacement
             pass 

        # Components
        try:
            stt = deepgram.STT(model="nova-2")
        except Exception as e:
             raise

        
        # LLM — Gemini 3 Flash (fastest) > Mistral > DeepSeek/OpenRouter
        try:
            gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
            if gemini_key:
                from livekit.plugins import google as google_plugin
                logger.info("Connecting to Gemini 3 Flash (fastest LLM — 218 tok/s)")
                llm_instance = google_plugin.LLM(
                    model="gemini-3-flash-preview",
                    api_key=gemini_key,
                    temperature=0.7,
                )
            elif os.getenv("MISTRAL_API_KEY"):
                logger.info("Connecting to Mistral API with model: mistral-large-latest")
                llm_instance = openai.LLM(
                    model="mistral-large-latest",
                    base_url="https://api.mistral.ai/v1",
                    api_key=os.getenv("MISTRAL_API_KEY")
                )
            else:
                or_key = os.getenv("OPENROUTER_API_KEY")
                if or_key:
                    logger.info("Connecting to OpenRouter API (DeepSeek-V3)")
                    llm_instance = openai.LLM(
                        model="deepseek/deepseek-chat",
                        base_url="https://openrouter.ai/api/v1",
                        api_key=or_key
                    )
                else:
                    llm_instance = openai.LLM(model="gpt-4o-mini")
        except Exception as e:
             raise
            
        vad = ctx.proc.userdata["vad"]
        
        # TTS
        raw_voice_id = settings.get("voice_id", "Josh")
        voice_id = raw_voice_id.split('(')[0].strip()
        
        # ElevenLabs Mapping (Name -> UUID)
        ELEVENLABS_VOICE_MAP = {
            "Adam": "pNInz6obpgDQGcFmaJgB",
            "Alice": "Xb7hH8MSUJpSbSDYk0k2",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Bill": "pqHfZKP75CvOlQylNhV4",
            "Brian": "nPczCjzI2devNBz1zQrb",
            "Callum": "N2lVS1w4EtoT3dr4eOWO",
            "Charlie": "IKne3meq5aSn9XLyUdCD",
            "Chris": "iP95p4xoKVk53GoZ742B",
            "Daniel": "onwK4e9ZLuTAKqWW03F9",
            "Eric": "cjVigY5qzO86Huf0OWal",
            "George": "JBFqnCBsd6RMkjVDRZzb",
            "Harry": "SOYHLrjzK2X1ezoPC6cr",
            "Jessica": "pTJ3s5g507282l0yS44j",
            "Laura": "FGY2WhTYpPnrIDTdsKH5",
            "Liam": "TX3LPaxmHKxFdv7VOQHJ",
            "Lily": "zXbbPAe5GvWR44sRk39z",
            "Matilda": "XrExE9yK5vX15sY82p3N",
            "River": "SAz9YHcvj6GT2YYXdXww",
            "Roger": "CwhRBWXzGAHq8TQ4Fs17",
            "Sarah": "EXAVITQu4vr4xnSDxMaL",
            "Will": "21m00Tcm4T8k8a2Z47fG"
        }
        
        openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        if voice_id.lower() in [v.lower() for v in openai_voices]:
            logger.info(f"Using OpenAI TTS for voice: {voice_id}")
            tts = openai.TTS(voice=voice_id.lower())
        else:
            eleven_key = os.getenv("ELEVENLABS_API_KEY")
            if eleven_key:
                # Map name to ID if possible
                voice_id_to_use = ELEVENLABS_VOICE_MAP.get(voice_id, voice_id)
                logger.info(f"Attempting ElevenLabs TTS for voice: {voice_id} (ID: {voice_id_to_use})")
                try:
                    tts = elevenlabs.TTS(voice_id=voice_id_to_use, api_key=eleven_key)
                except Exception as e:
                    logger.error(f"ElevenLabs Init Failed: {e}. Falling back to OpenAI.")
                    tts = openai.TTS(voice="alloy")
            else:
                logger.warning("No ElevenLabs key found, falling back to OpenAI (alloy)")
                tts = openai.TTS(voice="alloy")

        # Wrap in RobustTTS if using ElevenLabs
        if not isinstance(tts, openai.TTS):
            logger.info("Wrapping ElevenLabs in RobustTTS fallback...")
            tts = RobustTTS(primary=tts, fallback=openai.TTS(voice="alloy"))

        # Initialize Tools
        workspace_id = settings.get("workspace_id", "wrk_default") 
        # Note: Avatar/Voice agents should resolve workspace_id properly. 
        # Using placeholder default if missing, but ideally passed in metadata.
        
        # Initialize WorkerTools
        allowed_workers = settings.get("allowed_worker_types", [])
        if enabled_skills:
            skill_slugs = [s.slug for s in enabled_skills]
            allowed_workers = list(set(allowed_workers + skill_slugs))
            
        worker_tools_instance = WorkerTools(
            workspace_id=workspace_id,
            allowed_worker_types=allowed_workers
        )
        
        # Initialize AgentTools
        agent_tools_instance = AgentTools(
            workspace_id=workspace_id,
            worker_tools=worker_tools_instance
        )
        
        # Vision Context State
        latest_image = {"frame": None}

        def before_llm_cb(assistant: AgentSession, chat_ctx: llm.ChatContext):
            if latest_image["frame"]:
                image = latest_image["frame"]
                # Convert frame to ChatImage (LiveKit native)
                # Ensure we are using correct image type for the LLM
                try:
                    # Provide image to the context's last user message if possible
                    # Or append a system message? usually user message is best.
                    if chat_ctx.messages and chat_ctx.messages[-1].role == "user":
                        # Check if model supports images (Gemini/GPT-4o do)
                        # We need to encode it
                        chat_ctx.messages[-1].content = [
                            llm.ChatImage(image=image),
                            chat_ctx.messages[-1].content if isinstance(chat_ctx.messages[-1].content, str) else ""
                        ]
                        logger.info("Vision Check: Injected video frame into LLM context.")
                        with open("backend/debug_avatar.log", "a") as f: f.write("Vision Check: Injected video frame into LLM context.\n")
                except Exception as e:
                    logger.error(f"Failed to attach image: {e}")
        
        # Combine all tools and deduplicate by name to prevent ValueError
        all_tools = llm.find_function_tools(agent_tools_instance)
        if worker_tools_instance:
            worker_function_tools = llm.find_function_tools(worker_tools_instance)
            existing_names = {t.info.name for t in all_tools}
            for t in worker_function_tools:
                if t.info.name not in existing_names:
                    all_tools.append(t)

        # Chat Context
        acknowledgement_rules = """CRITICAL CONVERSATIONAL RULES (STRICTLY ENFORCE):

1. **IMMEDIATE DYNAMIC ACKNOWLEDGMENT (MANDATORY):**
   - The INSTANT the user finishes speaking, you MUST respond with a brief, DYNAMIC acknowledgment.
   - Your acknowledgment must be CONTEXTUAL to what they asked — NOT a generic canned phrase.
   - VARY your acknowledgments every single time. NEVER repeat the same phrase twice in a row.
   - Examples of GOOD dynamic acknowledgments:
     * For weather: "Great question about the weather — let me check that..."
     * For flights: "Sure, let me look up that flight for you..."
     * For distance: "Good one! Let me calculate that distance..."
     * For general: "Absolutely, working on that now..."
   - BAD (too generic/repetitive): "Let me check that..." every time.
   - This acknowledgment must be SEPARATE from the tool call result.
   - NEVER call a tool silently without acknowledging first.

2. **PROGRESS UPDATES (FOR LONG OPERATIONS):**
   - If you expect a tool to take >3 seconds, immediately say: "This might take a moment..."
   - After 5 seconds of processing, say: "Still working on that..."
   - After 10+ seconds, say: "Almost there, this is taking a bit longer than expected..."
   - For background tasks (dispatch_worker_task), say: "I've started that task in the background. I'll let you know when it's done."

3. **NEVER REMAIN SILENT:**
   - You must ALWAYS respond verbally within 1 second of the user speaking.
   - If you're thinking or processing, say so immediately.
   - Silence is UNACCEPTABLE in voice conversations.
   - Even if you're unsure, acknowledge the user immediately.

4. **KEEP ACKNOWLEDGMENTS BRIEF BUT NATURAL:**
   - One short sentence maximum (5-10 words)
   - Sound human and conversational, not robotic
   - Get to the actual answer quickly after acknowledging

"""
        base_prompt = settings.get("prompt_template", "You are a helpful AI assistant.")
        
        # Inject Personality Prompt (SOUL.md style)
        if personality_prompt:
            base_prompt = f"{personality_prompt}\n\n{base_prompt}"

        # Inject Skills Instructions
        if enabled_skills:
            skill_info = "\n\nENRICHED SKILLS & CAPABILITIES:\n"
            skill_info += "You have been equipped with the following specialized skills. Follow their specific instructions strictly:\n\n"
            for skill in enabled_skills:
                skill_info += f"### {skill.name} ({skill.slug})\n{skill.instructions}\n\n"
            base_prompt += skill_info

        full_prompt = acknowledgement_rules + base_prompt
        
        initial_ctx = llm.ChatContext()
        initial_ctx.add_message(
            role="system",
            content=full_prompt
        )
        
        # 4. Create AgentSession (The Pipeline Manager)
        session = AgentSession(
            vad=vad,
            stt=stt,
            llm=llm_instance,
            tts=tts,
            tools=all_tools,
            turn_handling=TurnHandlingConfig(interruption={"mode": "vad"})
        )

        # Vision: Background Task to Capture Frames
        async def image_provider():
            while True:
                await asyncio.sleep(2)
                # Find video track
                video_track = None
                for p in ctx.room.remote_participants.values():
                    for t in p.track_publications.values():
                        if t.track and t.kind == rtc.TrackKind.KIND_VIDEO:
                            video_track = t.track
                            break
                    if video_track: break
                
                if video_track:
                    stream = rtc.VideoStream(video_track)
                    async for frame in stream:
                        latest_image["frame"] = frame
                        # We only need one frame per interval, so break immediate stream loop to wait
                        break
                    await stream.aclose()
        
        # Start vision loop
        asyncio.create_task(image_provider())

        # 5. Create Logic Agent (The Brain)
        agent_logic = Agent(
            instructions=full_prompt or "You are a helpful AI assistant."
        )
        # 6. Create Tavus Session (The Body)
        avatar = None
        if tavus_replica_id:
            try:
                # --- WSS FIX: Ensure LiveKit URL uses wss:// for Tavus ---
                original_url = os.environ.get("LIVEKIT_URL", "")
                if original_url.startswith("https://"):
                    fixed_url = original_url.replace("https://", "wss://")
                    os.environ["LIVEKIT_URL"] = fixed_url
                    logger.info(f"Fixed LIVEKIT_URL for Tavus: {fixed_url}")
                    with open("backend/debug_avatar.log", "a") as f: 
                        f.write(f"Fixed LIVEKIT_URL for Tavus: {fixed_url}\n")
                elif original_url.startswith("http://"):
                    fixed_url = original_url.replace("http://", "ws://")
                    os.environ["LIVEKIT_URL"] = fixed_url
                    logger.info(f"Fixed LIVEKIT_URL for Tavus: {fixed_url}")

                logger.info(f"Initializing Tavus session with replica={tavus_replica_id}, persona={str(tavus_persona_id)}")
                avatar = tavus.AvatarSession(
                    replica_id=tavus_replica_id,
                    persona_id=tavus_persona_id,
                )
                # Bridge Tavus to the Session
                logger.info("Starting Tavus Avatar...")
                await avatar.start(session, room=ctx.room)
                logger.info("Tavus Avatar Started!")
                
                # Log Conversation ID if available
                try:
                    cid = getattr(avatar, 'conversation_id', 'Unknown')
                    logger.info(f"Tavus Conversation ID: {cid}")
                    
                    # --- PUSH TO ROOM METADATA FOR WEB/E2E VISIBILITY ---
                    if cid and cid != 'Unknown':
                        current_meta = {}
                        if ctx.room.metadata:
                            try:
                                current_meta = json.loads(ctx.room.metadata)
                            except: pass
                        
                        current_meta["tavus_conversation_id"] = cid
                        await ctx.room.update_metadata(json.dumps(current_meta))
                        logger.info("Pushed Tavus ID to room metadata.")
                    
                    with open("backend/debug_avatar.log", "a") as f: 
                        f.write(f"TAVUS AVATAR STARTED! Conversation ID: {cid}\n")
                        f.write(f"Avatar Attributes: {dir(avatar)}\n")
                        f.flush()
                except Exception as meta_err:
                    logger.warning(f"Failed to push Tavus ID to metadata: {meta_err}")
            except Exception as e:
                msg = f"TAVUS ERROR: {e}"
                logger.error(msg)
                with open("backend/debug_avatar_error.log", "a") as f: 
                    f.write(f"{msg}\n")
                    f.write(f"Replica: {tavus_replica_id}, Persona: {tavus_persona_id}\n")
                    import traceback
                    f.write(traceback.format_exc() + "\n")
                    f.flush()
        else:
            logger.warning(f"Skipping Tavus Connection. Replica: {tavus_replica_id}, Persona: {tavus_persona_id}")

        # 7. Start the Voice/Agent Session
        await session.start(agent_logic, room=ctx.room, chat_ctx=initial_ctx)

        # 8. Send Greeting
        welcome_msg = settings.get("welcome_message") or "Hello! I am your AI assistant. How can I help you today?"
        logger.info(f"Avatar Session Started. Sending welcome message: {welcome_msg}")
        try:
            # session.responses.add(text=welcome_msg, allow_interruptions=True)
            # Actually, use session.say for immediate output if responses.add is for pipeline
            # Wait, SDK 1.3+ uses session.responses.add(text=...)
            # FIXED: AgentSession does not have .responses. Using .say().
            session.say(welcome_msg, allow_interruptions=True)
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
        # Add event listeners for transcription
        @session.on("user_speech_committed")
        def on_user_speech(msg: llm.ChatMessage):
            if isinstance(msg.content, str):
                logger.info(f"USER SPEECH: {msg.content}")
                conversation_transcript.append(f"USER: {msg.content}")

        @session.on("agent_speech_committed")
        def on_agent_speech(msg: llm.ChatMessage):
            if isinstance(msg.content, str):
                logger.info(f"AGENT SPEECH: {msg.content}")
                conversation_transcript.append(f"AGENT: {msg.content}")

        # Note: AgentSession doesn't have a direct .say() for welcome messages in older versions,
        # but the logic agent should handle the initial greeting if the LLM context allows.
        
        await asyncio.sleep(1) # Wait for connection
        
        # --- Lifecycle Wait ---
        shutdown_event = asyncio.Event()
        @ctx.room.on("disconnected")
        def on_room_disconnect(reason=None):
            logger.info("Room disconnected.")
            shutdown_event.set()

        # Loop
        await shutdown_event.wait()
        logger.info(f"Avatar Session Ending. Finalizing log {log_id}")

        # FINAL LOGGING UPDATE
        if log_id:
            try:
                db = SessionLocal()
                log = db.query(Communication).filter(Communication.id == log_id).first()
                if log:
                    log.status = "completed"
                    end_time = datetime.now(timezone.utc)
                    log.ended_at = end_time
                    
                    if conversation_transcript:
                        transcript_text = "\n".join(conversation_transcript)
                        log.transcript = transcript_text
                    
                    duration = (end_time - log.started_at).total_seconds()
                    log.duration = int(duration)
                    
                    # Update metadata with Tavus info if available
                    if avatar and hasattr(avatar, 'conversation_id'):
                        meta = dict(log.metadata or {})
                        meta["tavus_conversation_id"] = avatar.conversation_id
                        log.metadata = meta

                    db.commit()
                    logger.info(f"Finalized Log: {log_id}, Duration: {int(duration)}s")

                    # TRIGGER ANALYSIS (Sentiment, Intent, Outcome)
                    if conversation_transcript:
                        try:
                            from backend.services.analysis_service import AnalysisService
                            logger.info(f"Triggering analysis for avatar communication {log_id}")
                            # Await analysis to ensure it completes before process exits
                            await asyncio.wait_for(AnalysisService.analyze_communication(log_id, "\n".join(conversation_transcript)), timeout=60.0)
                            logger.info(f"Analysis completed for {log_id}")
                        except Exception as analysis_err:
                            logger.error(f"Failed to analyze avatar communication: {analysis_err}")
                db.close()
            except Exception as finalize_err:
                logger.error(f"Failed to finalize avatar communication log: {finalize_err}")

    except Exception as e:
        import traceback
        logger.error(f"CRITICAL AGENT CRASH: {e}\n{traceback.format_exc()}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        agent_name=os.getenv("AGENT_NAME", "supaagent-avatar-agent-v2")
        )
    )
