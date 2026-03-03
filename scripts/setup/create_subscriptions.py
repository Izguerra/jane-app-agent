"""
Quick script to create Stripe subscriptions for customers who have Stripe customer IDs but no subscriptions.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.services.stripe_service import StripeService

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()
try:
    stripe_service = StripeService(db)
    
    # Get customers with Stripe customer IDs but no subscriptions
    result = db.execute(text("""
        SELECT id, first_name, last_name, email, plan, stripe_customer_id
        FROM customers 
        WHERE stripe_customer_id IS NOT NULL 
        AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
        AND (is_deleted = false OR is_deleted IS NULL)
    """))
    
    customers = result.fetchall()
    print(f"Found {len(customers)} customers needing subscriptions\n")
    
    for row in customers:
        customer_id, first_name, last_name, email, plan, stripe_cust_id = row
        try:
            print(f"Creating subscription for: {first_name} {last_name}")
            print(f"  Email: {email}")
            print(f"  Plan: {plan}")
            print(f"  Stripe Customer ID: {stripe_cust_id}")
            
            subscription = stripe_service.create_subscription(customer_id, plan)
            print(f"  ✓ Subscription created: {subscription['id']}")
            print(f"  ✓ Status: {subscription['status']}\n")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            continue
    
    print("Done!")
    
finally:
    db.close()
