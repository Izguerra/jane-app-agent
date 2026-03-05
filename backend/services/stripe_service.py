import stripe
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models_db import Customer

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Plan price IDs from environment
PLAN_PRICES = {
    "Starter": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
    "Professional": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID", "price_professional"),
    "Enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise"),
}

PLAN_AMOUNTS = {
    "Starter": 2900,  # $29.00 in cents
    "Professional": 9900,  # $99.00 in cents
    "Enterprise": 29900,  # $299.00 in cents
}

class StripeService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_get_customer(self, customer_id: str) -> str:
        """Create or retrieve Stripe customer for a database customer."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        # Return existing Stripe customer if already created
        if customer.stripe_customer_id:
            return customer.stripe_customer_id

        # Create new Stripe customer
        stripe_customer = stripe.Customer.create(
            email=customer.email,
            name=f"{customer.first_name} {customer.last_name}",
            metadata={"customer_id": customer_id}
        )

        # Save Stripe customer ID
        customer.stripe_customer_id = stripe_customer.id
        self.db.commit()

        return stripe_customer.id

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> Dict[str, Any]:
        """Attach a payment method to a customer and set as default."""
        stripe_customer_id = self.create_or_get_customer(customer_id)

        # Attach payment method to customer
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=stripe_customer_id,
        )

        # Set as default payment method
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
        )

        # Update database
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        customer.stripe_payment_method_id = payment_method_id
        self.db.commit()

        return payment_method

    def create_subscription(self, customer_id: str, plan: str) -> Dict[str, Any]:
        """Create a new subscription for a customer."""
        stripe_customer_id = self.create_or_get_customer(customer_id)
        price_id = PLAN_PRICES.get(plan)

        if not price_id:
            raise ValueError(f"Invalid plan: {plan}")

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )

        # Update database
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        customer.stripe_subscription_id = subscription.id
        customer.subscription_status = subscription.status
        customer.plan = plan
        
        # Only set current_period_end if subscription is active (has this field)
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            customer.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        
        self.db.commit()

        return subscription

    def update_subscription(self, customer_id: str, new_plan: str) -> Dict[str, Any]:
        """Update subscription to a new plan with proration."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.stripe_subscription_id:
            raise ValueError("No active subscription found")

        new_price_id = PLAN_PRICES.get(new_plan)
        if not new_price_id:
            raise ValueError(f"Invalid plan: {new_plan}")

        # Get current subscription
        subscription = stripe.Subscription.retrieve(customer.stripe_subscription_id)

        # Update subscription with proration
        updated_subscription = stripe.Subscription.modify(
            customer.stripe_subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id,
            }],
            proration_behavior="create_prorations",  # Charge immediately for upgrades
        )

        # Update database
        customer.plan = new_plan
        customer.subscription_status = updated_subscription.status
        customer.current_period_end = datetime.fromtimestamp(updated_subscription.current_period_end)
        self.db.commit()

        return updated_subscription

    def calculate_proration(self, customer_id: str, new_plan: str) -> Dict[str, Any]:
        """Calculate proration amount for plan change."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.stripe_subscription_id:
            return {"amount": 0, "description": "No active subscription"}

        # Get current subscription
        subscription = stripe.Subscription.retrieve(customer.stripe_subscription_id)
        
        # Calculate proration preview
        current_period_end = subscription.current_period_end
        now = int(datetime.now().timestamp())
        days_remaining = (current_period_end - now) / 86400  # seconds to days

        old_amount = PLAN_AMOUNTS.get(customer.plan, 0)
        new_amount = PLAN_AMOUNTS.get(new_plan, 0)

        # Calculate prorated amounts
        old_daily = old_amount / 30
        new_daily = new_amount / 30

        unused_credit = old_daily * days_remaining
        new_prorated = new_daily * days_remaining

        amount_due = new_prorated - unused_credit

        return {
            "amount": int(amount_due),  # in cents
            "amount_formatted": f"${amount_due / 100:.2f}",
            "days_remaining": int(days_remaining),
            "old_plan": customer.plan,
            "new_plan": new_plan,
            "description": f"Upgrade from {customer.plan} to {new_plan}",
        }

    def get_payment_methods(self, customer_id: str) -> list:
        """Get all payment methods for a customer."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.stripe_customer_id:
            return []

        payment_methods = stripe.PaymentMethod.list(
            customer=customer.stripe_customer_id,
            type="card",
        )

        return payment_methods.data

    def create_setup_intent(self, customer_id: str) -> Dict[str, Any]:
        """Create a SetupIntent for adding payment method."""
        stripe_customer_id = self.create_or_get_customer(customer_id)

        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
        )

        return setup_intent

    def cancel_subscription(self, customer_id: str) -> Dict[str, Any]:
        """Cancel a customer's subscription."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.stripe_subscription_id:
            raise ValueError("No active subscription found")

        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            customer.stripe_subscription_id,
            cancel_at_period_end=True,
        )

        # Update database
        customer.subscription_status = "canceling"
        self.db.commit()

        return subscription

    def get_invoices(self, customer_id: str, limit: int = 10) -> list:
        """Get customer invoices."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.stripe_customer_id:
            return []

        invoices = stripe.Invoice.list(
            customer=customer.stripe_customer_id,
            limit=limit,
        )

        return invoices.data
