# Configuration for subscription plans and limits

PLAN_LIMITS = {
    "Starter": {
        "conversations": 1000,
        "voice_minutes": 100,
        "chatbots": 1,
        "storage_mb": 10,
        "analytics": "basic"
    },
    "Professional": {
        "conversations": 10000,
        "voice_minutes": 1000,
        "chatbots": 3,
        "storage_mb": 100,
        "analytics": "advanced"
    },
    "Pro": {
        "conversations": 10000,
        "voice_minutes": 1000,
        "chatbots": 3,
        "storage_mb": 100,
        "analytics": "advanced"
    },
    "Pro Plan": {
        "conversations": 10000,
        "voice_minutes": 1000,
        "chatbots": 3,
        "storage_mb": 100,
        "analytics": "advanced"
    },
    "Pro+": {
        "conversations": 25000,
        "voice_minutes": 2500,
        "chatbots": 5,
        "storage_mb": 250,
        "analytics": "advanced"
    },
    "Pro+ Plan": {
        "conversations": 25000,
        "voice_minutes": 2500,
        "chatbots": 5,
        "storage_mb": 250,
        "analytics": "advanced"
    },
    "ProMax": {
        "conversations": 50000,
        "voice_minutes": 5000,
        "chatbots": 10,
        "storage_mb": 500,
        "analytics": "advanced"
    },
    "ProMax Plan": {
        "conversations": 50000,
        "voice_minutes": 5000,
        "chatbots": 10,
        "storage_mb": 500,
        "analytics": "advanced"
    },
    "Enterprise": {
        "conversations": float('inf'),
        "voice_minutes": float('inf'),
        "chatbots": 20,
        "storage_mb": float('inf'),
        "analytics": "custom"
    }
}

DEFAULT_PLAN = "Starter" # Default plan for new teams or those without a subscription

def get_plan_limits(plan_name):
    """Returns the limits for a given plan name."""
    if not plan_name or plan_name not in PLAN_LIMITS:
        return PLAN_LIMITS[DEFAULT_PLAN]
    return PLAN_LIMITS[plan_name]

def check_limit(current_usage, limit):
    """Returns True if usage is within limit, False otherwise."""
    return current_usage < limit


# Integration Registry: all known integration providers and their metadata
INTEGRATION_REGISTRY = {
    "openai": {"display_name": "OpenAI", "category": "ai"},
    "google_gemini": {"display_name": "Google Gemini", "category": "ai"},
    "mistral": {"display_name": "Mistral AI", "category": "ai"},
    "anthropic": {"display_name": "Anthropic", "category": "ai"},
    "openrouter": {"display_name": "OpenRouter", "category": "ai"},
    "deepseek": {"display_name": "DeepSeek", "category": "ai"},
    "tavily": {"display_name": "Tavily Search", "category": "search"},
    "twilio": {"display_name": "Twilio", "category": "phone"},
    "phone": {"display_name": "Phone", "category": "phone"},
    "google_calendar": {"display_name": "Google Calendar", "category": "calendar"},
    "exchange": {"display_name": "Microsoft Exchange", "category": "calendar"},
    "tavus": {"display_name": "Tavus Avatar", "category": "avatar"},
    "anam": {"display_name": "Anam Avatar", "category": "avatar"},
    "stripe": {"display_name": "Stripe", "category": "payment"},
    "zapier": {"display_name": "Zapier", "category": "automation"},
    "slack": {"display_name": "Slack", "category": "communication"},
    "sendgrid": {"display_name": "SendGrid", "category": "email"},
}

# Integrations available per plan tier
PLAN_INTEGRATIONS = {
    "starter": ["openai", "google_gemini", "tavily"],
    "professional": ["openai", "google_gemini", "mistral", "anthropic", "openrouter", "tavily", "twilio", "phone", "google_calendar", "tavus"],
    "pro": ["openai", "google_gemini", "mistral", "anthropic", "openrouter", "deepseek", "tavily", "twilio", "phone", "google_calendar", "tavus", "anam", "stripe"],
    "pro+": list(INTEGRATION_REGISTRY.keys()),
    "promax": list(INTEGRATION_REGISTRY.keys()),
    "enterprise": list(INTEGRATION_REGISTRY.keys()),
}

def get_available_integrations(plan_name: str) -> list:
    """Returns the list of integration providers available for a given plan."""
    tier = (plan_name or "starter").lower().replace(" plan", "").replace(" ", "")
    return PLAN_INTEGRATIONS.get(tier, PLAN_INTEGRATIONS["starter"])
