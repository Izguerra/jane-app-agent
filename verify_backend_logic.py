
import os
import stripe
import time
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Mock Request Data
CUSTOMER = "cus_TkUFTIyhr8uZiG" 
SUB = "sub_1SmzHA6Rc2ce57mvhqzsK4Wd"
NEW_PRICE = "price_1SpuwS6Rc2ce57mvuoenTeSt" # Pro

def get_val(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def test_logic():
    print("Fetching Sub...")
    sub = stripe.Subscription.retrieve(SUB)
    current_item = sub['items']['data'][0]
    
    items = [{
        'id': current_item.id,
        'price': NEW_PRICE, 
    }]
    
    proration_date = int(time.time())
    
    print("Calling create_preview...")
    invoice = stripe.Invoice.create_preview(
        customer=CUSTOMER,
        subscription=SUB,
        subscription_details={
            "items": items,
            "proration_date": proration_date,
        }
    )
    
    # Logic from backend
    lines_data = get_val(get_val(invoice, "lines"), "data", [])
    print(f"Lines Data Type: {type(lines_data)}")
    print(f"Num Lines: {len(lines_data)}")
    
    for i, line in enumerate(lines_data):
        desc = get_val(line, "description")
        amt = get_val(line, "amount", 0)
        is_proration = get_val(line, "proration")
        print(f"Line {i}: {desc} | Amt: {amt} | Proration: {is_proration}")
        if i == 0:
            print("Line 0 details:")
            try:
                print(line)
            except:
                pass
            print(dir(line))

    proration_amount = sum(
        get_val(line, "amount", 0) 
        for line in lines_data 
        if get_val(line, "proration")
    )
    
    print(f"\nCalculated Proration Amount: {proration_amount}")

if __name__ == "__main__":
    test_logic()
