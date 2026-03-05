
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from backend.agent_tools import get_worker_handler

# List of ALL expected workers based on file inventory
EXPECTED_WORKERS = [
    ("email-assistant", "EmailWorker"), # Check for alias: email-worker
    ("sms-messaging", "SMSMessagingWorker"),
    ("job-search", "JobSearchWorker"),
    ("weather-worker", "WeatherWorker"), # New
    ("flight-tracker", "FlightTrackerWorker"), # New
    ("map-worker", "MapWorker"), # New
    ("sales-outreach", "SalesOutreachWorker"),
    ("faq-resolution", "FAQResolutionWorker"),
    ("content-writer", "ContentWriterWorker"),
    ("payment-billing", "PaymentBillingWorker"),
    ("order-status", "OrderStatusWorker"),
    ("hr-onboarding", "HROnboardingWorker"),
    ("it-support", "ITSupportWorker"),
    ("meeting-coordination", "MeetingCoordinationWorker"),
    ("lead-research", "LeadResearchWorker"),
    ("translation-worker", "TranslationWorker"),
    ("data-entry", "DataEntryWorker"),
    ("compliance-worker", "ComplianceWorker"),
    ("intelligent-routing", "IntelligentRoutingWorker"),
    ("content-moderation", "ContentModerationWorker"),
    ("sentiment-escalation", "SentimentEscalationWorker")
]

def test_registry():
    print("--- TESTING WORKER REGISTRY ---")
    
    failed = []
    passed = []
    
    for slug, class_name in EXPECTED_WORKERS:
        print(f"\nChecking: {slug} (Expects: {class_name})")
        
        # Test: get_worker_handler
        handler = get_worker_handler(slug)
        print(f"  - get_worker_handler('{slug}'): {handler}")
        
        if not handler:
             print(f"  [FAIL] {slug} is missing from registry!")
             failed.append(slug)
        else:
             passed.append(slug)

    print("\n--- SUMMARY ---")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("MISSING WORKERS:")
        for w in failed:
            print(f" - {w}")
    else:
        print("ALL WORKERS REGISTERED SUCCESSFULLY.")

if __name__ == "__main__":
    test_registry()
