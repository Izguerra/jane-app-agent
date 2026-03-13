from fastapi import APIRouter, Depends
import stripe
import os
from . import subscription, checkout, phone, admin

router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Include sub-routers
router.include_router(subscription.router)
router.include_router(checkout.router)
router.include_router(phone.router)
router.include_router(admin.router)
