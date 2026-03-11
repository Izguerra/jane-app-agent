import os
import stripe
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

logger = logging.getLogger("billing-service")

class BillingService:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if self.api_key:
            stripe.api_key = self.api_key
        else:
            logger.warning("STRIPE_SECRET_KEY not set. Billing operations will fail.")

    def get_billing_history(self, stripe_customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve billing history (invoices) for a customer.
        """
        if not self.api_key or not stripe_customer_id:
            return []

        history = []
        try:
            # Retrieve invoices
            invoices = stripe.Invoice.list(
                customer=stripe_customer_id, 
                limit=limit
            )
            
            for inv in invoices.data:
                history.append({
                    "id": inv.id,
                    "date": datetime.fromtimestamp(inv.created).strftime('%Y-%m-%d'),
                    "amount": inv.total / 100.0,
                    "status": inv.status,
                    "pdf_url": inv.invoice_pdf
                })
        except Exception as e:
            logger.error(f"Error fetching invoices for {stripe_customer_id}: {e}")
        
        return history

    def calculate_ltv(self, stripe_customer_id: str) -> float:
        """
        Calculate Lifetime Value (LTV) based on paid invoices.
        """
        if not self.api_key or not stripe_customer_id:
            return 0.0

        ltv = 0.0
        try:
            # Retrieve up to 100 invoices for calculation
            all_invoices = stripe.Invoice.list(
                customer=stripe_customer_id, 
                limit=100
            )
            
            ltv_cents = 0
            for inv in all_invoices.data:
                if inv.status == 'paid':
                    ltv_cents += inv.amount_paid
            
            ltv = ltv_cents / 100.0
        except Exception as e:
            logger.error(f"Error calculating LTV for {stripe_customer_id}: {e}")
            
        return ltv

    def get_subscription_trial_status(self, stripe_subscription_id: str) -> Dict[str, Any]:
        """
        Get trial status information.
        """
        result = {
            "trial_end_date": None,
            "is_trial_expired": False,
            "days_until_trial_end": None
        }

        if not self.api_key or not stripe_subscription_id:
            return result

        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            if subscription.trial_end:
                trial_end_dt = datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)
                result["trial_end_date"] = trial_end_dt.isoformat()
                now = datetime.now(timezone.utc)
                
                # Calculate days until trial end
                delta = trial_end_dt - now
                result["days_until_trial_end"] = max(0, delta.days)
                
                # Check if trial is expired
                # Note: Logic caller typically checks if status is 'trialing' too, but we return raw data here
                if trial_end_dt < now:
                    result["is_trial_expired"] = True
                    result["days_until_trial_end"] = 0
                    
        except Exception as e:
            logger.error(f"Error fetching trial info for {stripe_subscription_id}: {e}")
            
        return result

    def pause_subscription(self, stripe_subscription_id: str) -> bool:
        """
        Pause a subscription (voiding invoices).
        """
        if not self.api_key or not stripe_subscription_id:
            return False

        try:
            stripe.Subscription.modify(
                stripe_subscription_id,
                pause_collection={'behavior': 'void'}
            )
            return True
        except Exception as e:
            logger.error(f"Error pausing subscription {stripe_subscription_id}: {e}")
            raise e

    def resume_subscription(self, stripe_subscription_id: str) -> bool:
        """
        Resume a subscription.
        """
        if not self.api_key or not stripe_subscription_id:
            return False

        try:
            stripe.Subscription.modify(
                stripe_subscription_id,
                pause_collection=''
            )
            return True
        except Exception as e:
            logger.error(f"Error resuming subscription {stripe_subscription_id}: {e}")
            raise e
