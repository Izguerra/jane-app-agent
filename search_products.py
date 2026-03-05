
import os
from dotenv import load_dotenv
import stripe

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def search_upgrades():
    print("Searching for 'Upgrade'...")
    try:
        products = stripe.Product.search(query="name~'Upgrade'", limit=10)
        for p in products.data:
            print(f"Product: {p.name} ({p.id})")
            prices = stripe.Price.list(product=p.id)
            for price in prices.data:
                print(f"  - Price: {price.id} | {price.unit_amount/100 if price.unit_amount else 0} {price.currency}")
            print("-" * 30)
            
        print("\nSearching for 'Difference'...")
        products2 = stripe.Product.search(query="name~'Difference'", limit=10)
        for p in products2.data:
            print(f"Product: {p.name} ({p.id})")
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    search_upgrades()
