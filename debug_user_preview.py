
import os
import stripe
from dotenv import load_dotenv
import time

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# User Details from previous logs
CUSTOMER = "cus_TkUFTIyhr8uZiG" 
SUB = "sub_1SmzHA6Rc2ce57mvhqzsK4Wd"

# Target Prices
STARTER = "price_1SZbis6Rc2ce57mvRsWtgE4S" # Current legacy starter?
PRO = "price_1SpuwS6Rc2ce57mvuoenTeSt" # New Pro
PRO_PLUS = "price_1Spv0g6Rc2ce57mvskyImgME" # New Pro+

def inspect_sub():
    print(f"--- Inspecting Subscription {SUB} ---")
    sub = stripe.Subscription.retrieve(SUB)
    print(f"Status: {sub.status}")
    print(f"Current Period End: {sub.get('current_period_end')}")
    print("Items:")
    for item in sub['items']['data']:
        print(f" - Item ID: {item.id}")
        print(f"   Price ID: {item.price.id}")
        print(f"   Product: {item.price.product}")
        print(f"   Qty: {item.quantity}")
    return sub['items']['data'][0].id

def preview_update(sub_item_id, new_price_id, label):
    print(f"\n--- Preview Switch to {label} ({new_price_id}) ---")
    proration_date = int(time.time())
    
    try:
        preview = stripe.Invoice.create_preview(
            customer=CUSTOMER,
            subscription=SUB,
            subscription_details={
                "items": [{
                    "id": sub_item_id,
                    "price": new_price_id,
                }],
                "proration_date": proration_date,
            }
        )
        print(f"Total Amount Due: {preview.amount_due / 100} {preview.currency}")
        print("Lines:")
        for line in preview.lines.data:
            desc = line.description or "No desc"
            amt = line.amount / 100
            period = f"{line.period.start} to {line.period.end}"
            print(f" - {desc:<50} | {amt:>8} | Period: {period}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    item_id = inspect_sub()
    # Test Upgrade to Pro+ (High discrepancy seen: $624 instead of $349)
    preview_update(item_id, PRO_PLUS, "Pro+")
    # Test Upgrade to Starter (Should be 0 if current)
    # Note: Using the ID from verify plans (price_1SffxH...) which might differ from current
    # preview_update(item_id, "price_1SffxH6Rc2ce57mvgxJPdVEx", "Starter (New ID)")
