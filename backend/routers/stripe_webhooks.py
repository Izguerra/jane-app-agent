from fastapi import APIRouter, Request, HTTPException, Header
import stripe
import os
import logging
from sqlalchemy.orm import Session
from backend.database import SessionLocal, generate_phone_id
from backend.models_db import Team, Workspace, PhoneNumber
from backend.services.twilio_service import TwilioService

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks"])
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Allowance map
PLAN_ALLOWANCE = {
    "Starter": 1,
    "Professional": 3,
    "Enterprise": 10
}

@router.post("")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        # For dev without secret, maybe pass? No, strict.
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] in ["customer.subscription.created", "customer.subscription.updated"]:
        subscription = event["data"]["object"]
        await handle_subscription_change(subscription)

    return {"status": "success"}

async def handle_subscription_change(subscription):
    customer_id = subscription["customer"]
    
    # Get product to know the plan
    # In reality subscription.plan.nickname or product lookup needed
    plan_name = "Starter" # Default
    try:
        if subscription.get("plan"):
             # Or fetch product
             product_id = subscription["items"]["data"][0]["price"]["product"]
             product = stripe.Product.retrieve(product_id)
             plan_name = product.name
    except Exception as e:
        logger.error(f"Error fetching product: {e}")

    logger.info(f"Processing subscription for customer {customer_id}, Plan: {plan_name}")

    db = SessionLocal()
    try:
        team = db.query(Team).filter(Team.stripe_customer_id == customer_id).first()
        if not team:
            logger.warning(f"Team not found for stripe customer {customer_id}")
            return

        # Update team plan info
        team.plan_name = plan_name
        team.stripe_subscription_id = subscription["id"]
        team.subscription_status = subscription["status"]
        db.commit()

        # Provisioning Logic
        workspace = db.query(Workspace).filter(Workspace.team_id == team.id).first()
        if not workspace:
            logger.warning("Workspace not found for team")
            return

        allowed_count = PLAN_ALLOWANCE.get(plan_name, 0)
        
        # Count existing numbers (excluding Purchased Add-ons - how to distinguish? Maybe assuming included ones don't have stripe_subscription_item_id?)
        # Let's check all active numbers. 
        # Actually proper logic: Active numbers = Included + Purchased.
        # But here we are provisioning "Included" ones.
        # If we have purchased ones, they should persist.
        # Let's simplistic approach: Ensure we have AT LEAST allowed_count numbers.
        
        current_numbers = db.query(PhoneNumber).filter(
            PhoneNumber.workspace_id == workspace.id,
            PhoneNumber.is_active == True
        ).all()
        
        count = len(current_numbers)
        
        if count < allowed_count:
            needed = allowed_count - count
            logger.info(f"Provisioning {needed} new numbers for workspace {workspace.id}")
            
            twilio_service = TwilioService()
            
            for _ in range(needed):
                try:
                    # Search
                    # Check metadata from subscription for preferred area code
                    area_code = subscription.get("metadata", {}).get("preferred_area_code") or "415"
                    
                    logger.info(f"Preferred area code from metadata: {area_code}")
                    
                    if workspace.phone:
                        # Try to extract area code from workspace phone
                        pass 
                    
                    # Smart Country Detection
                    target_country = "US"
                    # Common Canadian Area Codes (expanding list as needed)
                    CANADIAN_CODES = ["416", "647", "437", "905", "289", "365", "604", "778", "236", "403", "780", "514", "438", "613", "343"]
                    if area_code in CANADIAN_CODES:
                        target_country = "CA"
                        
                    numbers = []
                    
                    # Try preferred country first if known
                    if target_country == "CA":
                         numbers = twilio_service.search_phone_numbers(limit=1, area_code=area_code, country_code="CA")
                    
                    # If not found or US, try US (standard path)
                    if not numbers:
                        numbers = twilio_service.search_phone_numbers(limit=1, area_code=area_code, country_code="US")
                        
                    # If US failed and we haven't tried CA yet (e.g. unknown code that happens to be CA)
                    if not numbers and target_country == "US":
                        numbers = twilio_service.search_phone_numbers(limit=1, area_code=area_code, country_code="CA")
                        if numbers:
                             target_country = "CA" # Update target country if found in CA
                        
                    # Fallback Logic
                    if not numbers:
                        logger.warning(f"Could not find number in {area_code}. Falling back to general pool for {target_country}.")
                        numbers = twilio_service.search_phone_numbers(limit=1, country_code=target_country) # Fallback to same country
                        
                    # Ultimate Fallback to US if CA general failed (unlikely but safe)
                    if not numbers and target_country != "US":
                         numbers = twilio_service.search_phone_numbers(limit=1, country_code="US")
                        
                    if numbers:
                        selected = numbers[0]
                        purchased = twilio_service.purchase_phone_number(
                            phone_number=selected["phone_number"],
                            friendly_name=f"Included Number - {workspace.name}"
                        )
                        
                        # Find Orchestrator agent to assign to
                        from backend.models_db import Agent
                        orchestrator = db.query(Agent).filter(
                            Agent.workspace_id == workspace.id,
                            Agent.is_orchestrator == True
                        ).first()
                        
                        # Save to DB
                        new_number = PhoneNumber(
                            id=generate_phone_id(),
                            workspace_id=workspace.id,
                            phone_number=purchased["phone_number"],
                            friendly_name=purchased.get("friendly_name", f"Number {purchased['phone_number']}"),
                            country_code=purchased.get("iso_country", "US"),
                            twilio_sid=purchased["sid"],
                            is_active=True,
                            voice_enabled=True,
                            sms_enabled=True,
                            agent_id=orchestrator.id if orchestrator else None
                        )
                        db.add(new_number)
                        db.commit()
                        logger.info(f"Provisioned {new_number.phone_number} for Workspace {workspace.id} (Agent: {new_number.agent_id})")
                        
                except Exception as e:
                    logger.error(f"Error provisioning number: {e}")
                    
    finally:
        db.close()

def generate_id(prefix):
    import random, string
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
