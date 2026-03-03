import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def list_products():
    try:
        products = stripe.Product.list(limit=20, active=True)
        for p in products.data:
            print(f"Product: {p.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_products()
