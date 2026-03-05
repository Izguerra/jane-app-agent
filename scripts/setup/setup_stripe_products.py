import stripe
import os
import logging
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import stripe
import os
import logging
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hybrid Pricing Configuration
PLANS = {
    "pro": {
        "name": "Pro Plan",
        "amount": 12900, # $129
        "features": {
            "voice_monitor": {"amount": 22, "nickname": "Voice Usage ($0.22/min)", "meter_event": "voice_minutes"},
            "chat_monitor": {"amount": 6, "nickname": "Chat Usage ($0.06/msg)", "meter_event": "chat_messages"}
        }
    },
    "pro_plus": {
        "name": "Pro+ Plan",
        "amount": 34900, # $349
        "features": {
            "voice_monitor_plus": {"amount": 15, "nickname": "Voice Usage ($0.15/min)", "meter_event": "voice_minutes"},
            "chat_monitor_plus": {"amount": 4, "nickname": "Chat Usage ($0.04/msg)", "meter_event": "chat_messages"},
            "outcome_fee": {"amount": 250, "nickname": "Outcome Fee ($2.50/booking)", "meter_event": "outcomes"}
        }
    },
    "pro_max": {
        "name": "ProMax Plan",
        "amount": 89900, # $899
        "features": {
            "voice_monitor_max": {"amount": 9, "nickname": "Voice Usage ($0.09/min)", "meter_event": "voice_minutes"},
            "chat_monitor_max": {"amount": 2, "nickname": "Chat Usage ($0.02/msg)", "meter_event": "chat_messages"},
            "outcome_fee_max": {"amount": 150, "nickname": "Outcome Fee ($1.50/booking)", "meter_event": "outcomes"}
        }
    }
}

METERS = {
    "voice_minutes": "usage_voice_minutes",
    "chat_messages": "usage_chat_messages",
    "outcomes": "usage_outcomes"
}

def get_or_create_meter(event_name, display_name):
    # List meters to see if exists
    try:
        meters = stripe.billing.Meter.list(limit=100)
        for m in meters.data:
            if m.event_name == event_name:
                logger.info(f"Meter found: {display_name} ({m.id})")
                return m.id
        
        # Create if not exists
        meter = stripe.billing.Meter.create(
            display_name=display_name,
            event_name=event_name,
            default_aggregation={"formula": "sum"},
        )
        logger.info(f"Meter created: {display_name} ({meter.id})")
        return meter.id
    except Exception as e:
        logger.error(f"Error getting/creating meter {event_name}: {e}")
        return None

def get_or_create_product(name):
    products = stripe.Product.search(query=f"name:'{name}'", limit=1)
    if products.data:
        logger.info(f"Product found: {name} ({products.data[0].id})")
        return products.data[0]
    else:
        p = stripe.Product.create(name=name)
        logger.info(f"Product created: {name} ({p.id})")
        return p

def get_or_create_price(product_id, amount, interval="month", usage_type="licensed", nickname=None, meter_id=None):
    # This checks for exact match might be tricky, simplified to just creating if needed
    # For now, we'll list prices and see if one matches the amount/type
    prices = stripe.Price.list(product=product_id, limit=10, active=True)
    for p in prices.data:
        if p.unit_amount == amount and p.recurring.usage_type == usage_type:
            if interval and p.recurring.interval != interval:
                continue
            # If metered, strictly checking meter_id usually requires retrieving specific config, 
            # but for simplicity we rely on amount/usage_type match for existing prices.
            logger.info(f"  - Use existing price: {p.id} ({nickname})")
            return p
            
    # Create new
    recurring = {"interval": interval}
    if usage_type == "metered":
        recurring["usage_type"] = "metered"
        # aggregate_usage is defined on the Meter, not the Price for newer API versions
        if meter_id:
            recurring["meter"] = meter_id

    price = stripe.Price.create(
        product=product_id,
        unit_amount=amount,
        currency="usd",
        recurring=recurring,
        nickname=nickname
    )
    logger.info(f"  - Created new price: {price.id} ({nickname})")
    return price

def setup_products():
    if not stripe.api_key:
        logger.error("STRIPE_SECRET_KEY not set")
        return

    print("\n--- Stripe Configuration Output ---")
    
    # Setup Meters first
    meter_ids = {}
    print("\nConfiguring Meters...")
    for event, display in METERS.items():
        m_id = get_or_create_meter(event, display)
        if m_id:
            meter_ids[event] = m_id
    
    for key, config in PLANS.items():
        print(f"\nProcessing {config['name']}...")
        product = get_or_create_product(config["name"])
        
        # Base Subscription Price
        base_price = get_or_create_price(product.id, config["amount"], nickname=f"{config['name']} Base")
        print(f"STRIPE_PRICE_{key.upper()}_BASE={base_price.id}")
        
        # Metered Usage Prices
        for feature_key, feature in config["features"].items():
            meter_id = meter_ids.get(feature.get("meter_event")) if feature.get("meter_event") else None
            
            metered_price = get_or_create_price(
                product.id, 
                feature["amount"], 
                usage_type="metered", 
                nickname=feature["nickname"],
                meter_id=meter_id
            )
            print(f"STRIPE_PRICE_{key.upper()}_{feature_key.upper()}={metered_price.id}")

    # Additional Number (Legacy/Global)
    print("\nProcessing Add-ons...")
    phone_product = get_or_create_product("Additional Phone Number")
    phone_price = get_or_create_price(phone_product.id, 500, nickname="Additional Number ($5/mo)")
    print(f"STRIPE_PRICE_ADDITIONAL_NUMBER={phone_price.id}")

if __name__ == "__main__":
    setup_products()
