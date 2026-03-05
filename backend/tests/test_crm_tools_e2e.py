import asyncio
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from backend.agent_tools import AgentTools
from backend.database import SessionLocal
from backend.models_db import Customer, Deal, Campaign, Integration, Appointment, Workspace

class TestCRMToolsE2E(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Ensure test workspace exists
        self.workspace = self.db.query(Workspace).first()
        if not self.workspace:
            self.workspace = Workspace(id="test_ws", name="Test Workspace", team_id="test_team")
            self.db.add(self.workspace)
            self.db.commit()
            self.db.refresh(self.workspace)

    def tearDown(self):
        self.db.close()

    async def run_async_test(self):
        # Setup tools
        tools = AgentTools(workspace_id=self.workspace.id)
        
        print("\n1. Testing list_worker_agents...")
        workers = await tools.list_worker_agents()
        print(f"Result: {workers[:100]}...")
        self.assertTrue("Available" in workers or "No specialized" in workers)

        print("\n2. Testing check_google_calendar_sync...")
        sync_status = await tools.check_google_calendar_sync()
        print(f"Result: {sync_status}")
        self.assertIn("Google Calendar", sync_status)

        print("\n3. Testing Customer Search & Update...")
        test_cust = Customer(
            id="test_cust_123", 
            workspace_id=self.workspace.id, 
            first_name="Test", 
            last_name="User", 
            email="test_crm@example.com",
            lifecycle_stage="Lead"
        )
        self.db.merge(test_cust)
        self.db.commit()
        
        search_res = await tools.search_customers("test_crm")
        print(f"Search Result: {search_res}")
        self.assertIn("Test User", search_res)
        
        update_res = await tools.update_customer_record("test_cust_123", {"lifecycle_stage": "SQL"})
        print(f"Update Result: {update_res}")
        self.assertIn("Successfully updated", update_res)
        self.db.refresh(test_cust)
        self.assertEqual(test_cust.lifecycle_stage, "SQL")

        print("\n4. Testing Deals...")
        deal_res = await tools.create_or_update_deal(title="Big Deal", customer_id="test_cust_123", value_cents=50000)
        print(f"Create Deal Result: {deal_res}")
        self.assertIn("successfully", deal_res)
        
        list_deals_res = await tools.list_deals()
        print(f"List Deals Result: {list_deals_res}")
        self.assertIn("Big Deal", list_deals_res)

        print("\n5. Testing Campaigns...")
        test_cam = Campaign(id="test_cam_123", workspace_id=self.workspace.id, name="Test Campaign", trigger_type="event", status="active")
        self.db.merge(test_cam)
        self.db.commit()
        
        cam_res = await tools.list_active_campaigns()
        print(f"Campaign Result: {cam_res}")
        self.assertIn("Test Campaign", cam_res)

        print("\n6. Testing Lead -> Customer Conversion Trigger...")
        lead = Customer(
            id="lead_conv_123", 
            workspace_id=self.workspace.id, 
            first_name="Potential", 
            last_name="Customer", 
            customer_type="guest",
            lifecycle_stage="Lead"
        )
        self.db.merge(lead)
        self.db.commit()
        
        tools_with_cust = AgentTools(workspace_id=self.workspace.id, customer_id="lead_conv_123")
        
        # Mock external calendar API
        with patch("backend.services.calendar_service.CalendarService.create_event", return_value={"id": "mock_event_id", "title": "Test Appt"}):
            start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            await tools_with_cust.create_appointment(
                title="Sales Pitch",
                start_time=start_time,
                attendee_name="Potential Customer",
                attendee_email="lead_conv@example.com"
            )
            
        self.db.refresh(lead)
        print(f"Lead status after appointment: Type={lead.customer_type}, Stage={lead.lifecycle_stage}")
        self.assertEqual(lead.customer_type, "customer")
        self.assertEqual(lead.lifecycle_stage, "Customer")

    def test_all_crm_tools(self):
        asyncio.run(self.run_async_test())

if __name__ == "__main__":
    unittest.main()
