import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.settings_store import get_settings

class TestSettingsFix(unittest.TestCase):
    
    @patch('backend.settings_store.SessionLocal')
    def test_get_settings_includes_allowed_worker_types(self, mock_session_cls):
        # Setup
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        
        # Mock Agent result
        mock_agent = MagicMock()
        mock_agent.id = "ag_123"
        mock_agent.settings = {} # Empty extended settings
        mock_agent.allowed_worker_types = ["flight-tracker", "email-worker"]
        
        # Configure query chain
        # The logic uses filter(A, B) which is a single call, or filter(A) in fallback.
        # We ensure that any call to first() returns our agent.
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent
        
        # Execute
        settings = get_settings(workspace_id="ws_1")
        
        # Verify
        self.assertIn("allowed_worker_types", settings)
        self.assertEqual(settings["allowed_worker_types"], ["flight-tracker", "email-worker"])
        print("✅ Settings Fix Verified: allowed_worker_types is present and correct.")

if __name__ == '__main__':
    unittest.main()
