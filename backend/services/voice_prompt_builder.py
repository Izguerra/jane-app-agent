import logging
from datetime import datetime
from backend.prompts.general import GATEKEEPER_INSTRUCTION
from backend.prompts.personal_assistant import PERSONAL_ASSISTANT_INSTRUCTION

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
        "email-worker": "Manage Email (Send REQUIRES: 'recipient', 'subject', 'body'. Optional: 'cc', 'bcc', 'schedule_time')",
        "flight-tracker": "Check Flight Status/Schedule (REQUIRES: 'flight_number' OR 'origin'+'destination'. Optional: 'date', 'airline', 'approx_time')",
        "map-worker": "Navigation (REQUIRES: 'origin', 'destination', 'mode')",
        "weather-worker": "Check Weather (REQUIRES: 'location'. Optional: 'date', 'units' [C/F], 'details' [sunrise, humidity, etc.])",
        "hr-onboarding": "HR Onboarding (REQUIRES: 'candidate_name')",
        "payment-billing": "Check Payments (REQUIRES: 'action', 'transaction_id' OR 'email')",
        "web-research": "Search the web for real-time information",
    }

    @staticmethod
    def build_prompt(settings, personality_prompt, enabled_skills, workspace_info, current_datetime_str, client_location):
        # 1. Base instructions and rules
        tool_usage = (
            "\n\nTOOL USAGE & PERMISSIONS:\n"
            "1. You have access to specialized tools (Skills & Workers). However, some may be disabled based on business settings.\n"
            "2. If a tool returns 'Error: Tool not enabled', explain politely to the user that this feature is currently disabled for your agent.\n"
            "3. For almost ALL requests (searching, email, CRM, weather), use `run_task_now` for immediate results.\n"
            "4. ONLY use `dispatch_worker_task` for long-running background jobs.\n"
            "5. ALWAYS check for required parameters (location, email, dates) before calling a tool. If missing, ASK the user."
        )

        location_context = f"CURRENT ENVIRONMENT CONTEXT:\\n- User's Timezone: {settings.get('client_timezone', 'America/Toronto')}\\n- User's Estimated Location: {client_location}\\n" if client_location else ""

        # 2. Worker context string generation
        allowed_workers = settings.get("allowed_worker_types") or []
        if not isinstance(allowed_workers, list):
            allowed_workers = []
            
        if enabled_skills:
            allowed_workers = list(set(allowed_workers + [s.slug for s in enabled_skills]))
        
        allowed_list_str = "\n".join([f"- {w}: {VoicePromptBuilder.WORKER_DESCRIPTIONS.get(w, w)}" for w in allowed_workers]) or "- None"

        agent_type = settings.get("agent_type", "business")
        
        # 3. Select Base Instruction
        if agent_type == "personal":
            base_instruction = PERSONAL_ASSISTANT_INSTRUCTION.format(
                owner_name=settings.get("owner_name", "User"),
                location=settings.get("personal_location", "Not specified"),
                timezone=settings.get("personal_timezone", "Not specified"),
                favorite_foods=settings.get("favorite_foods", "Not specified"),
                favorite_restaurants=settings.get("favorite_restaurants", "Not specified"),
                favorite_music=settings.get("favorite_music", "Not specified"),
                favorite_activities=settings.get("favorite_activities", "Not specified"),
                other_interests=settings.get("other_interests", "Not specified"),
                likes=settings.get("personal_likes", "Not specified"),
                dislikes=settings.get("personal_dislikes", "Not specified"),
                allowed_worker_list=allowed_list_str
            )
        else:
            p_business_name = settings.get("business_name", workspace_info.get("name", "The Business"))
            p_services = settings.get("services", workspace_info.get("services", "General Inquiry"))
            p_role = settings.get("name", workspace_info.get("role", "AI Assistant"))
            
            base_instruction = GATEKEEPER_INSTRUCTION.format(
                business_name=p_business_name,
                services=p_services,
                role=p_role,
                allowed_worker_list=allowed_list_str
            )

        prompt = f"{base_instruction}\n\n"
        prompt += f"CURRENT DATE AND TIME: {current_datetime_str}. Use this to interpret relative dates.\n\n"
        prompt += f"{location_context}Running Mode: VOICE CONVERSATION.{tool_usage}\n\n"
        prompt += f"CUSTOMER INSTRUCTIONS:\n{settings.get('prompt_template', 'You are a helpful assistant.')}"

        if personality_prompt:
            prompt = f"{personality_prompt}\n\n{prompt}"

        # 4. Add Skills
        if enabled_skills:
            skill_info = "\n\nENRICHED SKILLS & CAPABILITIES:\nYou have been equipped with the following specialized skills:\n\n"
            for skill in enabled_skills:
                skill_info += f"### {skill.name} ({skill.slug})\n{skill.instructions}\n\n"
            prompt += skill_info

        # 5. Language settings
        lang = settings.get("language", "en")
        lang_name = VoicePromptBuilder.LANGUAGE_NAMES.get(lang, lang)
        if lang != "en":
            prompt += f"\n\nCRITICAL LANGUAGE REQUIREMENT:\n- You MUST speak ONLY in {lang_name}.\n- ALL responses must be in {lang_name}.\n- Do NOT respond in English."

        prompt += f"\n\nBUSINESS INFO:\nName: {workspace_info.get('name')}\nPhone: {workspace_info.get('phone')}\nIDENTITY: You represent {workspace_info.get('name')}."
        
        return prompt
