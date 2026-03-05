import sys
import os

# Add parent dir
sys.path.append(os.getcwd())

from backend.services.twilio_service import TwilioService
from dotenv import load_dotenv

load_dotenv()

def check_availability():
    service = TwilioService()
    
    print("Checking 416 in US...")
    us_numbers = service.search_phone_numbers(area_code="416", country_code="US", limit=5)
    print(f"Found {len(us_numbers)} in US.")
    for n in us_numbers:
        print(f" - {n['phone_number']} ({n['friendly_name']})")
        
    print("\nChecking 416 in CA...")
    ca_numbers = service.search_phone_numbers(area_code="416", country_code="CA", limit=5)
    print(f"Found {len(ca_numbers)} in CA.")
    for n in ca_numbers:
        print(f" - {n['phone_number']} ({n['friendly_name']})")

if __name__ == "__main__":
    check_availability()
