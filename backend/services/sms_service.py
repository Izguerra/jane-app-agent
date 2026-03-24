import os
from twilio.rest import Client
import logging
import re
import json

logger = logging.getLogger("sms-service")

def format_phone_number(phone: str) -> str:
    """
    Format a phone number to E.164 format for Twilio.
    Assumes North American numbers if no country code is present.
    
    Args:
        phone: Phone number in various formats
        
    Returns:
        str: Phone number in E.164 format (+1XXXXXXXXXX)
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # If it starts with 1 and has 11 digits, it's already formatted (just needs +)
    if len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    
    # If it has 10 digits, assume North American and add +1
    if len(digits) == 10:
        return f"+1{digits}"
    
    # If it already has a country code (more than 10 digits), add +
    if len(digits) > 10:
        return f"+{digits}"
    
    # Otherwise, return as-is with + (might fail, but let Twilio handle it)
    return f"+{digits}"

def send_sms(to_number: str, message: str, workspace_id: int = None, force_whatsapp: bool = False) -> (bool, str):
    """
    Send an SMS message using Twilio.
    
    Args:
        to_number: The recipient's phone number
        message: The message body
        workspace_id: Workspace ID for credentials
        force_whatsapp: If True, treats this as a WhatsApp message regardless of other settings
        
    Returns:
        (bool, str): (True, None) if successful, (False, error_message) otherwise
    """
    if not workspace_id:
        logger.error("Cannot send SMS: workspace_id is required")
        return False, "workspace_id is required"
    
    account_sid = None
    auth_token = None
    from_number = None
    is_whatsapp = force_whatsapp # Initialize with passed value
    
    # 1. Try to get WhatsApp credentials from database (Client Integration)
    # ONLY if prompt requested WhatsApp
    if is_whatsapp:
        try:
            from backend.database import SessionLocal
            from backend.models_db import Integration
            
            db = SessionLocal()
            try:
                whatsapp_integration = db.query(Integration).filter(
                    Integration.workspace_id == workspace_id,
                    Integration.provider == "whatsapp",
                    Integration.is_active == True
                ).first()
                
                if whatsapp_integration:
                    # Decrypt credentials before parsing
                    from backend.security import decrypt_text
                    
                    credentials = {}
                    if whatsapp_integration.credentials:
                        try:
                            decrypted_creds = decrypt_text(whatsapp_integration.credentials)
                            credentials = json.loads(decrypted_creds)
                        except Exception as e:
                            logger.error(f"Failed to decrypt WhatsApp credentials: {e}")
                    
                    settings = json.loads(whatsapp_integration.settings) if whatsapp_integration.settings else {}
                    
                    # Check if we have valid credentials
                    wa_sid = credentials.get("account_sid") or settings.get("account_sid")
                    wa_token = credentials.get("auth_token") or settings.get("auth_token")
                    wa_phone = credentials.get("phone_number") or settings.get("phone_number")
                    
                    if wa_sid and wa_token and wa_phone:
                        account_sid = wa_sid
                        auth_token = wa_token
                        from_number = wa_phone
                        is_whatsapp = True
                        logger.info(f"Using Client WhatsApp credentials for workspace {workspace_id}")
                    else:
                        logger.warning(f"WhatsApp integration found for workspace {workspace_id} but missing credentials. Falling back to platform SMS.")
                else:
                    logger.info(f"No WhatsApp integration for workspace {workspace_id}. Falling back to platform SMS.")
                    
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error checking database for WhatsApp credentials: {e}")
        # Continue to fallback
    
    # Format phone numbers early
    formatted_to = format_phone_number(to_number)
    
    # 2. Check Database for Assigned Number / Provider (New)
    try:
        from backend.database import SessionLocal
        from backend.models_db import PhoneNumber
        
        db = SessionLocal()
        try:
            # Find the most recently active number for this workspace
            phone_record = db.query(PhoneNumber).filter(
                PhoneNumber.workspace_id == workspace_id,
                PhoneNumber.is_active == True
            ).order_by(PhoneNumber.created_at.desc()).first()
            
            if phone_record:
                from_number = phone_record.phone_number
                provider = phone_record.provider or "twilio"
                
                if provider == "telnyx":
                    from backend.services.telnyx_service import TelnyxService
                    telnyx_svc = TelnyxService()
                    try:
                        result = telnyx_svc.send_sms(
                            from_number=from_number,
                            to_number=formatted_to,
                            text=message
                        )
                        logger.info(f"Telnyx SMS sent successfully to {formatted_to}: {result}")
                        return True, None
                    except Exception as te:
                        logger.error(f"Telnyx SMS failed to {formatted_to}: {te}")
                        return False, str(te)
                
                # If twilio, we fall through to existing Twilio logic but use the from_number found
                logger.info(f"Using found Twilio number {from_number} for workspace {workspace_id}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Error checking DB for phone number: {e}. Falling back to default.")

    # 3. Fallback to Platform SMS (Environment Variables)
    if not account_sid or not auth_token or not from_number:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = from_number or os.getenv("TWILIO_PHONE_NUMBER")
        # Keep is_whatsapp as True if force_whatsapp was passed, otherwise default to False
        if not is_whatsapp: 
            is_whatsapp = False 
        
        if account_sid and auth_token and from_number:
            logger.info("Using Platform SMS credentials (fallback)")
        else:
            logger.error("No credentials available (neither Client WhatsApp nor Platform SMS). Message cannot be sent.")
            return False, "No SMS/WhatsApp credentials available"
    
    # Ensure is_whatsapp is set correctly if from_number explicitly has 'whatsapp:'
    # OR if using the known Twilio Sandbox number (+14155238888), which is EXCLUSIVELY WhatsApp.
    if from_number:
        if "whatsapp" in from_number.lower():
            is_whatsapp = True
        elif "14155238888" in from_number.replace("+", "").replace("-", ""):
            # Detect Twilio Sandbox number usage and force WhatsApp
            is_whatsapp = True
            logger.info("Detected Twilio Sandbox number. Forcing is_whatsapp=True")
        
    if is_whatsapp:
        # Ensure 'whatsapp:' prefix is present for both numbers
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        
        # Check if destination might already have whatsapp: prefix (handled by logic above but formatted_to strips it)
        # If the original to_number had 'whatsapp:', we should definitely trust that.
        # But format_phone_number strips alpha. So we re-add here.
        if not formatted_to.startswith("whatsapp:"):
            formatted_to = f"whatsapp:{formatted_to}"
            
        logger.info(f"Sending WhatsApp message to {formatted_to} from {from_number}")
    else:
        logger.info(f"Attempting to send SMS to {formatted_to} (original: {to_number}) from {from_number}")
        
    try:
        client = Client(account_sid, auth_token)
        
        sent_message = client.messages.create(
            body=message,
            from_=from_number,
            to=formatted_to
        )
        
        logger.info(f"Message sent successfully to {formatted_to}: SID={sent_message.sid}, Status={sent_message.status}")
        return True, None
    except Exception as e:
        logger.error(f"Failed to send message to {formatted_to}: {type(e).__name__}: {e}")
        return False, str(e)

