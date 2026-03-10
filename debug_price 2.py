
import os
from dotenv import load_dotenv
import stripe

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_ID = "price_1SZbis6Rc2ce57mvRsWtgE4S" # The one found in DB

try:
    price = stripe.Price.retrieve(PRICE_ID)
    print(f"Price ID: {price.id}")
    print(f"Unit Amount: {price.unit_amount}")
    print(f"Currency: {price.currency}")
    print(f"Product: {price.product}")
    
    prod = stripe.Product.retrieve(price.product)
    print(f"Product Name: {prod.name}")

except Exception as e:
    print(e)
