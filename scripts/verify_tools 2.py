import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.appointments import AppointmentTools
from backend.tools.customers import CustomerTools
from backend.tools.general import GeneralTools
from backend.database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verification")

def test_tools():
    logger.info("--- Starting Tool Verification ---")
    
    workspace_id = "test_workspace_123"
    customer_id = "test_customer_456"
    comm_id = "test_comm_789"

    try:
        # 1. Test Customer Tools
        logger.info("[1/3] Testing CustomerTools...")
        cust_tools = CustomerTools(workspace_id=workspace_id)
        # Just check if method exists and runs (even if DB empty)
        status = cust_tools.check_registration_status(email="test@example.com")
        logger.info(f"CustomerTools.check_registration_status result: {status}")
        
        # 2. Test General Tools
        logger.info("[2/3] Testing GeneralTools...")
        gen_tools = GeneralTools(workspace_id=workspace_id)
        weather = gen_tools.get_weather("New York")
        logger.info(f"GeneralTools.get_weather result: {weather}")

        # 3. Test Appointment Tools
        logger.info("[3/3] Testing AppointmentTools...")
        appt_tools = AppointmentTools(workspace_id=workspace_id, customer_id=customer_id, communication_id=comm_id)
        availability = appt_tools.get_availability("2025-10-30")
        logger.info(f"AppointmentTools.get_availability result: {availability}")
        
        logger.info("--- Verification SUCCESS: All tools verified! ---")
        return True

    except Exception as e:
        logger.error(f"--- Verification FAILED: {e} ---", exc_info=True)
        return False

if __name__ == "__main__":
    if test_tools():
        sys.exit(0)
    else:
        sys.exit(1)
