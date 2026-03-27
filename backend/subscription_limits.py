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

