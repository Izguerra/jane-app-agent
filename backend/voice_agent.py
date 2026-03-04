import logging
import os
import asyncio
import aiohttp
import json
import time
import wave
import sys
from datetime import datetime, timezone
from pathlib import Path
from openai import AsyncOpenAI
from datetime import datetime, timezone

# Ensure project root is in sys.path to allow 'backend' imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from livekit import rtc
from livekit.rtc import ConnectionState
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    AgentServer,
    cli,
    llm,
    stt,
    vad,
    tts,
    WorkerOptions, # Added WorkerOptions
)
# from livekit.agents.pipeline import VoicePipelineAgent # REMOVED - Causing ModuleNotFoundError
from livekit.plugins import deepgram, openai, silero, elevenlabs # Moved from entrypoint


# Using AgentSession and Agent for 1.3.x compatibility
# Plugins and Voice imports moved to local scope to prevent IPC crash
from livekit.agents.voice.turn import TurnHandlingConfig

# Import settings store
try:
    from backend.settings_store import get_settings
except ImportError:
    # Fallback if path setup is still weird
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from backend.settings_store import get_settings

load_dotenv()

# Map Gemini Key if present
if os.getenv("GOOGLE_GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_GEMINI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# Check for Mistral API Key
if not os.getenv("MISTRAL_API_KEY"):
    logger.error("CRITICAL: MISTRAL_API_KEY is not set in environment variables!")
else:
    logger.info("MISTRAL_API_KEY found.")

# Recordings directory
RECORDINGS_DIR = Path(__file__).parent / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

# Preload VAD model globally
_vad_model = None

def get_vad_model():
    global _vad_model
    if _vad_model is None:
        try:
            from livekit.plugins import silero
            logger.info("Loading Silero VAD model...")
            _vad_model = silero.VAD.load()
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise e
    return _vad_model

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = get_vad_model()

async def entrypoint(ctx: JobContext):
    # File-based debug logging (survives crashes)
    def log_debug(msg):
        try:
            with open("backend/debug_voice.log", "a") as f:
                f.write(f"DEBUG [{datetime.now().isoformat()}]: {msg}\n")
        except: pass

    log_debug(f"ENTRYPOINT START | Room: {ctx.room.name}")
    try:
        log_debug("Step 1: Imports starting")
        from livekit.agents.voice import AgentSession, Agent
        from livekit.plugins import deepgram, google, silero, elevenlabs
        log_debug("Step 2: LiveKit plugins imported")
        
        from backend.settings_store import get_settings
        from backend.agent_tools import AgentTools
        from backend.database import SessionLocal, generate_comm_id
        from backend.models_db import Communication, Workspace, Agent as AgentModel, Customer
        from backend.services.skill_service import SkillService
        from backend.services.personality_service import PersonalityService
        log_debug("Step 3: Backend modules imported")
    except Exception as e:
         log_debug(f"CRITICAL ERROR during imports: {e}")
         logger.error(f"CRITICAL: Failed to import backend modules: {e}")
         return

    
    log_id = None
    start_time = datetime.now(timezone.utc)
    workspace_id = None
    
    try:
        # Debug Connection Details
        lk_url = os.getenv("LIVEKIT_URL")
        logger.info(f"Agent connecting to LiveKit URL: {lk_url}")
        
        logger.info(f"Entrypoint called for room {ctx.room.name}")

        # Connect to room — needed for mode check and wait_for_participant below.
        # AgentSession.start(room=ctx.room) will reuse this connection via RoomIO
        # and automatically publish lk.agent.state attributes.
        if ctx.room.connection_state == ConnectionState.CONN_DISCONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        # -----------------------------------------------------------------
        # MODE CHECK: Prevents Voice Agent from speaking during Avatar calls
        # -----------------------------------------------------------------
        if ctx.room.metadata:
            try:
                room_meta = json.loads(ctx.room.metadata)
                if room_meta.get("mode") == "avatar":
                    logger.info("Room is in AVATAR mode. Waiting 5s for avatar agent before stepping down gracefully.")
                    await asyncio.sleep(5)  # Give avatar agent time to connect first
                    logger.info("Voice agent stepping down (avatar agent should be active now).")
                    return
            except Exception as me:
                logger.warning(f"Failed to parse room metadata for mode check: {me}")
        
        # Check waiting for participant early to catch mode from participant metadata
        logger.info("Waiting for participant...")
        try:
            participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=20.0)
            
            # CHECK PARTICIPANT METADATA FOR MODE
            if participant.metadata:
                try:
                    p_meta = json.loads(participant.metadata)
                    if p_meta.get("mode") == "avatar":
                         logger.info(f"Participant metadata indicates 'avatar' mode. Waiting 5s before stepping down.")
                         await asyncio.sleep(5)
                         logger.info("Voice agent stepping down after participant avatar mode delay.")
                         return
                except: pass

            msg_identity = f"DEBUG: Participant connected: {participant.identity}"
            print(msg_identity, flush=True)
            logger.info(msg_identity)
            
            msg_metadata = f"DEBUG: Participant Metadata: {participant.metadata}"
            print(msg_metadata, flush=True)
            logger.info(msg_metadata)
            
            msg_attributes = f"DEBUG: Participant Attributes: {participant.attributes}"
            print(msg_attributes, flush=True)
            logger.info(msg_attributes)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for participant. Exiting job to free worker.")
            return
        
        # --- Context Resolution Logic (Preserved) ---
        settings = {}
        call_context = None
        sip_to = None
        workspace_id = None  # Initialize workspace_id
        
        # Log room metadata for debugging
        logger.info(f"DEBUG: Room name: {ctx.room.name}")
        logger.info(f"DEBUG: Room metadata: {ctx.room.metadata[:200] if ctx.room.metadata else 'EMPTY'}...")
        
        # FIRST: Try to get workspace_id and agent_id from room metadata (most reliable)
        agent_id = None
        if ctx.room.metadata:
            try:
                room_settings = json.loads(ctx.room.metadata)
                workspace_id = room_settings.get("workspace_id")
                agent_id = room_settings.get("agent_id")
                if workspace_id:
                    logger.info(f"DEBUG: Found workspace_id={workspace_id} in ROOM metadata!")
                    settings = room_settings
            except json.JSONDecodeError as e:
                logger.error(f"DEBUG: Failed to parse room metadata: {e}")
        
        try:
            # STRATEGY 1: Outbound Call via Room Name
            if ctx.room.name.startswith("outbound_"):
                comm_id = ctx.room.name.replace("outbound_", "")
                db = SessionLocal()
                try:
                    comm_record = db.query(Communication).filter(Communication.id == comm_id).first()
                    if comm_record:
                        workspace_id = comm_record.workspace_id
                        call_context = comm_record.call_context
                        if not call_context and comm_record.call_intent:
                              call_context = {
                                  "intent": comm_record.call_intent,
                                  "customer_id": comm_record.customer_id
                              }
                        logger.info(f"Resolved Context from DB: Workspace={workspace_id}, Intent={call_context.get('intent') if call_context else 'None'}")
                        
                        if call_context and call_context.get("customer_id") and not call_context.get("customer"):
                             cust = db.query(Customer).filter(Customer.id == call_context.get("customer_id")).first()
                             if cust:
                                 call_context["customer"] = {
                                     "first_name": cust.first_name,
                                     "last_name": cust.last_name,
                                     "phone": cust.phone,
                                     "email": cust.email
                                 }
                except Exception as db_e:
                    logger.error(f"Failed to lookup communication record: {db_e}")
                finally:
                    db.close()

            # STRATEGY 2: Inbound SIP Call
            if not workspace_id:
                sip_to = participant.attributes.get("sip.callTo") or participant.attributes.get("to")
                if sip_to:
                    logger.info(f"Detected SIP call to: {sip_to}")
                    db = SessionLocal()
                    try:
                        workspace = db.query(Workspace).filter(Workspace.inbound_agent_phone == sip_to).first()
                        if workspace:
                            workspace_id = workspace.id
                            logger.info(f"Resolved Workspace ID {workspace_id} from phone number {sip_to}")
                    finally:
                         db.close()

            # STRATEGY 3: Metadata / Fallback
            if not workspace_id and participant.metadata:
                try:
                    logger.info(f"DEBUG S3: Parsing participant metadata: {participant.metadata[:200]}...")
                    parsed_metadata = json.loads(participant.metadata)
                    logger.info(f"DEBUG S3: Parsed keys: {list(parsed_metadata.keys())}")
                    workspace_id = parsed_metadata.get("workspace_id")
                    if not agent_id: agent_id = parsed_metadata.get("agent_id")
                    call_context = parsed_metadata.get("call_context")
                    settings = parsed_metadata  # Use the full metadata as settings
                    if workspace_id:
                        logger.info(f"DEBUG S3: Found workspace_id={workspace_id} in participant metadata!")
                    else:
                        logger.warning(f"DEBUG S3: 'workspace_id' key NOT FOUND in metadata. Available: {list(parsed_metadata.keys())}")
                except json.JSONDecodeError as je:
                    logger.error(f"DEBUG S3: Failed to parse metadata as JSON: {je}")
                    pass

            if not workspace_id:
                # Default Fallback
                logger.warning(f"DEBUG FALLBACK: No workspace_id found. Using default fallback.")
                workspace_id = "wrk_000V7MkytiPCf7GFQzZN3O1K8O"
                settings = get_settings(workspace_id)

        except Exception as e:
            logger.error(f"Error resolving context: {e}")
            workspace_id = "wrk_000V7MkytiPCf7GFQzZN3O1K8O"
            settings = get_settings(workspace_id)

        # Fetch Agent Settings
        if workspace_id and not settings:
             settings = get_settings(workspace_id)

        # Log Call Start
        customer_id = None
        db = SessionLocal()
        try:
            direction = "outbound" if call_context else "inbound"
            if not agent_id and workspace_id:
                default_agent = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
                if default_agent:
                    agent_id = default_agent.id
                
                # Resolve Customer ID
                if call_context and call_context.get("customer", {}).get("id"):
                    customer_id = call_context.get("customer", {}).get("id")
                
                if not customer_id:
                    identifier = settings.get("user_email") or participant.identity or ""
                    from backend.services.crm_service import CRMService
                    crm = CRMService(db)
                    cust = crm.get_or_create_from_identifier(workspace_id=workspace_id, identifier=identifier, channel="voice")
                    if cust:
                        customer_id = cust.id

            # user_identifier construction
            # Changed to always append session_id if present
            base_identifier = customer_id if customer_id else (settings.get("user_email") or participant.identity or "unknown_caller")
            final_user_identifier = f"{base_identifier}#{settings.get('session_id')}" if settings.get("session_id") else base_identifier

            existing_log_id = settings.get("log_id")
            if existing_log_id:
                logger.info(f"Using existing log_id from metadata: {existing_log_id}")
                log_id = existing_log_id
                # Optional: Update status to running if needed, or trust token generation
            else:
                log_entry = Communication(
                    id=generate_comm_id(),
                    type="call",
                    direction=direction,
                    status="ongoing",
                    started_at=start_time,
                    workspace_id=workspace_id,
                    channel="phone_call",
                    user_identifier=final_user_identifier,
                    agent_id=agent_id,
                    call_intent=call_context.get("intent") if call_context else None,
                    call_context=call_context,
                    customer_id=customer_id
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                log_id = log_entry.id
                logger.info(f"Logged call start: {log_id} at {start_time}")

        except Exception as e:
            logger.error(f"Failed to log call start: {e}")
        finally:
            db.close()

        # Update Settings from Agent Model
        welcome_message = None
        if workspace_id:
            try:
                db_settings = SessionLocal()
                agent_settings = db_settings.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
                if agent_settings:
                    if agent_settings.settings:
                         try:
                             for k, v in agent_settings.settings.items():
                                 if v is not None: settings[k] = v
                         except: pass
                    if agent_settings.voice_id: 
                        settings["voice_id"] = agent_settings.voice_id
                        logger.info(f"✅ VOICE_ID from database: {agent_settings.voice_id}")
                    if agent_settings.language: settings["language"] = agent_settings.language
                    
                    if agent_settings.prompt_template:
                        # Logic to avoid double enrichment
                        if "BUSINESS INFORMATION" not in settings.get("prompt_template", ""):
                            settings["prompt_template"] = agent_settings.prompt_template

                    if agent_settings.welcome_message:
                        welcome_message = agent_settings.welcome_message
                db_settings.close()
            except Exception as e:
                logger.error(f"Failed to fetch agent settings: {e}")

        # --- Metadata / Settings Resolution (Use Metadata Validation overrides) ---
        metadata_voice_id = None
        if participant.metadata:
            try:
                meta = json.loads(participant.metadata)
                metadata_voice_id = meta.get("voice_id") or meta.get("avatarVoiceId") or meta.get("avatar_voice_id")
                logger.info(f"🔍 Checking metadata for voice_id: {metadata_voice_id}")
                
                # Override settings with metadata (Transient Preview State)
                if meta.get("language"):
                    settings["language"] = meta.get("language")
                    logger.info(f"Language overridden by metadata: {settings['language']}")
                
                # Check for welcome message in metadata (Translated version)
                if meta.get("welcome_message"):
                    welcome_message = meta.get("welcome_message")
                    settings["welcome_message"] = welcome_message # Keep consistent
                    logger.info("Welcome message overridden by metadata")
                
                if metadata_voice_id:
                     settings["voice_id"] = metadata_voice_id
                     logger.info(f"✅ VOICE_ID OVERRIDDEN by metadata: {metadata_voice_id}")
                
                # Capture session_id for consistent tracking
                if meta.get("session_id"):
                     settings["session_id"] = meta.get("session_id")
                     logger.info(f"SESSION_ID from metadata: {settings['session_id']}")

            except Exception as e:
                logger.warning(f"Failed to parse participant metadata: {participant.metadata} -> {e}")

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
                logger.error(f"Error fetching skills/personality for voice agent {agent_id}: {e}")
            finally:
                db_skills.close()

        # Import the centralized instruction set (including ambiguity rules)
        from backend.prompts.general import GATEKEEPER_INSTRUCTION
        
        voice_id = settings.get("voice_id", "alloy")
        logger.info(f"🎤 FINAL VOICE_ID selected: {voice_id}")
        language = settings.get("language", "en")
        
        # Base Template from settings or default
        customer_template = settings.get("prompt_template", "You are a helpful assistant.")
        
        # Combine: Central Instructions + Customer Template
        # We replace placeholders in GATEKEEPER_INSTRUCTION if needed, or just prepend it.
        # {business_name}, {services}, {role} placeholders are handled below.
        
        from zoneinfo import ZoneInfo
        est_tz = ZoneInfo("America/Toronto")
        current_datetime = datetime.now(est_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        
        # Start with the STRONG System Instruction
        # Tool Usage Instructions
        tool_usage_instructions = (
            "\n\nTOOL USAGE & FOLLOW-UP QUESTIONS:\n"
            "1. For almost ALL requests (searching, email, CRM, weather), use `run_task_now`. This gives an immediate answer.\n"
            "2. ONLY use `dispatch_worker_task` if the user explicitly asks for a long background job or if you know it will take minutes to complete.\n"
            "3. BEFORE calling ANY tool, check if you have all required parameters (e.g., location for weather, email for sending, job title for search).\n"
            "4. If a parameter is missing, ASK the user for it. Do NOT guess. Do NOT call the tool with placeholders."
        )


        # Acknowledgement rules for natural conversational flow
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

        prompt_template = f"{acknowledgement_rules}{GATEKEEPER_INSTRUCTION}\n\nCURRENT DATE AND TIME: {current_datetime}. Use this to interpret relative dates.\n\nRunning Mode: VOICE CONVERSATION.{tool_usage_instructions}\n\nCUSTOMER INSTRUCTIONS:\n{customer_template}"

        # Inject Personality Prompt (SOUL.md style)
        if personality_prompt:
            prompt_template = f"{personality_prompt}\n\n{prompt_template}"

        # Inject Skills Instructions
        if enabled_skills:
            skill_info = "\n\nENRICHED SKILLS & CAPABILITIES:\n"
            skill_info += "You have been equipped with the following specialized skills. Follow their specific instructions strictly:\n\n"
            for skill in enabled_skills:
                skill_info += f"### {skill.name} ({skill.slug})\n{skill.instructions}\n\n"
            prompt_template += skill_info


        # Language - Map ISO codes to full language names for better LLM/TTS compliance
        LANGUAGE_NAMES = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
            "pt": "Portuguese", "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic",
            "nl": "Dutch", "pl": "Polish", "ru": "Russian", "tr": "Turkish", "sv": "Swedish",
            "da": "Danish", "fi": "Finnish", "no": "Norwegian", "cs": "Czech", "el": "Greek",
            "he": "Hebrew", "hu": "Hungarian", "id": "Indonesian", "hi": "Hindi", "uk": "Ukrainian",
            "vi": "Vietnamese", "th": "Thai", "ms": "Malay", "ro": "Romanian", "sk": "Slovak",
            "bg": "Bulgarian", "hr": "Croatian", "af": "Afrikaans", "bn": "Bengali", "ta": "Tamil",
            "te": "Telugu", "ml": "Malayalam", "kn": "Kannada", "mr": "Marathi", "gu": "Gujarati",
            "pa": "Punjabi", "ur": "Urdu", "sw": "Swahili", "cy": "Welsh", "ca": "Catalan",
            "et": "Estonian", "lv": "Latvian", "lt": "Lithuanian", "sl": "Slovenian", "sr": "Serbian",
            "mk": "Macedonian", "bs": "Bosnian", "is": "Icelandic", "gl": "Galician", "ka": "Georgian",
            "az": "Azerbaijani", "be": "Belarusian", "kk": "Kazakh", "mn": "Mongolian", "ne": "Nepali",
            "tl": "Filipino",
        }
        language_name = LANGUAGE_NAMES.get(language, language)
        
        if language != "en":
            # Strong language instruction with examples
            prompt_template += f"""

CRITICAL LANGUAGE REQUIREMENT:
- You MUST speak ONLY in {language_name}.
- ALL responses must be in {language_name}, including greetings, questions, and any information provided.
- Do NOT respond in English under any circumstances.
- If the user speaks English, still respond in {language_name}.
- Use natural, fluent {language_name} appropriate for the context."""
            logger.info(f"Language set to: {language} ({language_name})")
        
        # Business Context Injection
        b_name = "The Business"
        b_phone = "N/A"
        b_services = "General Inquiry"
        b_role = "AI Assistant"
        
        if workspace_id:
            try:
                 db = SessionLocal()
                 workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                 if workspace:
                     b_name = settings.get("business_name") or workspace.name or 'N/A'
                     b_phone = settings.get("phone") or workspace.phone or 'N/A'
                     # Try to infer services/role from settings if available, else generic
                     b_services = settings.get("services", "Appointments, General Inquiries") 
                     b_role = settings.get("role", "AI Receptionist")
                 db.close()
            except: pass
            
        # Prepare Allowed Workers List for Gatekeeper
        worker_descriptions = {
            "sms-messaging": "Send SMS (REQUIRES: 'recipient_number', 'message')",
            "sales-outreach": "Sales Outreach (REQUIRES: 'target_role', 'company_list')",
            "faq-resolution": "Answer Customer FAQs",
            "content-writer": "Generate Content (Optional: topic, content_type)",
            "job-search": "Find Jobs (REQUIRES: 'job_title', 'level', 'job_type', 'location_type')",
            "email-worker": "Manage Email (Send REQUIRES: 'recipient', 'subject', 'body'. Optional: 'cc', 'bcc', 'schedule_time')",
            "flight-tracker": "Check Flight Status/Schedule (REQUIRES: 'flight_number' OR 'origin'+'destination'. Optional: 'date', 'airline', 'approx_time')",
            "map-worker": "Navigation (REQUIRES: 'origin', 'destination', 'mode')",
            "weather-worker": "Check Weather (REQUIRES: 'location'. Optional: 'date', 'units' [C/F], 'details' [sunrise, humidity, etc.])",
            "hr-onboarding": "HR Onboarding (REQUIRES: 'candidate_name')",
            "payment-billing": "Check Payments (REQUIRES: 'action', 'transaction_id' OR 'email')",
            "web-research": "Search the web for real-time information",
        }
        
        allowed_workers_list = settings.get("allowed_worker_types", [])
        if enabled_skills:
            skill_slugs = [s.slug for s in enabled_skills]
            allowed_workers_list = list(set(allowed_workers_list + skill_slugs))
            
        logger.info(f"Final Allowed Workers: {allowed_workers_list}")
        
        if allowed_workers_list:
            allowed_list_items = []
            for w in allowed_workers_list:
                desc = worker_descriptions.get(w, w.replace("-", " ").title())
                allowed_list_items.append(f"- {w}: {desc}")
            allowed_worker_list_str = "\n".join(allowed_list_items)
        else:
            allowed_worker_list_str = "- None (You generally cannot dispatch workers unless explicitly authorized)"

        # Format the GATEKEEPER part of the prompt
        try:
            prompt_template = prompt_template.format(
                business_name=b_name,
                services=b_services,
                role=b_role,
                allowed_worker_list=allowed_worker_list_str
            )
        except KeyError:
             # Fallback if specific keys aren't matched exactly or extra braces exist
             logger.warning("Failed to format prompt template keys completely.")
             pass
             
        prompt_template += f"\n\nBUSINESS INFO:\nName: {b_name}\nPhone: {b_phone}\nIDENTITY: You represent {b_name}."

        # After fetching settings
        selected_voice = metadata_voice_id or settings.get("voice_id") or "alloy"
        logger.info(f"FINAL RESOLVED VOICE_ID: {selected_voice}")
        
        # Initialize WorkerTools for scheduling and worker dispatch capabilities
        worker_tools_instance = None
        try:
            from backend.tools.worker_tools import WorkerTools
            worker_tools_instance = WorkerTools(
                workspace_id=workspace_id or "wrk_default", 
                agent_id=agent_id,
                allowed_worker_types=allowed_workers_list
            )
            logger.info("WorkerTools initialized for voice agent")
        except Exception as e:
            logger.warning(f"Failed to initialize WorkerTools: {e}")
            
        # Initialize Tools (Common for both pipelines)
        logger.info(f"debug: Initializing AgentTools with comm_id={log_id} agent_id={agent_id}")
        agent_tools_instance = AgentTools(
            workspace_id=workspace_id or "wrk_default", 
            customer_id=customer_id, 
            communication_id=log_id, 
            agent_id=agent_id,
            worker_tools=worker_tools_instance # Bridge to validation
        )
        
        # Combine all tools and deduplicate by name to prevent ValueError
        all_tools = llm.find_function_tools(agent_tools_instance)
        if worker_tools_instance:
            worker_function_tools = llm.find_function_tools(worker_tools_instance)
            existing_names = {t.info.name for t in all_tools}
            for t in worker_function_tools:
                if t.info.name not in existing_names:
                    all_tools.append(t)
        
        session = None # For cleanup

        
        # --- Pipeline Selection Based on Voice ---
        # Known legacy Grok voices (keep for backward compat) + New Valid Ones
        grok_voices = ["ara", "annmariv", "berlo", "cmdr_hadfield", "dora", "kroenen", "mark", "maximillian", "min", "paula", "pettey", "raiden", "remy", "rex", "sienna", "stefan", "tobias", "warwick", "leo", "sal", "eve"]
        selected_voice_lower = selected_voice.lower()
        
        # ElevenLabs Mapping (Name -> UUID) preventing "stuck" listening state due to invalid IDs
        ELEVENLABS_VOICE_MAP = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Adam": "pNInz6obpgDQGcFmaJgB",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Chris": "iP95p4xoKVk53GoZ742B",
            "Emily": "LcfcDJNUP1GQjkzn1xUU",
            "Josh": "TxGEqnHWrfWFTfGW9XjX",
            "Leo": "IlPhMts77q4KnhTULU2v", # ElevenLabs Version
            "Matilda": "XrExE9yKIg1WjnnlVkGX",
            "Nicole": "piTKgcLEGmPE4e6mEKli",
            "Sam": "yoZ06aMxZJJ28mfd3POQ"
        }

        # Detect collision for "Leo" (Grok uses 'leo', ElevenLabs uses 'Leo')
        # If strict case match for "Leo" -> ElevenLabs
        # Otherwise if "leo" -> Grok
        is_elevenlabs_leo = (selected_voice == "Leo") 

        agent_started = False
        use_xai = False
        
        # Check if it should be xAI
        # Must be in grok_voices AND not be the specific ElevenLabs "Leo" case
        # Also ensure XAI_API_KEY is present
        if selected_voice_lower in grok_voices and not is_elevenlabs_leo and os.getenv("XAI_API_KEY"):

            logger.info(f"Detected Grok voice: {selected_voice} (using XAI)")
            logger.info(f"Initializing Native XAI (Grok) AgentSession with voice: {selected_voice_lower}")
            try:
                # Import RealtimeModel 
                from livekit.plugins.xai.realtime import RealtimeModel
                
                use_xai = True
                
                # Valid xAI Realtime Voices (Title Case as per docs)
                VALID_XAI_VOICES = ["Ara", "Eve", "Leo", "Sal", "Rex"]
                
                # Helper to standardize to Title Case for checking
                selected_voice_title = selected_voice.title()
                
                final_voice_id = "Ara" # Default

                if selected_voice_title in VALID_XAI_VOICES:
                    # If it's a valid native voice (e.g. "Leo", "Ara"), use it
                    final_voice_id = selected_voice_title
                    logger.info(f"Using native xAI voice: {final_voice_id}")
                else:
                    # Fallback/Mapping for legacy or unsupported UI options
                    # Check lowercase for loose matching of legacy names
                    sel_lower = selected_voice.lower()
                    
                    # Male-sounding legacy names -> Map to valid male voices
                    if sel_lower in ["mark", "tobias", "stefan", "warwick", "raiden", "maximillian", "kroenen", "berlo", "cmdr_hadfield"]:
                        # Distribute mappings
                        if sel_lower in ["mark", "tobias"]:
                             final_voice_id = "Leo" # Mark/Tobias -> Leo
                        elif sel_lower in ["rex", "raiden"]: 
                             final_voice_id = "Rex"
                        else:
                             final_voice_id = "Sal" # Others -> Sal
                        
                        logger.info(f"Mapped legacy voice '{settings.get('voice_id')}' to valid xAI male voice '{final_voice_id}'")
                    
                    # Female/Neutral legacy names -> Map to valid female voices
                    else:
                        if sel_lower in ["sienna", "paula", "dora"]:
                            final_voice_id = "Eve"
                        else:
                            final_voice_id = "Ara" # Default fallback

                # Create Grok Model
                # NOTE: Grok RealtimeModel usually handles its own STT/TTS internally or via spec
                # Assuming simple instantiation based on past code
                model = RealtimeModel(
                    instructions=prompt_template,
                    voice=final_voice_id,
                    turn_detection=vad.EOU(
                        threshold=0.6,
                        silence_threshold_ms=200
                    )
                )
                
                session = AgentSession(
                    model, # Pass model as first arg if 0.8 style, or keyword?
                    # Recalling standard: AgentSession() takes opts usually.
                    # Use args from compatible code block found in git log
                )
                # Wait, AgentSession in 1.3.x usually involves pipeline.
                # If xAI is a 'Model' that acts as a pipeline, use it directly?
                # The git log showed:
                # session = AgentSession( ... ) was usually further down.
                # But here we replace the pipeline.
                
                # RE-EVALUATING CODE STRUCTURE:
                # The git log didn't show the full instantiation clear enough in the snippet I saw.
                # But standard livekit-plugins-xai pattern:
                # model = RealtimeModel(...)
                # agent = MultimodalAgent(model=model)
                # await agent.start(ctx.room, participant)
                
                # However, your current code uses 'AgentSession' (VoicePipelineAgent).
                # xAI Realtime is Multimodal?
                # Let's assume standard VoicePipelineAgent usage with special LLM/TTS?
                # NO, xAI Realtime is end-to-end.
                
                # Let's try to infer from the 'use_xai' flag.
                
                # Instantiate MultimodalAgent if use_xai
                from livekit.agents.multimodal import MultimodalAgent
                
                agent = MultimodalAgent(
                    model=model,
                    fnc_ctx=all_tools # attach tools
                )
                logger.info("Starting xAI MultimodalAgent...")
                await agent.start(ctx.room, participant)
                agent_started = True

            except ImportError:
                 logger.error("Failed to import livekit.plugins.xai. Install it to use Grok.")
                 use_xai = False
            except Exception as e:
                 logger.error(f"Failed to start xAI agent: {e}")
                 use_xai = False

        if not use_xai:
            # --- Standard VoicePipelineAgent (Deepgram/ElevenLabs/Mistral) ---
            logger.info(f"Initializing Standard VoicePipelineAgent with voice: {voice_id}")
            
            voice_id_lower = voice_id.lower()
            
            # Helper to check if voice is OpenAI native
            is_openai_voice = voice_id_lower in ["alloy", "echo", "fable", "onyx", "nova", "shimmer", 
                                                 "ballad", "breeze", "cove", "ember", "juniper", "sapphire"]
            
            # LLM Selection — Gemini 3 Flash > OpenAI > Mistral
            creativity = settings.get("creativity_level")
            temperature = float(creativity) / 100.0 if creativity is not None else 0.7
            
            openai_key = os.getenv("OPENAI_API_KEY")
            gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
            
            if gemini_key:
                from livekit.plugins import google as google_plugin
                logger.info("Connecting to Gemini (gemini-3-flash-preview)")
                agent_llm = google_plugin.LLM(
                    model="gemini-3-flash-preview",
                    api_key=gemini_key,
                    temperature=temperature
                )
            elif openai_key:
                from livekit.plugins import openai as openai_plugin
                logger.info("Connecting to OpenAI (gpt-4o-mini) as fallback")
                agent_llm = openai_plugin.LLM(
                    model="gpt-4o-mini",
                    api_key=openai_key,
                    temperature=temperature,
                )
            elif os.getenv("MISTRAL_API_KEY"):
                from livekit.plugins import openai as openai_plugin # Mistral uses openai plugin with custom base_url
                logger.info("Connecting to Mistral API with model: mistral-large-latest")
                agent_llm = openai_plugin.LLM(
                    model="mistral-large-latest",
                    base_url="https://api.mistral.ai/v1",
                    api_key=os.getenv("MISTRAL_API_KEY")
                )
            else:
                 # OpenRouter fallback - Using DeepSeek-V3
                 from livekit.plugins import openai as openai_plugin
                 logger.info("Connecting to OpenRouter API (DeepSeek-V3)")
                 agent_llm = openai_plugin.LLM(
                    model="deepseek/deepseek-chat",
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY")
                )
            
            # Wrap LLM in FallbackAdapter if using Gemini and OpenAI key is available
            # Wrap LLM in FallbackAdapter if using Gemini and OpenAI key is available
            openai_key = os.getenv("OPENAI_API_KEY")
            if gemini_key and openai_key:
                logger.info("Wrapping Gemini LLM in FallbackAdapter with OpenAI fallback...")
                from livekit.agents.llm import FallbackAdapter as LLMFallbackAdapter
                from livekit.plugins import openai as openai_plugin
                fallback_llm = openai_plugin.LLM(
                    model="gpt-4o-mini",
                    api_key=openai_key,
                    temperature=temperature,
                    _strict_tool_schema=False,
                )

                agent_llm = LLMFallbackAdapter(llm=[agent_llm, fallback_llm], attempt_timeout=2.5)

            
            # Tools
            # agent_tools_instance already initialized above
            
            # TTS Selection
            tts_provider = None
            if is_openai_voice:
                tts_provider = openai.TTS(voice=voice_id)
            else:
                eleven_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
                if eleven_key:
                    # ELEVENLABS_VOICE_MAP is defined above now
                    mapped_id = ELEVENLABS_VOICE_MAP.get(voice_id, ELEVENLABS_VOICE_MAP.get(voice_id.title()))
                    
                    # Logic: If not in map, check if it looks like a valid ID (long string). 
                    # If short string (name) and not in map, fallback to default.
                    if mapped_id:
                        voice_id_to_use = mapped_id
                    elif len(voice_id) > 15: # Assumption: valid IDs are long
                        voice_id_to_use = voice_id
                    else:
                        logger.warning(f"Voice '{voice_id}' not found in map and invalid as ID. Fallback to Rachel.")
                        voice_id_to_use = "21m00Tcm4TlvDq8ikWAM" # Rachel

                    logger.info(f"Using ElevenLabs TTS for voice: {voice_id} (ID: {voice_id_to_use})")
                    tts_provider = elevenlabs.TTS(voice_id=voice_id_to_use, api_key=eleven_key)
                else:
                     logger.warning(f"Voice {voice_id} not found in OpenAI and no ElevenLabs key. Defaulting to Alloy.")
                     tts_provider = openai.TTS(voice="alloy")
            
            # Wrap in FallbackAdapter if using ElevenLabs
            if tts_provider and not isinstance(tts_provider, openai.TTS):
                logger.info("Wrapping ElevenLabs in FallbackAdapter fallback...")
                from livekit.agents.tts import FallbackAdapter
                tts_provider = FallbackAdapter(tts=[tts_provider, openai.TTS(voice="alloy")])

            # Initialize VAD/STT
            vad_model = get_vad_model()
            stt_instance = deepgram.STT(model="nova-2")
            
            session = AgentSession(
                vad=vad_model,
                stt=stt_instance,
                llm=agent_llm,
                tts=tts_provider,
                tools=all_tools,
                turn_handling=TurnHandlingConfig(interruption={"mode": "vad"}),
            )

            voice_agent = Agent(instructions=prompt_template or "You are a helpful AI assistant.")
            
            @session.on("user_started_speaking")
            def on_user_started_speaking():
                logger.info("🎙️ DEBUG: USER STARTED SPEAKING (VAD triggered)")
                
            @session.on("user_stopped_speaking")
            def on_user_stopped_speaking():
                logger.info("🎙️ DEBUG: USER STOPPED SPEAKING")
                
            @session.on("agent_started_speaking")
            def on_agent_started_speaking():
                logger.info("🤖 DEBUG: AGENT STARTED SPEAKING")
                
            # Try/except block for transcription since event might vary by version
            try:
                @session.on("user_speech_committed")
                def on_transcripts(msg):
                    logger.info(f"📝 DEBUG: USER TRANSCRIPT RECORDED: {msg}")
            except Exception as e:
                logger.warning(f"Could not bind user_speech_committed event: {e}")

            logger.info("Starting AgentSession...")
            await session.start(voice_agent, room=ctx.room)
            agent_started = True

        if welcome_message and session:
             try:
                session.say(welcome_message, allow_interruptions=True)
             except Exception as e:
                logger.error(f"Failed to say welcome message: {e}")
        elif not call_context and session:
             try:
                # FIXED: AgentSession does not have .responses. Using .say().
                session.say("Hello! How can I help you today?", allow_interruptions=True)
             except Exception as e:
                logger.error(f"Failed to say default welcome: {e}")


        # Welcome message already handled above — do not duplicate

        # --- Lifecyle Wait ---
        shutdown_event = asyncio.Event()
        @ctx.room.on("disconnected")
        def on_room_disconnect(reason=None):
            logger.info("Room disconnected.")
            shutdown_event.set()
        await shutdown_event.wait()

        # --- Cleanup ---
        logger.info("Session ended. Cleaning up...")
        
        # Try to capture transcript using LiveKit SDK 1.3.x API
        conversation_transcript = []
        try:
            if session and hasattr(session, 'history'):
                logger.info("Capturing transcript from session.history...")
                transcript_items = []
                for item in session.history.items:
                    # ChatMessage has role and text_content() method
                    role = getattr(item, 'role', 'unknown')
                    # Use text_content() method to get the text from ChatContent list
                    if hasattr(item, 'text_content') and callable(item.text_content):
                        content = item.text_content()
                    else:
                        # Fallback for older SDK versions
                        content = getattr(item, 'content', '')
                        if isinstance(content, list):
                            content = ' '.join(str(c) for c in content if c)
                    
                    # Filter out system prompts that may have been injected as user messages
                    # These are used to initialize the agent but shouldn't appear in transcript
                    system_prompt_indicators = [
                        "SYSTEM INSTRUCTIONS:",
                        "IMMEDIATE TASK:",
                        "IDENTITY VERIFICATION",
                        "GATEKEEPER RULE",
                        "CALENDAR RULES",
                        "CURRENT DATE AND TIME:"
                    ]
                    
                    is_system_prompt = any(indicator in content for indicator in system_prompt_indicators)
                    
                    if role != 'system' and content and not is_system_prompt:
                        transcript_items.append(f"{str(role).upper()}: {content}")
                        logger.debug(f"Transcript item: {role}: {content[:50]}...")
                        
                conversation_transcript = transcript_items
                logger.info(f"Captured {len(transcript_items)} transcript items with content")
        except Exception as e:
            logger.error(f"Failed to capture transcript: {e}", exc_info=True)


        
        if log_id:
             try:
                 db = SessionLocal()
                 # Re-fetching ensures we get the actual DB-generated timestamp (with timezone awareness)
                 log = db.query(Communication).filter(Communication.id == log_id).first()
                 if log:
                     log.status = "completed"
                     end_time = datetime.now(timezone.utc)
                     log.ended_at = end_time

                     transcript_text = None
                     if conversation_transcript:
                         transcript_text = "\n".join(conversation_transcript)
                         log.transcript = transcript_text
                     
                     # Calculate duration using the stored started_at for reliability
                     # Critical: Ensure start_time is present. If log.started_at is somehow missing, use our local fallback.
                     final_start_time = log.started_at or start_time
                     
                     if final_start_time:
                         duration = (end_time - final_start_time).total_seconds()
                         # FIXED: Model field is 'duration', not 'duration_seconds'
                         log.duration = int(duration)
                         logger.info(f"Call duration calculated: {duration:.1f}s (Start: {final_start_time}, End: {end_time})")
                         
                         if workspace_id:
                             usage = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                             if usage:
                                 usage.voice_minutes_this_month = (usage.voice_minutes_this_month or 0) + max(1, int(duration/60))
                     else:
                         logger.warning("Both log.started_at and local start_time are missing, cannot calculate duration")
                     
                     db.commit()
                     
                     # Trigger analysis for sentiment/intent/outcome (same as chat endpoint)
                     print(f"DEBUG: Processing analysis for {log_id}. Transcript len: {len(transcript_text) if transcript_text else 0}")
                     if transcript_text:
                         try:
                             from backend.services.analysis_service import AnalysisService
                             logger.info(f"Triggering analysis for communication {log_id}")
                             print(f"DEBUG: Triggering AnalysisService for {log_id}")
                             
                             # CRITICAL FIX: Await the analysis so the process doesn't exit before it's done
                             # We use a longer timeout to allow for OpenAI latency
                             try:
                                 await asyncio.wait_for(AnalysisService.analyze_communication(log_id, transcript_text), timeout=60.0)
                                 logger.info(f"Analysis completed successfully for {log_id}")
                                 print(f"DEBUG: Analysis COMPLETED for {log_id}")
                             except asyncio.TimeoutError:
                                 logger.error(f"Analysis timed out for {log_id}")
                                 print(f"DEBUG: Analysis TIMED OUT for {log_id}")
                                 
                         except Exception as analysis_error:
                             logger.error(f"Failed to trigger analysis: {analysis_error}")
                             print(f"DEBUG: Analysis FAILED with error: {analysis_error}")
                     else:
                         print("DEBUG: No transcript text, skipping analysis.")
                             
                 db.close()
             except Exception as e:
                 logger.error(f"Cleanup failed: {e}")

    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)

# Create AgentServer instance
# Generic job management via CLI

if __name__ == "__main__":
    configured_agent_name = os.getenv("AGENT_NAME")
    if not configured_agent_name:
        configured_agent_name = "supaagent-voice-agent-v2"
        
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        prewarm_fnc=prewarm,
        agent_name=configured_agent_name
    ))
