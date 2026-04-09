from datetime import datetime, timezone

ACKNOWLEDGEMENT_RULES = """CRITICAL CONVERSATIONAL RULES (STRICTLY ENFORCE):

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

TOOL_USAGE_INSTRUCTIONS = """
TOOL USAGE & PERMISSIONS:
1. You have access to specialized tools (Skills & Workers). USE THEM to answer user questions — DO NOT guess or make up answers.
2. For weather questions, use `get_current_weather`. For directions/distance, use `get_directions`. For flights, use `get_flight_status`.
3. For general knowledge or real-time info, use `web_search`.
4. For SMS, use `send_sms_notification`. For email, use `send_email_notification`.
5. If a tool returns 'Error: Tool not enabled', explain politely to the user that this feature is currently disabled.
6. For almost ALL requests (searching, email, CRM, weather), use `run_task_now` for immediate results.
7. ONLY use `dispatch_worker_task` for long-running background jobs.
8. ALWAYS check for required parameters (location, email, dates) before calling a tool. If missing, ASK the user.
9. NEVER answer a factual question (weather, time, flights, directions) from memory alone — ALWAYS use the appropriate tool.
"""

WORKER_DESCRIPTIONS = {
    "sms-messaging": "Send SMS (REQUIRES: 'recipient_number', 'message')",
    "sales-outreach": "Sales Outreach (REQUIRES: 'target_role', 'company_list')",
    "faq-resolution": "Answer Customer FAQs",
    "content-writer": "Generate Content (Optional: topic, content_type)",
    "job-search": "Find Jobs (REQUIRES: 'job_title', 'level', 'job_type', 'location_type')",
    "email-worker": "Manage Email (Send REQUIRES: 'recipient', 'subject', 'body')",
    "flight-tracker": "Check Flight Status/Schedule (REQUIRES: 'flight_number' OR 'origin'+'destination')",
    "map-worker": "Navigation (REQUIRES: 'origin', 'destination', 'mode')",
    "weather-worker": "Check Weather (REQUIRES: 'location'. Optional: 'date', 'units')",
    "hr-onboarding": "HR Onboarding (REQUIRES: 'candidate_name')",
    "payment-billing": "Check Payments (REQUIRES: 'action', 'transaction_id' OR 'email')",
    "web-research": "Search the web for real-time information",
}


def get_avatar_prompt(settings: dict, enabled_skills: list = [], personality_prompt: str = None) -> str:
    base_prompt = settings.get("prompt_template", "You are a helpful AI assistant.")
    
    if personality_prompt:
        base_prompt = f"{personality_prompt}\n\n{base_prompt}"

    # Add current datetime for relative date interpretation
    now_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
    
    prompt = f"{ACKNOWLEDGEMENT_RULES}\n\nCURRENT DATE AND TIME: {now_str}. Use this to interpret relative dates.\n\n"
    prompt += f"Running Mode: AVATAR CONVERSATION.\n{TOOL_USAGE_INSTRUCTIONS}\n\n"
    prompt += f"CUSTOMER INSTRUCTIONS:\n{base_prompt}"

    if enabled_skills:
        skill_info = "\n\nENRICHED SKILLS & CAPABILITIES:\n"
        skill_info += "You have been equipped with the following specialized skills. Follow their specific instructions strictly:\n\n"
        for skill in enabled_skills:
            skill_info += f"### {skill.name} ({skill.slug})\n{skill.instructions}\n\n"
        prompt += skill_info

    # Add worker context
    allowed_workers = settings.get("allowed_worker_types", [])
    if enabled_skills:
        allowed_workers = list(set(allowed_workers + [s.slug for s in enabled_skills]))
    
    if allowed_workers:
        allowed_list = "\n".join([f"- {w}: {WORKER_DESCRIPTIONS.get(w, w)}" for w in allowed_workers])
        prompt += f"\n\nAVAILABLE WORKERS:\n{allowed_list}"

    return prompt

