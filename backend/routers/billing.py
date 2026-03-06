from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Team, Workspace, PhoneNumber
from backend.services.twilio_service import TwilioService
from pydantic import BaseModel
from typing import Optional
import random
import string
from backend.auth import get_current_user, AuthUser
import stripe
import os
from datetime import datetime

router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.get("/subscription")
async def get_subscription(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return {"plan": "Free", "status": "active"}

    # Auto-heal: Check Stripe if DB missing subscription
    if team.stripe_customer_id and not team.stripe_subscription_id:
        try:
             # Check active first
             subs = stripe.Subscription.list(customer=team.stripe_customer_id, limit=1, status='active')
             if subs.data:
                 team.stripe_subscription_id = subs.data[0].id
                 db.commit()
             else:
                 # Check trialing
                 subs_trial = stripe.Subscription.list(customer=team.stripe_customer_id, limit=1, status='trialing')
                 if subs_trial.data:
                     team.stripe_subscription_id = subs_trial.data[0].id
                     db.commit()
        except Exception as e:
            print(f"Auto-heal error: {e}")

    if not team.stripe_customer_id:
        return {
            "plan": team.plan_name or "Free",
            "status": team.subscription_status or "active",
            "is_stripe": False
        }

    try:
        # Fetch subscription details from Stripe if available
        subscription = None
        if team.stripe_subscription_id:
            subscription = stripe.Subscription.retrieve(team.stripe_subscription_id)
        
        # If no subscription ID stored, maybe list subscriptions for customer? (Redundant with auto-heal but keeps fallback)
        if not subscription:
            subs = stripe.Subscription.list(customer=team.stripe_customer_id, limit=1)
            if subs.data:
                subscription = subs.data[0]
                # Update DB
                team.stripe_subscription_id = subscription.id
                db.commit()

        if subscription:
            # Handle both dict and object (Stripe objects usually allow both but let's be safe)
            def get_val(obj, key):
                return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
            
            items_data = get_val(subscription, "items").data[0] # SubscriptionItems is list wrapper
            price = items_data.price
            product_id = price.product
            product = stripe.Product.retrieve(product_id)
            
            return {
                "plan": product.name,
                "status": get_val(subscription, "status"),
                "current_period_end": get_val(subscription, "current_period_end"),
                "cancel_at_period_end": get_val(subscription, "cancel_at_period_end"),
                "amount": price.unit_amount / 100 if price.unit_amount else 0,
                "currency": price.currency,
                "is_stripe": True
            }
    except Exception as e:
        print(f"Stripe Error: {e}")
        # Fallback to DB
        pass

    return {
        "plan": team.plan_name or "Free",
        "status": team.subscription_status or "active",
        "is_stripe": True 
    }

@router.get("/invoices")
async def get_invoices(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        return []

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.stripe_customer_id:
        return []

    try:
        # Fetch last 5 invoices
        invoices = stripe.Invoice.list(customer=team.stripe_customer_id, limit=5)
        return [
            {
                "id": inv.id,
                "date": inv.created,
                "amount": inv.total / 100,
                "currency": inv.currency,
                "status": inv.status,
                "pdf_url": inv.invoice_pdf,
                "number": inv.number
            }
            for inv in invoices.data
        ]
    except Exception as e:
        print(f"Stripe Invoice Error: {e}")
        return []

@router.post("/portal")
async def create_portal_session(
    request: Request,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        # Construct return URL from request headers (origin) OR generic env
        # request.headers.get("referer") is usually the page calling it
        return_url = request.headers.get("referer") or os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000") + "/dashboard/account"

        session = stripe.billing_portal.Session.create(
            customer=team.stripe_customer_id,
            return_url=return_url,
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CheckoutSessionRequest(BaseModel):
    price_id: str
    mode: str = "subscription"

@router.post("/create-checkout-session")
async def create_checkout_session(
    req: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    
    # Resolve workspace_id for the redirect URL
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    ws_part = f"/{workspace.id}" if workspace else "/ws_default"
    
    # Return URL
    base_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
    success_url = f"{base_url}{ws_part}/dashboard/account?checkout=success"
    cancel_url = f"{base_url}{ws_part}/dashboard/account/plans?checkout=cancel"

    try:
        if team.stripe_customer_id:
            # Existing customer
            session = stripe.checkout.Session.create(
                customer=team.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': req.price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                allow_promotion_codes=True,
                billing_address_collection='auto',
            )
        else:
            # New customer (shouldn't happen here usually but fallback)
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': req.price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.email, # Pre-fill email
                allow_promotion_codes=True,
                billing_address_collection='auto',
                metadata={
                    "team_id": team.id,
                    "user_id": user.id
                }
            )
            
    except Exception as e:
        print(f"Checkout Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpgradeRequest(BaseModel):
    price_id: str

@router.post("/preview-upgrade")
async def preview_upgrade(
    req: UpgradeRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return {"amount_due": 0, "can_upgrade": False}
        
    # Auto-heal: If we have customer ID but no subscription ID, check Stripe
    if team.stripe_customer_id and not team.stripe_subscription_id:
        try:
            subs = stripe.Subscription.list(customer=team.stripe_customer_id, limit=1, status='active')
            if subs.data:
                team.stripe_subscription_id = subs.data[0].id
                db.commit()
            else:
                 # Check for trialing too
                 subs_trial = stripe.Subscription.list(customer=team.stripe_customer_id, limit=1, status='trialing')
                 if subs_trial.data:
                     team.stripe_subscription_id = subs_trial.data[0].id
                     db.commit()
        except Exception as e:
            print(f"Error syncing subscription: {e}")

    if not team.stripe_subscription_id:
        # No active subscription to upgrade from
        return {"amount_due": 0, "currency": "usd", "proration_date": int(datetime.utcnow().timestamp()), "can_upgrade": False}

    try:
        # specific logic: retrieve subscription, retrieve upcoming invoice with scheduled change
        subscription = stripe.Subscription.retrieve(team.stripe_subscription_id)
        current_item = subscription['items']['data'][0]

        # Preview the proration
        proration_date = int(datetime.utcnow().timestamp())
        
        items = [{
            'id': current_item.id,
            'price': req.price_id, # New price
        }]

        # Helper for safe access (Stripe objects vs dicts)
        def get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def is_proration(line):
            # Direct check
            if get_val(line, "proration"): return True
            
            # Nested check (newer API structure)
            parent = get_val(line, "parent")
            if parent:
                sub_details = get_val(parent, "subscription_item_details")
                if sub_details:
                    return get_val(sub_details, "proration", False)
            return False

        # Use create_preview (newer API) instead of upcoming
        items = [{
            'id': current_item.id,
            'price': req.price_id, # New price
        }]

        invoice = stripe.Invoice.create_preview(
            customer=team.stripe_customer_id,
            subscription=team.stripe_subscription_id,
            subscription_details={
                "items": items,
                "proration_date": proration_date,
            }
        )

        lines_data = get_val(get_val(invoice, "lines"), "data", [])
        
        # Calculate immediate payment (Prorations only)
        # We look for lines that are prorations. The 'upcoming' invoice usually includes the NEXT period (recurring)
        # which isn't paid today unless we reset the cycle. We assume we don't reset.
        # So Pay Today = Sum of Prorations.
        proration_amount = sum(
            get_val(line, "amount", 0) 
            for line in lines_data 
            if is_proration(line)
        )

        # Get default payment method
        payment_method_details = None
        try:
            customer = stripe.Customer.retrieve(team.stripe_customer_id)
            pm_id = customer.invoice_settings.default_payment_method
            
            if pm_id:
                pm = stripe.PaymentMethod.retrieve(pm_id)
                if pm.type == 'card':
                    payment_method_details = {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4
                    }
        except Exception as e:
            print(f"Error fetching payment method: {e}")

        return {
            "amount_due": proration_amount / 100, # We return this as the "Fee" to show
            "currency": invoice.currency,
            "proration_date": proration_date,
            "can_upgrade": True,
            "payment_method": payment_method_details, 
            "immediate_payment": {
                "amount": proration_amount / 100,
                "currency": invoice.currency,
                "description": f"Pay today to switch to {req.price_id}" 
            },

            "breakdown": [
                {
                    "description": get_val(line, "description"),
                    "amount": get_val(line, "amount", 0) / 100,
                    "period_start": get_val(get_val(line, "period"), "start") if get_val(line, "period") else None,
                    "period_end": get_val(get_val(line, "period"), "end") if get_val(line, "period") else None
                } for line in lines_data 
                if is_proration(line) or get_val(line, "amount", 0) != 0
            ]
        }
    except Exception as e:
        print(f"Proration Preview Error: {e}")
        # If error, it might be because we can't prorate (e.g. going from year to month?) or other issue
        # We can still try to return false to force checkout if needed, 
        # but for now let's raise error or return defaults
        return {"amount_due": 0, "can_upgrade": False}


@router.post("/update-subscription")
async def update_subscription(
    req: UpgradeRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.stripe_subscription_id:
         raise HTTPException(status_code=400, detail="No active subscription to upgrade")

    try:
        subscription = stripe.Subscription.retrieve(team.stripe_subscription_id)
        current_item = subscription['items']['data'][0]
        
        # Determine if we need to collect payment immediately
        updated_sub = stripe.Subscription.modify(
            team.stripe_subscription_id,
            items=[{
                'id': current_item.id,
                'price': req.price_id,
            }],
            proration_behavior='always_invoice', # Charge difference immediately
            payment_behavior='pending_if_incomplete', # Don't fail if payment requires Auth
        )
        
        # Update DB with new plan name
        try:
             # Get product name
             items_data = updated_sub['items']['data'][0]
             price = items_data.price
             product = stripe.Product.retrieve(price.product)
             
             team.plan_name = product.name
             team.subscription_status = updated_sub.status
             db.commit()
        except Exception as e:
            print(f"Error updating DB plan name: {e}")

        return {"status": "success", "subscription_status": updated_sub.status, "plan": team.plan_name}

    except Exception as e:
        print(f"Update Subscription Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PurchaseNumberRequest(BaseModel):
    area_code: Optional[str] = "415"
    phone_number: Optional[str] = None # If user pre-selected a number
    provider: Optional[str] = "twilio" # "twilio" or "telnyx"

@router.post("/purchase-phone-number")
async def purchase_phone_number(
    req: PurchaseNumberRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    team_id = user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User has no team")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="Active subscription required")

    # Check for "Included" number slots
    plan = team.plan_name or "Starter"
    allowed_count = PLAN_ALLOWANCE.get(plan, 1)
    
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    if not workspace:
         raise HTTPException(status_code=404, detail="Workspace not found")

    current_numbers = db.query(PhoneNumber).filter(
        PhoneNumber.workspace_id == workspace.id,
        PhoneNumber.is_active == True
    ).all()
    
    # Count numbers that don't have a Stripe Sub Item (these are the "Included" ones)
    included_count = len([n for n in current_numbers if not n.stripe_subscription_item_id])
    is_included_slot = included_count < allowed_count

    sub_item = None
    if not is_included_slot:
        # 1. Find Price ID for "Additional Phone Number"
        price_search_query = "name:'Additional Twilio Phone Number'" if req.provider == 'twilio' else "name:'Additional Telnyx Phone Number'"
        price_id = os.getenv("STRIPE_ADDITIONAL_NUMBER_PRICE_ID")
        if not price_id:
            try:
                products = stripe.Product.search(query=price_search_query, limit=1)
                if products.data:
                    product_id = products.data[0].id
                    prices = stripe.Price.list(product=product_id, limit=1)
                    if prices.data:
                        price_id = prices.data[0].id
            except Exception as e:
                print(f"Error finding product: {e}")
                
        if not price_id:
            raise HTTPException(status_code=500, detail="Product not configured")

        try:
            # 2. Add Subscription Item in Stripe (This charges the user)
            sub_item = stripe.SubscriptionItem.create(
                subscription=team.stripe_subscription_id,
                price=price_id,
                quantity=1
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    try:
        # 3. Provision Number
        requested_provider = (req.provider or "twilio").lower()
        if requested_provider == "telnyx":
            from backend.services.telnyx_service import TelnyxService
            service = TelnyxService()
        else:
            service = TwilioService()
        
        purchased = None
        friendly_name_prefix = "Included" if is_included_slot else "Add-on"
        
        if req.phone_number:
            # Buy specific number
            try:
                purchased = service.purchase_phone_number(
                    phone_number=req.phone_number,
                    friendly_name=f"{friendly_name_prefix} - {workspace.name}"
                )
            except Exception as e:
                if sub_item:
                    stripe.SubscriptionItem.delete(sub_item.id)
                raise HTTPException(status_code=400, detail=f"Failed to purchase selected number: {str(e)}")
        else:
            # Auto-search
            area_code = req.area_code or "415"
            numbers = service.search_phone_numbers(limit=1, area_code=area_code)
            if not numbers and req.area_code:
                 numbers = service.search_phone_numbers(limit=1, area_code=area_code, country_code="CA")
            
            if not numbers:
                 numbers = service.search_phone_numbers(limit=1, country_code="US")
                 
            if not numbers:
                 if sub_item:
                     stripe.SubscriptionItem.delete(sub_item.id)
                 raise HTTPException(status_code=500, detail="No phone numbers available")
            
            selected = numbers[0]
            purchased = service.purchase_phone_number(
                phone_number=selected["phone_number"],
                friendly_name=f"{friendly_name_prefix} - {workspace.name}"
            )
        
        # 4. Optional: Auto-configure Voice for Telnyx
        if requested_provider == "telnyx":
            # Link to generic connection for LiveKit SIP if configured
            connection_id = os.getenv("TELNYX_CONNECTION_ID")
            if connection_id:
                try:
                    service.configure_voice_connection(purchased["id"], connection_id)
                    print(f"DEBUG: Configured Telnyx voice for {purchased['phone_number']}")
                except Exception as ve:
                    print(f"WARNING: Failed to auto-configure Telnyx voice: {ve}")

        # 5. Save to DB
        new_number = PhoneNumber(
            id=f"pn_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}",
            workspace_id=workspace.id,
            phone_number=purchased["phone_number"],
            friendly_name=purchased.get("friendly_name", f"{friendly_name_prefix} {purchased['phone_number']}"),
            country_code=purchased.get("iso_country", "US"),
            twilio_sid=purchased.get("sid", purchased.get("id")), # Telnyx uses 'id' instead of 'sid'
            provider=requested_provider,
            is_active=True,
            voice_enabled=True,
            sms_enabled=True,
            stripe_subscription_item_id=sub_item.id if sub_item else None,
            monthly_cost=0 if is_included_slot else (999 if req.provider == 'twilio' else 200)
        )
        
        db.add(new_number)
        db.commit()
        db.refresh(new_number)
        
        return {
            "status": "success",
            "phone_number": new_number.phone_number,
            "id": new_number.id,
            "is_included": is_included_slot
        }

    except Exception as e:
        print(f"Purchase Error: {e}")
        if sub_item:
             try: stripe.SubscriptionItem.delete(sub_item.id)
             except: pass
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        print(f"Purchase Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ProvisionRequest(BaseModel):
    team_id: str
    area_code: Optional[str] = "415"

PLAN_ALLOWANCE = {
    "Starter": 1,
    "Starter Plan": 1,
    "Professional": 3,
    "Professional Plan": 3,
    "Pro": 3,
    "Pro Plan": 3,
    "Pro+": 5,
    "Pro+ Plan": 5,
    "ProMax": 10,
    "ProMax Plan": 10,
    "Enterprise": 20,
    "Enterprise Plan": 20
}

def generate_pn_id(prefix="pn"):
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

@router.post("/provision")
async def provision_numbers(
    req: ProvisionRequest,
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == req.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    workspace = db.query(Workspace).filter(Workspace.team_id == team.id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    plan = team.plan_name or "Starter"
    allowed = PLAN_ALLOWANCE.get(plan, 0)
    
    current_numbers = db.query(PhoneNumber).filter(
        PhoneNumber.workspace_id == workspace.id,
        PhoneNumber.is_active == True
    ).all()
    
    count = len(current_numbers)
    needed = 0
    if count < allowed:
        needed = allowed - count
        twilio = TwilioService()
        for _ in range(needed):
            try:
                # Use provided area code
                numbers = twilio.search_phone_numbers(limit=1, area_code=req.area_code)
                if not numbers and req.area_code:
                    # Try CA if US failed
                    numbers = twilio.search_phone_numbers(limit=1, area_code=req.area_code, country_code="CA")
                
                if not numbers:
                    # Fallback to US if specific area code not found
                    numbers = twilio.search_phone_numbers(limit=1, country_code="US")
                
                if numbers:
                    selected = numbers[0]
                    purchased = twilio.purchase_phone_number(
                        phone_number=selected["phone_number"],
                        friendly_name=f"Included Number - {workspace.name}"
                    )
                    
                    new_number = PhoneNumber(
                        id=generate_pn_id(),
                        workspace_id=workspace.id,
                        phone_number=purchased["phone_number"],
                        friendly_name=purchased["friendly_name"],
                        country_code="US", 
                        twilio_sid=purchased["sid"],
                        is_active=True,
                        voice_enabled=True,
                        sms_enabled=True
                    )
                    db.add(new_number)
                    db.commit()
            except Exception as e:
                print(f"Provisioning error: {e}")
                
    return {"status": "success", "provisioned": needed, "current_count": count + needed}

# Admin Endpoints for Billing Dashboard
@router.get("/admin/stats")
async def get_admin_billing_stats(
    time_range: int = 30,  # days
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get overall billing statistics for admin dashboard"""
    
    # Verify admin access
    if current_user.role != "supaagent_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import timedelta
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range)
    
    try:
        # Get all invoices for this time period
        invoices = stripe.Invoice.list(
            limit=100,
            created={
                'gte': int(start_date.timestamp()),
                'lte': int(end_date.timestamp())
            }
        )
        
        # Calculate stats
        total_revenue = sum(inv.amount_paid / 100 for inv in invoices.data if inv.status == 'paid')
        pending_amount = sum(inv.amount_due / 100 for inv in invoices.data if inv.status == 'open')
        pending_count = len([inv for inv in invoices.data if inv.status == 'open'])
        failed_payments = len([inv for inv in invoices.data if inv.status == 'uncollectible'])
        
        # Get active subscriptions count
        subscriptions = stripe.Subscription.list(status='active', limit=100)
        active_subscribers = len(subscriptions.data)
        
        # Calculate revenue change (compare to previous period)
        prev_start = start_date - timedelta(days=time_range)
        prev_invoices = stripe.Invoice.list(
            limit=100,
            created={
                'gte': int(prev_start.timestamp()),
                'lte': int(start_date.timestamp())
            }
        )
        prev_revenue = sum(inv.amount_paid / 100 for inv in prev_invoices.data if inv.status == 'paid')
        revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "revenue_change": round(revenue_change, 1),
            "active_subscribers": active_subscribers,
            "subscriber_change": 5.4,  # TODO: Calculate actual change
            "pending_amount": pending_amount,
            "pending_count": pending_count,
            "failed_payments": failed_payments
        }
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        # Return mock data if Stripe is not configured
        return {
            "total_revenue": 48250.00,
            "revenue_change": 12,
            "active_subscribers": 1240,
            "subscriber_change": 5.4,
            "pending_amount": 3200.00,
            "pending_count": 14,
            "failed_payments": 8,
        }

@router.get("/admin/invoices")
async def get_admin_invoices(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get all invoices for admin dashboard"""
    
    # Verify admin access
    if current_user.role != "supaagent_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get invoices from Stripe
        params = {'limit': limit}
        if status and status != 'all':
            params['status'] = status
        
        invoices = stripe.Invoice.list(**params)
        
        # Format invoice data
        invoice_list = []
        for inv in invoices.data:
            # Get customer name
            customer_name = "Unknown"
            if inv.customer:
                try:
                    customer = stripe.Customer.retrieve(inv.customer)
                    customer_name = customer.name or customer.email or "Unknown"
                except:
                    pass
            
            # Get plan name from subscription
            plan_name = "One-time Payment"
            if inv.subscription:
                try:
                    subscription = stripe.Subscription.retrieve(inv.subscription)
                    if subscription.items.data:
                        price = subscription.items.data[0].price
                        plan_name = f"{price.nickname or 'Plan'} ({'Monthly' if price.recurring.interval == 'month' else 'Annual'})"
                except:
                    pass
            
            # Map Stripe status to our status
            status_map = {
                'paid': 'paid',
                'open': 'pending',
                'uncollectible': 'failed',
                'void': 'refunded'
            }
            
            invoice_list.append({
                "id": inv.id,
                "invoice_number": inv.number or f"#INV-{inv.id[:8]}",
                "customer_name": customer_name,
                "plan": plan_name,
                "date": datetime.fromtimestamp(inv.created).strftime('%b %d, %Y'),
                "amount": inv.amount_paid / 100 if inv.amount_paid else inv.amount_due / 100,
                "status": status_map.get(inv.status, inv.status),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url
            })
        
        return {
            "invoices": invoice_list,
            "total": len(invoice_list),
            "has_more": invoices.has_more
        }
    
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        # Return mock data if Stripe is not configured
        return {
            "invoices": [
                {
                    "id": "inv_001",
                    "invoice_number": "#INV-2024-001",
                    "customer_name": "Acme Corp",
                    "plan": "Pro Plan (Monthly)",
                    "date": "Oct 24, 2024",
                    "amount": 49.00,
                    "status": "paid",
                    "invoice_pdf": None,
                    "hosted_invoice_url": None
                },
                {
                    "id": "inv_002",
                    "invoice_number": "#INV-2024-002",
                    "customer_name": "Global Systems",
                    "plan": "Enterprise Plan",
                    "date": "Oct 23, 2024",
                    "amount": 299.00,
                    "status": "pending",
                    "invoice_pdf": None,
                    "hosted_invoice_url": None
                },
                {
                    "id": "inv_003",
                    "invoice_number": "#INV-2024-003",
                    "customer_name": "Starlight Inc.",
                    "plan": "Starter Plan",
                    "date": "Oct 22, 2024",
                    "amount": 19.00,
                    "status": "failed",
                    "invoice_pdf": None,
                    "hosted_invoice_url": None
                },
                {
                    "id": "inv_004",
                    "invoice_number": "#INV-2024-004",
                    "customer_name": "NextGen Bionics",
                    "plan": "Pro Plan (Annual)",
                    "date": "Oct 20, 2024",
                    "amount": 490.00,
                    "status": "paid",
                    "invoice_pdf": None,
                    "hosted_invoice_url": None
                },
                {
                    "id": "inv_005",
                    "invoice_number": "#INV-2024-005",
                    "customer_name": "Tech Dash",
                    "plan": "Pro Plan (Monthly)",
                    "date": "Oct 18, 2024",
                    "amount": 49.00,
                    "status": "paid",
                    "invoice_pdf": None,
                    "hosted_invoice_url": None
                }
            ],
            "total": 5,
            "has_more": False
        }

@router.post("/admin/invoices/{invoice_id}/retry")
async def retry_admin_payment(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Retry a failed payment (admin only)"""
    
    # Verify admin access
    if current_user.role != "supaagent_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        # Attempt to pay the invoice
        result = stripe.Invoice.pay(invoice_id)
        
        return {
            "success": True,
            "status": result.status,
            "message": "Payment retry initiated"
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
