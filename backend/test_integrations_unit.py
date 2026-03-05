
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.services.outlook_service import OutlookService
from backend.services.icloud_service import ICloudService
# from backend.services.gmail_service import GmailService # Skipping for brevity/complexity of google discovery mocks

class TestIntegrationsLogc(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_integ = MagicMock()
        self.mock_integ.credentials = '{"access_token": "fake_token", "email": "test@test.com", "app_password": "fake"}'
        self.mock_integ.settings = '{"can_read_emails": true, "can_view_events": true, "can_create_events": true, "can_edit_events": true}'
        
    @patch('backend.services.outlook_service.decrypt_text')
    @patch('backend.services.outlook_service.requests.get')
    def test_outlook_list_emails(self, mock_get, mock_decrypt):
        # Setup
        mock_decrypt.side_effect = lambda x: x # Identity function
        service = OutlookService(self.mock_db)
        service._get_integration = MagicMock(return_value=self.mock_integ)
        service._check_permission = MagicMock(return_value=True) # Mock permission check
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "123",
                    "subject": "Test Email",
                    "from": {"emailAddress": {"name": "Sender", "address": "sender@example.com"}},
                    "receivedDateTime": "2024-01-01T12:00:00Z",
                    "bodyPreview": "Hello world"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Execute
        emails = service.list_emails(workspace_id=1, limit=5)
        
        # Verify
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['subject'], "Test Email")
        self.assertEqual(emails[0]['provider'], "outlook")
        print("✅ Outlook List Emails Logic Passed")

    @patch('backend.services.outlook_service.decrypt_text')
    @patch('backend.services.outlook_service.requests.get')
    def test_outlook_list_events(self, mock_get, mock_decrypt):
        mock_decrypt.side_effect = lambda x: x # Identity
        service = OutlookService(self.mock_db)
        service._get_integration = MagicMock(return_value=self.mock_integ) # use outlook_calendar mocked internally in test logic
        service._check_permission = MagicMock(return_value=True)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "evt123",
                    "subject": "Meeting",
                    "start": {"dateTime": "2024-01-01T10:00:00"},
                    "end": {"dateTime": "2024-01-01T11:00:00"},
                    "bodyPreview": "Discuss things"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        events = service.list_events(1, datetime.now(), datetime.now())
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], "Meeting")
        self.assertEqual(events[0]['provider'], "outlook_calendar")
        print("✅ Outlook List Events Logic Passed")

    def test_icloud_service_init(self):
        # Just testing basic class structure and import validity
        service = ICloudService(self.mock_db)
        self.assertIsNotNone(service)
        print("✅ iCloud Service Init Passed")

if __name__ == '__main__':
    unittest.main()
