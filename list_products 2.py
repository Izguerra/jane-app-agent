
import os
from dotenv import load_dotenv
import stripe

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def list_products():
    print("Listing Active Products...")
    try:
        products = stripe.Product.list(limit=20, active=True)
        for p in products.data:
            print(f"Product: {p.name} ({p.id})")
            prices = stripe.Price.list(product=p.id, limit=3)
            for price in prices.data:
                print(f"  - Price: {price.id} | {price.unit_amount/100 if price.unit_amount else 0} {price.currency} | {price.type} | {price.recurring if price.recurring else ''}")
            print("-" * 30)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    list_products()
