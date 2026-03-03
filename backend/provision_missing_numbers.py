from backend.database import SessionLocal
from backend.models_db import Team, Workspace, PhoneNumber
from backend.services.twilio_service import TwilioService
import random, string
import os

PLAN_ALLOWANCE = {
    "Starter": 1,
    "Professional": 3,
    "Enterprise": 10
}

def generate_id(prefix):
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

def provision():
    db = SessionLocal()
    try:
        teams = db.query(Team).all()
        print(f"Checking {len(teams)} teams...")
        
        for team in teams:
            workspace = db.query(Workspace).filter(Workspace.team_id == team.id).first()
            if not workspace:
                continue
                
            plan = team.plan_name or "Starter"
            allowed = PLAN_ALLOWANCE.get(plan, 0)
            
            numbers = db.query(PhoneNumber).filter(
                PhoneNumber.workspace_id == workspace.id,
                PhoneNumber.is_active == True
            ).all()
            
            print(f"Team {team.id} (Plan: {plan}) has {len(numbers)}/{allowed} numbers.")
            
            if len(numbers) < allowed:
                needed = allowed - len(numbers)
                print(f"Provisioning {needed} numbers for workspace {workspace.id}...")
                
                twilio = TwilioService()
                for _ in range(needed):
                    try:
                        search = twilio.search_phone_numbers(limit=1, country_code="US")
                        if search:
                            selected = search[0]
                            # Using 'Jane App Agent' friendly name part if needed, assuming default logic is fine
                            purchased = twilio.purchase_phone_number(
                                phone_number=selected["phone_number"],
                                friendly_name=f"Included Number - {workspace.name}"
                            )
                            
                            new_pn = PhoneNumber(
                                id=generate_id("pn"),
                                workspace_id=workspace.id,
                                phone_number=purchased["phone_number"],
                                friendly_name=purchased["friendly_name"],
                                country_code="US",
                                twilio_sid=purchased["sid"],
                                is_active=True,
                                voice_enabled=True,
                                sms_enabled=True
                            )
                            db.add(new_pn)
                            db.commit()
                            print(f"Success: {new_pn.phone_number}")
                        else:
                            print("No numbers found to purchase.")
                    except Exception as e:
                        print(f"Error provisioning: {e}")
                        
    finally:
        db.close()

if __name__ == "__main__":
    provision()
