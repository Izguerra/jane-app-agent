
import os
from dotenv import load_dotenv
import stripe
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DATABASE_URL = os.getenv("POSTGRES_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print(f"Stripe Version: {stripe.version.VERSION}")
# print(dir(stripe.Invoice))

def debug_proration():
    # Get a team with a sub
    result = db.execute(text("SELECT id, stripe_customer_id, stripe_subscription_id FROM teams WHERE stripe_subscription_id IS NOT NULL LIMIT 1"))
    team = result.fetchone()
    
    if not team:
        print("No team with subscription found.")
        return

    print(f"Team: {team.id}, Cust: {team.stripe_customer_id}, Sub: {team.stripe_subscription_id}")
    
    sub = stripe.Subscription.retrieve(team.stripe_subscription_id)
    print(f"Current Sub Status: {sub.status}")
    print(f"Current Price: {sub['items']['data'][0]['price']['id']}")

    # Target: Pro Plan
    TARGET_PRICE = "price_1SffxI6Rc2ce57mvEH53oKnE" 
    
    try:
        current_item_id = sub['items']['data'][0].id
        items = [{
            'id': current_item_id,
            'price': TARGET_PRICE,
        }]

        import time
        proration_date = int(time.time())

        invoice = stripe.Invoice.upcoming(
            customer=team.stripe_customer_id,
            subscription=team.stripe_subscription_id,
            subscription_items=items,
            subscription_proration_date=proration_date,
        )
        
        print("\n--- UPCOMING INVOICE ---")
        print(f"Amount Due: {invoice.amount_due}")
        print(f"Total: {invoice.total}")
        print("Lines:")
        for line in invoice.lines.data:
            print(f" - {line.description}: Amount: {line.amount} (Prd: {line.period.start} to {line.period.end})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_proration()
