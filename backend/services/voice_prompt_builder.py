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

"""

    @staticmethod
    def build_prompt(settings, personality_prompt, enabled_skills, workspace_info, current_datetime_str, client_location, agent_type="business", call_context=None):
        # 1. Choose Gatekeeper Template
        is_personal = agent_type == "personal" or settings.get("agent_type") == "personal"
        base_template = PERSONAL_GATEKEEPER_INSTRUCTION if is_personal else BUSINESS_GATEKEEPER_INSTRUCTION
        
        # 2. Build Tool List
        allowed_workers = settings.get("allowed_worker_types", [])
        if enabled_skills:
            allowed_workers = list(set(allowed_workers + [s.slug for s in enabled_skills]))
        
        # Ensure standard communication workers are listed
        for core_worker in ["sms-messaging", "email-worker"]:
            if core_worker not in allowed_workers:
                allowed_workers.append(core_worker)
        
        allowed_list_str = "\n".join([f"- {w}: {VoicePromptBuilder.WORKER_DESCRIPTIONS.get(w, w)}" for w in allowed_workers]) or "- None"

        # 3. Format Template Safely (In Isolation)
        try:
            gatekeeper = base_template.format(
                business_name=workspace_info.get("name", "The User" if is_personal else "The Business"),
                services=workspace_info.get("services", "General Assistance" if is_personal else "Appointments, General Inquiries"),
                role=workspace_info.get("role", "Personal Assistant" if is_personal else "AI Assistant"),
                allowed_worker_list=allowed_list_str
            )
        except Exception as e:
            logger.warning(f"Template formatting failed: {e}")
            gatekeeper = base_template # Fallback to raw if formatting blows up

        # 4. Assemble Final Prompt
        tool_usage = (
            "\n\nTOOL USAGE & PERMISSIONS:\n"
            "1. You have access to specialized tools. Use `get_weather`, `web_search`, `get_directions`, and `get_flight_status` directly when applicable.\n"
            "2. Use `run_task_now` for all other specialized skills.\n"
            "3. ALWAYS acknowledge the user BEFORE calling a tool."
        )

        location_context = f"CURRENT ENVIRONMENT CONTEXT:\\n- User's Timezone: {settings.get('client_timezone', 'America/Toronto')}\\n- User's Estimated Location: {client_location}\\n" if client_location else ""
        
        call_context_str = ""
        if call_context:
            call_context_str = "\n\n### MISSION-CRITICAL CALL CONTEXT ###\n"
            call_context_str += f"REASON FOR CALL: {call_context.get('intent', 'General')}\n"
            if call_context.get('customer'):
                cust = call_context.get('customer')
                call_context_str += f"CUSTOMER: {cust.get('full_name')} ({cust.get('email')}, {cust.get('phone')})\n"
            if call_context.get('appointment'):
                appt = call_context.get('appointment')
                call_context_str += f"APPOINTMENT: {appt.get('title')} on {appt.get('appointment_date')}\n"
            if call_context.get('deal'):
                deal = call_context.get('deal')
                call_context_str += f"DEAL: {deal.get('title')} (Stage: {deal.get('stage')}, Value: {deal.get('value')})\n"

        full_prompt = f"{VoicePromptBuilder.ACKNOWLEDGEMENT_RULES}\n{gatekeeper}\n\n"
        full_prompt += f"CURRENT DATE AND TIME: {current_datetime_str}.\n\n"
        full_prompt += f"{location_context}{call_context_str}\nRunning Mode: VOICE CONVERSATION.{tool_usage}\n\n"
        
        # Add User Instructions (Personality & Template) - Concatenate rather than format!
        full_prompt += "USER-SPECIFIED INSTRUCTIONS & PERSONA:\n"
        if personality_prompt:
            full_prompt += f"{personality_prompt}\n\n"
        
        full_prompt += f"{settings.get('prompt_template', 'Follow the guidelines above.')}\n\n"

        # 5. Add Enriched Skill Data
        if enabled_skills:
            skill_info = "\n\nENRICHED SKILLS:\n"
            for skill in enabled_skills:
                skill_info += f"### {skill.name} ({skill.slug})\n{skill.instructions}\n\n"
            full_prompt += skill_info

        # 6. Language requirements
        lang = settings.get("language", "en")
        lang_name = VoicePromptBuilder.LANGUAGE_NAMES.get(lang, lang)
        if lang != "en":
            full_prompt += f"\n\nCRITICAL LANGUAGE REQUIREMENT: Speak ONLY in {lang_name}."

        full_prompt += f"\n\nIDENTITY INFO:\nRepresenting: {workspace_info.get('name')}\nPhone: {workspace_info.get('phone')}\n"
        
        return full_prompt
