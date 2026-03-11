
import sys
import os
import time
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.workers.email_worker import EmailWorker
from backend.workers.flight_tracker_worker import FlightTrackerWorker
from backend.database import SessionLocal


# Helpers
def run_async(coro):
    return asyncio.run(coro)

def verify_enhancements():
    # Mock Service and DB
    mock_service = MagicMock()
    mock_db = MagicMock()
    mock_service.get_task.return_value.workspace_id = "1"
    
    print("--- Verifying Email Enhancements (CC/BCC) ---")
    
    input_data = {
        "action": "send",
        "recipient": "user@example.com",
        "subject": "Test Email",
        "body": "Hello World",
        "cc": ["manager@example.com"],
        "bcc": ["archive@example.com"]
    }
    
    async def test_email():
        with patch('backend.database.SessionLocal') as MockDB:
            with patch('backend.workers.email_worker.MailboxTools') as MockMailbox:
                mock_mb_instance = MockMailbox.return_value
                mock_mb_instance.list_emails.return_value = '[{"id": "1", "from": "a", "subject": "b", "snippet": "c"}]'
                mock_mb_instance.search_emails.return_value = '[]'
                mock_mb_instance.send_email.return_value = "Sent"
                
                print("Calling EmailWorker...")
                result = await EmailWorker._execute_async("task-1", input_data, mock_service)
                
                mock_mb_instance.send_email.assert_called_with(
                    to_email="user@example.com",
                    subject="Test Email",
                    body="Hello World",
                    cc=["manager@example.com"],
                    bcc=["archive@example.com"]
                )
                print("PASS: EmailWorker correctly passed CC/BCC.")

    # Run Email Test
    asyncio.run(test_email())

    print("\n--- Verifying Flight Enhancements (Airport Resolution) ---")
    
    # Run Flight Test (Synchronous call to _execute_logic which handles its own loop)
    
    # SCENARIO 1: Ambiguous
    print("Scenario 1: Ambiguous City (New York)")
    input_data_1 = {"origin": "New York", "destination": "London"}
    
    with patch('backend.workers.flight_tracker_worker.AsyncOpenAI') as MockAI:
        mock_client = MockAI.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"codes": ["JFK", "LGA", "EWR"]}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = FlightTrackerWorker._execute_logic("task-2", input_data_1, mock_service, mock_db)
        
        if "Multiple airports found" in str(result):
             print(f"PASS: Identified ambiguity. Result: {result.get('error')}")
        else:
             print(f"FAIL: {result}")

    # SCENARIO 2: Specific
    print("\nScenario 2: Single Airport Resolution (Toronto)")
    input_data_2 = {"origin": "Toronto", "destination": "Montreal"}
    
    with patch('backend.workers.flight_tracker_worker.AsyncOpenAI') as MockAI:
        mock_client = MockAI.return_value
        
        async def mock_llm_response(*args, **kwargs):
            content = kwargs['messages'][1]['content']
            resp = MagicMock()
            if "Toronto" in content:
                resp.choices[0].message.content = '{"codes": ["YYZ"]}'
            elif "Montreal" in content:
                resp.choices[0].message.content = '{"codes": ["YUL"]}'
            else:
                 resp.choices[0].message.content = '{"codes": ["UNKNOWN"]}'
            return resp
            
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_llm_response)
        
        with patch('backend.workers.flight_tracker_worker.ExternalTools') as MockExternal:
             mock_tool = MockExternal.return_value
             mock_tool.get_flight_status = AsyncMock(return_value="Flight found")
             
             result = FlightTrackerWorker._execute_logic("task-3", input_data_2, mock_service, mock_db)
             
             mock_tool.get_flight_status.assert_called_with(None, "YYZ", "YUL", None)
             print("PASS: Resolved and called API with YYZ/YUL.")

if __name__ == "__main__":
    verify_enhancements()
