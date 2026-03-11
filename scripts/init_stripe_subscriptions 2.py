"""
Script to initialize Stripe subscriptions for existing customers.
This adds the necessary Stripe columns and creates subscriptions for customers who have plans but no Stripe subscription.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models_db import Customer
from backend.services.stripe_service import StripeService

# Database setup - use same database as backend
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL or POSTGRES_URL must be set in .env file")

# Handle postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Using database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}\n")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def add_stripe_columns():
    """Add Stripe-related columns to customers table if they don't exist."""
    print("Adding Stripe columns to customers table...")
    
    with engine.connect() as conn:
        # Check if columns exist using PostgreSQL information_schema
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customers'
        """))
        columns = [row[0] for row in result]
        
        columns_to_add = {
            'plan': 'VARCHAR(50) DEFAULT \'Starter\'',
            'usage_limit': 'INTEGER DEFAULT 1000',
            'usage_used': 'INTEGER DEFAULT 0',
            'status': 'VARCHAR(20) DEFAULT \'active\'',
            'avatar_url': 'VARCHAR(255)',
            'is_deleted': 'BOOLEAN DEFAULT false',
            'stripe_customer_id': 'VARCHAR(255)',
            'stripe_subscription_id': 'VARCHAR(255)',
            'stripe_payment_method_id': 'VARCHAR(255)',
            'subscription_status': 'VARCHAR(50)',
            'current_period_end': 'TIMESTAMP',
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"  ✓ Added column: {col_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"  ⚠ Column {col_name} already exists")
                    else:
                        print(f"  ✗ Error adding {col_name}: {e}")
        
        # Add indexes
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_stripe_customer_id ON customers (stripe_customer_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_stripe_subscription_id ON customers (stripe_subscription_id)"))
            conn.commit()
            print("  ✓ Added indexes")
        except Exception as e:
            print(f"  ⚠ Index creation: {e}")

def initialize_stripe_subscriptions():
    """Create Stripe subscriptions for existing customers."""
    print("\nInitializing Stripe subscriptions for existing customers...")
    
    db = SessionLocal()
    try:
        stripe_service = StripeService(db)
        
        # Use raw SQL to get customers without Stripe subscriptions
        result = db.execute(text("""
            SELECT id, first_name, last_name, email, plan
            FROM customers 
            WHERE (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
            AND (is_deleted = false OR is_deleted IS NULL)
        """))
        
        customers = result.fetchall()
        
        print(f"Found {len(customers)} customers without Stripe subscriptions\n")
        
        for row in customers:
            customer_id, first_name, last_name, email, plan = row
            try:
                print(f"Processing: {first_name} {last_name} ({email})")
                print(f"  Current plan: {plan or 'Starter'}")
                
                # Create or get Stripe customer
                stripe_customer_id = stripe_service.create_or_get_customer(customer_id)
                print(f"  ✓ Stripe customer ID: {stripe_customer_id}")
                
                # Create subscription for their current plan
                plan_name = plan or "Starter"
                subscription = stripe_service.create_subscription(customer_id, plan_name)
                print(f"  ✓ Created subscription: {subscription.id}")
                print(f"  ✓ Status: {subscription.status}\n")
                
            except Exception as e:
                print(f"  ✗ Error for {email}: {str(e)}\n")
                continue
        
        print("✓ Stripe subscription initialization complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Stripe Subscription Initialization Script")
    print("=" * 60)
    print()
    
    # Step 1: Add columns
    add_stripe_columns()
    
    # Step 2: Initialize subscriptions
    initialize_stripe_subscriptions()
    
    print("\n" + "=" * 60)
    print("Script completed successfully!")
    print("=" * 60)
