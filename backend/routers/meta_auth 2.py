from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Integration, Workspace
from backend.services.meta_whatsapp_service import MetaWhatsAppService
from backend.security import encrypt_text
import os
import requests
import json
import logging

router = APIRouter(prefix="/auth/meta", tags=["meta-auth"])
logger = logging.getLogger(__name__)

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_API_VERSION = "v24.0"

class MetaAuthRequest(str):
    pass # Placeholder

@router.post("/exchange-token")
async def exchange_token(
    data: dict = Body(...),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exchange short-lived user token for long-lived token
    """
    user_access_token = data.get("access_token")
    if not user_access_token:
        raise HTTPException(status_code=400, detail="Missing access_token")

    # 1. Exchange for Long-Lived User Token
    try:
        url = f"https://graph.facebook.com/{META_API_VERSION}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": META_APP_ID,
            "client_secret": META_APP_SECRET,
            "fb_exchange_token": user_access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        long_lived_token = response.json().get("access_token")
    except Exception as e:
        logger.error(f"Failed to exchange token: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify Facebook login")

    # 2. Return the token to frontend (or fetch accounts immediately)
    return {"access_token": long_lived_token}


@router.get("/accounts")
async def get_meta_accounts(
    access_token: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Fetch accessible WhatsApp Business Accounts and Instagram Accounts
    """
    try:
        # A. Fetch WhatsApp Business Accounts
        waba_url = f"https://graph.facebook.com/{META_API_VERSION}/me/accounts" 
        # Note: /me/accounts lists Pages. WhatsApp is listed under businesses.
        # Correct endpoint for WABA:
        # GET /debug_token to get user_id -> GET /user_id/businesses -> GET /business_id/client_whatsapp_business_accounts
        
        # Simpler approach: GET /me?fields=accounts,businesses
        
        url = f"https://graph.facebook.com/{META_API_VERSION}/me"
        params = {
            "fields": "id,name,businesses{id,name,client_whatsapp_business_accounts{id,name,phone_numbers{id,display_phone_number}}},accounts{id,name,instagram_business_account{id,username}}",
            "access_token": access_token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        formatted_data = {
            "whatsapp": [],
            "instagram": []
        }
        
        # Process WhatsApp
        businesses = data.get("businesses", {}).get("data", [])
        for biz in businesses:
            wabas = biz.get("client_whatsapp_business_accounts", {}).get("data", [])
            for waba in wabas:
                phones = waba.get("phone_numbers", {}).get("data", [])
                for phone in phones:
                    formatted_data["whatsapp"].append({
                        "waba_id": waba["id"],
                        "waba_name": waba["name"],
                        "phone_id": phone["id"],
                        "display_number": phone["display_phone_number"],
                        "business_name": biz["name"]
                    })
                    
        # Process Instagram
        pages = data.get("accounts", {}).get("data", [])
        for page in pages:
            ig_account = page.get("instagram_business_account")
            if ig_account:
                formatted_data["instagram"].append({
                    "page_id": page["id"],
                    "page_name": page["name"],
                    "instagram_id": ig_account["id"],
                    "username": ig_account["username"]
                })
                
        return formatted_data
        
    except Exception as e:
        logger.error(f"Failed to fetch accounts: {e}")
        raise HTTPException(status_code=400, detail=str(e))
