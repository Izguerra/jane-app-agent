import stripe
import os
import sys

# Load env vars if managing manually or assume they are set
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def setup_avatar_products():
    api_key = os.getenv("STRIPE_SECRET_KEY")
    if not api_key:
        print("Error: STRIPE_SECRET_KEY environment variable not set.")
        return

    stripe.api_key = api_key
    
    product_name = "AI Avatar Usage"
    
    print(f"Checking for existing product: {product_name}...")
    
    # Check if product exists
    existing = stripe.Product.search(query=f"name:'{product_name}'", limit=1)
    
    if existing.data:
        product = existing.data[0]
        print(f"Found existing Product: {product.id}")
    else:
        print("Creating new Product...")
        product = stripe.Product.create(
            name=product_name,
            description="Per-minute billing for AI Avatar Usage (Tavus/LiveKit)",
            unit_label="minute"
        )
        print(f"Created Product: {product.id}")

    # --- Create Price 1: Pro+ (Flat $0.45) ---
    print("\nSetting up Pro+ Price ($0.45/min)...")
    # We ideally want a lookup key or metadata to avoid dupes, but for now we create
    try:
        price_pro_plus = stripe.Price.create(
            nickname="Avatar Usage (Pro+)",
            product=product.id,
            unit_amount=45, # $0.45
            currency="usd",
            recurring={
                "interval": "month",
                "usage_type": "metered",
                "aggregate_usage": "sum"
            },
            metadata={"tier": "pro_plus"}
        )
        print(f"Created Pro+ Price ID: {price_pro_plus.id}")
    except Exception as e:
        print(f"Error creating Pro+ price: {e}")

    # --- Create Price 2: ProMax (Tiered: 60 free, then $0.40) ---
    print("\nSetting up ProMax Price (60 free, then $0.40/min)...")
    try:
        price_pro_max = stripe.Price.create(
            nickname="Avatar Usage (ProMax)",
            product=product.id,
            currency="usd",
            recurring={
                "interval": "month",
                "usage_type": "metered",
                "aggregate_usage": "sum"
            },
            billing_scheme="tiered",
            tiers_mode="graduated",
            tiers=[
                {
                    "up_to": 60,
                    "unit_amount": 0 # First 60 free
                },
                {
                    "up_to": "inf",
                    "unit_amount": 40 # $0.40 after
                }
            ],
            metadata={"tier": "pro_max"}
        )
        print(f"Created ProMax Price ID: {price_pro_max.id}")
    except Exception as e:
        print(f"Error creating ProMax price: {e}")

    print("\n--- DONE ---")
    print("Add these to your .env file:")
    print("# from script output")

if __name__ == "__main__":
    setup_avatar_products()
