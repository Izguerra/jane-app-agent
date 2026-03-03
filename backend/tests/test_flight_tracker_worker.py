import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.workers.flight_tracker_worker import FlightTrackerWorker

class TestFlightTrackerWorker(unittest.TestCase):
    
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_db = MagicMock()

    @patch('backend.workers.flight_tracker_worker.ExternalTools')
    @patch('backend.workers.flight_tracker_worker.FlightTrackerWorker._batch_resolve_iata')
    def test_flight_tracker_by_number(self, mock_resolve, mock_tools_cls):
        # Setup
        mock_tools = mock_tools_cls.return_value
        # Mock the async method get_flight_status
        mock_tools.get_flight_status = AsyncMock(return_value="Status: On Time")
        
        # Mock resolve to not be called or return empty
        mock_resolve.return_value = {}

        input_data = {"flight_number": "AC123" }
        
        # Execute
        result = FlightTrackerWorker._execute_logic("task_1", input_data, self.mock_service, self.mock_db)
        
        # Verify
        self.assertEqual(result["flight_status"], "Status: On Time")
        mock_tools.get_flight_status.assert_called_with(
            flight_number="AC123", 
            origin=None, 
            destination=None, 
            airline=None, 
            date=None, 
            approx_time=None
        )

    @patch('backend.workers.flight_tracker_worker.ExternalTools')
    @patch('backend.workers.flight_tracker_worker.FlightTrackerWorker._batch_resolve_iata')
    def test_flight_tracker_by_route(self, mock_resolve, mock_tools_cls):
        # Setup
        mock_tools = mock_tools_cls.return_value
        mock_tools.get_flight_status = AsyncMock(return_value="Status: Delayed")
        
        # Mock async resolution
        # _batch_resolve_iata is a static method returning a dict
        mock_resolve.return_value = {"New York": ["JFK"], "London": ["LHR"]}

        input_data = {"origin": "New York", "destination": "London"}
        
        # Execute
        # We need to mock the side-effect of asyncio.run if possible, 
        # but since _execute_logic calls asyncio.run internally, we just let it run.
        # However, _batch_resolve_iata is async. We need to handle that.
        
        # FlightTrackerWorker._execute_logic defines an internal async function and runs it.
        # That internal function calls await cls._batch_resolve_iata
        # So our mock must be awaitable OR we patch it to return a future?
        # Since we patch the python object, AsyncMock is best.
        
        mock_resolve.side_effect = AsyncMock(return_value={"New York": ["JFK"], "London": ["LHR"]})

        result = FlightTrackerWorker._execute_logic("task_1", input_data, self.mock_service, self.mock_db)
        
        # Verify
        self.assertEqual(result["flight_status"], "Status: Delayed")
        
        # Check that origin/destination were updated to codes in the call
        mock_tools.get_flight_status.assert_called_with(
            flight_number=None, 
            origin="JFK", 
            destination="LHR", 
            airline=None, 
            date=None, 
            approx_time=None
        )

if __name__ == '__main__':
    unittest.main()
