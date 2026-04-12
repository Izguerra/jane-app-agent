import logging
from datetime import datetime
from backend.prompts.general import BUSINESS_GATEKEEPER_INSTRUCTION, PERSONAL_GATEKEEPER_INSTRUCTION

logger = logging.getLogger("voice-prompt-builder")

class VoicePromptBuilder:
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

    WORKER_DESCRIPTIONS = {
        "sms-messaging": "Send SMS (REQUIRES: 'recipient_number', 'message')",
        "sales-outreach": "Sales Outreach (REQUIRES: 'target_role', 'company_list')",
        "faq-resolution": "Answer Customer FAQs",
        "content-writer": "Generate Content (Optional: topic, content_type)",
        "job-search": "Find Jobs (REQUIRES: 'job_title', 'level', 'job_type', 'location_type')",
        "email-worker": "Manage Email (Send REQUIRES: 'recipient', 'subject', 'body')",
        "flight-tracker": "Check Flight Status/Schedule (REQUIRES: 'flight_number' OR 'origin'+'destination')",
        "map-worker": "Navigation & Directions (REQUIRES: 'origin', 'destination', 'mode')",
        "weather-worker": "Check Weather (REQUIRES: 'location')",
        "hr-onboarding": "HR Onboarding (REQUIRES: 'candidate_name')",
        "payment-billing": "Check Payments (REQUIRES: 'action', 'transaction_id')",
        "web-research": "Search the web for real-time information",
        "lead-research": "Research potential leads and companies",
        "lead-research-legacy": "Legacy lead research worker",
        "compliance-risk": "Analyze text for compliance and risk factors",
        "content-moderation": "Moderate content for safety and guidelines",
        "order-status": "Check status of an order",
        "sentiment-escalation": "Analyze sentiment and handle escalations",
        "meeting-coordination": "Coordinate and schedule meetings",
        "data-entry": "Automate data entry tasks",
        "document-processing": "Extract information from documents",
        "intelligent-routing": "Route inquiries to the correct department",
        "it-support": "Provide basic IT support and troubleshooting",
        "translation-localization": "Translate and localize content",
    }

    ACKNOWLEDGEMENT_RULES = """CRITICAL CONVERSATIONAL RULES (STRICTLY ENFORCE):

1. **IMMEDIATE DYNAMIC ACKNOWLEDGMENT (MANDATORY):**
   - The INSTANT the user finishes speaking, you MUST respond with a brief, DYNAMIC acknowledgment.
   - Your acknowledgment must be CONTEXTUAL to what they asked — NOT a generic canned phrase.
   - VARY your acknowledgments every single time. 
   - Examples: "Checking that now...", "Great question, let me look up...", "Absolutely, researching that..."
   - NEVER call a tool silently without acknowledging first.

2. **PROGRESS UPDATES:**
   - If a tool takes time, say: "This might take a moment...", "Still working on that...", "Almost there..."

3. **NEVER REMAIN SILENT:**
   - Silence is UNACCEPTABLE. If processing, speak immediately to acknowledge.

4. **KEEP IT NATURAL:**
   - Sound human and conversational, not robotic.

5. **PRONUNCIATION & FORMATTING (CRITICAL):**
   - For phone numbers, postal codes, zip codes, airline codes (e.g., AC, LH), airport codes (e.g., YYZ, JFK, LHR), or ID strings, ALWAYS insert a space between EVERY single character (e.g., "L 9 T 0 E 2", "Y Y Z", "A C", "4 1 6 - 7 8 6 - 5 7 8 6").
   - NEVER pronounce these codes as single spoken words. This ensures the text-to-speech engine pronounces individual characters correctly.

"""

    # This mapping connects skill slugs to their direct tool methods
    SKILL_TO_DIRECT_TOOLS = {
        "web-research": "`web_search`",
        "weather-worker": "`get_weather`",
        "sms-messaging": "`send_sms_notification`",
        "email-worker": "`send_email_notification`, `list_inbox_emails`, or `read_email_details`",
        "email-composer": "`send_email_notification`, `list_inbox_emails`, or `read_email_details`",
        "map-worker": "`get_directions`",
        "flight-tracker": "`get_flight_status`",
        "advanced-browsing": "`web_search`",
        "google-search": "`web_search`",
        "lead-research": "`web_search` or `search_customers` or `get_current_time`",
        "general-utility": "`get_current_time`"
    }

    @staticmethod
    def get_allowed_tool_names(enabled_skills) -> list:
        """Returns a clean list of Python method names allowed by the given skills."""
        import re
        # Core system tools that are always allowed
        allowed_methods = ["run_task_now", "get_current_time", "search_knowledge_base"]
        
        if enabled_skills:
            for skill in enabled_skills:
                raw_mapping = VoicePromptBuilder.SKILL_TO_DIRECT_TOOLS.get(skill.slug, "")
                # Robust extraction: find ALL strings enclosed in backticks
                matches = re.findall(r'`([^`]+)`', raw_mapping)
                for method in matches:
                    # Clean up the method name (remove spaces or parentheticals if they snuck in)
                    clean_method = method.split()[0].strip()
                    allowed_methods.append(clean_method)
        return list(set(allowed_methods))

    @staticmethod
    def build_prompt(settings, personality_prompt, enabled_skills, workspace_info, current_datetime_str, client_location, agent_type="business", call_context=None):
        # 1. Choose Gatekeeper Template
        is_personal = agent_type == "personal" or settings.get("agent_type") == "personal"
        base_template = PERSONAL_GATEKEEPER_INSTRUCTION if is_personal else BUSINESS_GATEKEEPER_INSTRUCTION
        
        # 2. Build Tool List (Dynamic)
        allowed_workers = settings.get("allowed_worker_types", [])
        direct_tool_list = []
        
        if enabled_skills:
            for skill in enabled_skills:
                # Add to workers list
                if skill.slug not in allowed_workers:
                    allowed_workers.append(skill.slug)
                # Add to direct tool usage list (Point 1 in prompt)
                if skill.slug in VoicePromptBuilder.SKILL_TO_DIRECT_TOOLS:
                    direct_tool_list.append(VoicePromptBuilder.SKILL_TO_DIRECT_TOOLS[skill.slug])
        
        # Ensure standard essentials are included if not specified but needed
        if is_personal:
            # Personal agents usually have core tools enabled by default in prompt if not explicitly disabled
            pass

        allowed_list_str = "\n".join([f"- {w}: {VoicePromptBuilder.WORKER_DESCRIPTIONS.get(w, w)}" for w in allowed_workers]) or "- None"

        # 3. Format Template Safely
        try:
            gatekeeper = base_template.format(
                business_name=workspace_info.get("name", "Individual" if is_personal else "The Business"),
                services=workspace_info.get("services", "General Utility" if is_personal else "Inquiries"),
                role=workspace_info.get("role", "Assistant" if is_personal else "Support"),
                allowed_worker_list=allowed_list_str
            )
        except Exception as e:
            logger.warning(f"Template formatting failed: {e}")
            gatekeeper = base_template

        # 4. Assemble Tool Usage (Dynamic based on selected capabilities)
        tool_instr = "\n\n### 🛠️ TOOL USAGE & PERMISSIONS ###\n"
        if direct_tool_list:
            tool_instr += f"1. DIRECT TOOLS: You have immediate access to: {', '.join(list(set(direct_tool_list)))}. USE THEM whenever relevant.\n"
        else:
            tool_instr += "1. DIRECT TOOLS: No direct tools enabled. Rely on general conversation or workers.\n"
            
        tool_instr += "2. BACKGROUND WORKERS: Use `run_task_now` for specialized operations or background tasks.\n"
        tool_instr += "3. MANDATORY: ALWAYS acknowledge the user BEFORE calling any tool.\n"

        # 5. Build Environment Block
        location_context = f"CURRENT ENVIRONMENT CONTEXT:\n- Reference Timezone: {settings.get('client_timezone', 'America/Toronto')} (Local Reference)\n- User Location: {client_location or 'Unknown'}\n"
        
        call_context_str = ""
        if call_context:
            call_context_str = "\n### MISSION-CRITICAL CALL CONTEXT ###\n"
            call_context_str += f"REASON FOR CALL: {call_context.get('intent', 'General')}\n"
            if call_context.get('customer'):
                cust = call_context.get('customer')
                call_context_str += f"CUSTOMER: {cust.get('full_name')} ({cust.get('email')}, {cust.get('phone')})\n"
            if call_context.get('appointment'):
                appt = call_context.get('appointment')
                call_context_str += f"APPOINTMENT: {appt.get('title')} on {appt.get('appointment_date')}\n"

        # 6. Final Assemble
        full_prompt = f"{VoicePromptBuilder.ACKNOWLEDGEMENT_RULES}\n\n{gatekeeper}\n\n"
        full_prompt += f"YOUR REFERENCE TIME: {current_datetime_str}\n\n"
        full_prompt += f"{location_context}{call_context_str}\n{tool_instr}\n"
        
        full_prompt += "### USER-SPECIFIED PERSONA & RULES ###\n"
        if personality_prompt:
            full_prompt += f"{personality_prompt}\n\n"
        full_prompt += f"SOUL:\n{settings.get('soul', '')}\n\n"
        full_prompt += f"INSTRUCTIONS:\n{settings.get('prompt_template', 'Follow behavioral guidelines.')}\n\n"

        if enabled_skills:
            skill_info = "### ENRICHED CAPABILITIES (SKILLS) ###\n"
            for skill in enabled_skills:
                skill_info += f"#### {skill.name}\n{skill.instructions}\n\n"
            full_prompt += skill_info

        # Identity
        full_prompt += f"\n---\nIDENTITY INFO:\n- Agent Name: {workspace_info.get('role', 'SupaAgent')}\n- Brand: {workspace_info.get('name')}\n- Reference Phone: {workspace_info.get('phone')}\n"
        
        return full_prompt
