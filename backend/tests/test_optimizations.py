
import unittest
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

class TestWorkerOptimizations(unittest.TestCase):

    def setUp(self):
        # Mock database session to prevent actual DB connection attempts
        self.mock_db_patcher = patch('backend.database.SessionLocal')
        self.mock_db = self.mock_db_patcher.start()
        
    def tearDown(self):
        self.mock_db_patcher.stop()

    def test_01_worker_executor_poll_interval(self):
        """Verify WorkerExecutor defaults to 1s poll interval"""
        from backend.workers.worker_executor import WorkerExecutor
        executor = WorkerExecutor()
        print(f"\n[TEST 01] WorkerExecutor.poll_interval: {executor.poll_interval}")
        self.assertEqual(executor.poll_interval, 1, "Poll interval should be 1 second")

    def test_02_worker_tools_docstrings(self):
        """Verify WorkerTools have correct semantic descriptions"""
        from backend.tools.worker_tools import WorkerTools
        
        # Check run_task_now
        run_task_doc = WorkerTools.run_task_now.__doc__ or ""
        print(f"\n[TEST 02a] run_task_now docstring length: {len(run_task_doc)}")
        # Check for case-insensitive match or specific phrase used in updated docstring
        self.assertTrue("immediately" in run_task_doc.lower(), "run_task_now should mention 'immediately'")
        
        # Check dispatch_worker_task
        dispatch_doc = WorkerTools.dispatch_worker_task.__doc__ or ""
        print(f"[TEST 02b] dispatch_worker_task docstring length: {len(dispatch_doc)}")
        # The update included "LONG-RUNNING" in the decorator description, but "background worker task" in docstring
        # Let's check for "background" or "long-running" broadly
        self.assertTrue("long-running" in dispatch_doc.lower(), "dispatch_worker_task should mention 'long-running'")

    def test_03_agent_system_prompt(self):
        """Verify AgentManager injects tool usage instructions"""
        from backend.agent import AgentManager
        
        # Create a dummy AgentManager (No args in init based on source inspection)
        manager = AgentManager()
        settings = {"prompt_template": "Custom Template"}
        
        with patch('backend.agent.Agent') as MockAgent:
            manager._create_agent(settings, team_id=1, tools=[], current_customer=None)
            
            call_args = MockAgent.call_args
            if call_args:
                _, kwargs = call_args
                instructions = kwargs.get('instructions', [])
                full_text = " ".join(instructions)
                
                print(f"\n[TEST 03] Agent Instructions length: {len(full_text)}")
                self.assertIn("TOOL USAGE & FOLLOW-UP QUESTIONS", full_text, "Agent instructions missing TOOL USAGE section")
                self.assertIn("ASK the user for it", full_text, "Agent instructions missing Follow-up question logic")
            else:
                self.fail("Agent class was not initialized")

    def test_04_voice_agent_prompt(self):
        """Verify Voice Agent entrypoint constructs correct prompt"""
        voice_agent_path = os.path.join(PROJECT_ROOT, 'backend/voice_agent.py')
        with open(voice_agent_path, 'r') as f:
            content = f.read()
            
        print(f"\n[TEST 04] Checking voice_agent.py content")
        self.assertIn("TOOL USAGE & FOLLOW-UP QUESTIONS", content, "voice_agent.py missing Tool Usage prompt injection")

    def test_05_workspaces_import_fix(self):
        """Verify backend/routers/workspaces.py has datetime import"""
        workspaces_path = os.path.join(PROJECT_ROOT, 'backend/routers/workspaces.py')
        with open(workspaces_path, 'r') as f:
            content = f.read()
            
        print(f"\n[TEST 05] Checking workspaces.py imports")
        self.assertIn("from datetime import datetime", content, "workspaces.py missing datetime import")

    def test_06_verify_run_task_now_logic(self):
        """Verify run_task_now calls run_in_executor (Synchronous execution)"""
        from backend.tools.worker_tools import WorkerTools
        
        tools = WorkerTools(workspace_id=1, agent_id=1)
        
        with patch('asyncio.get_running_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop
            mock_loop.run_in_executor = AsyncMock(return_value="Task Result")
            
            with patch('backend.tools.worker_tools.WorkerService') as MockService:
                # Patch where it is IMPORTED, which is inside backend.tools.worker_tools scope?
                # No, it's imported as `from backend.agent_tools import get_worker_handler` inside the function.
                # To patch this, we need to patch `backend.agent_tools.get_worker_handler`.
                with patch('backend.agent_tools.get_worker_handler') as mock_get_handler:
                    mock_get_handler.return_value = MagicMock()
                    
                    result = asyncio.run(tools.run_task_now("test-worker", {"param": "val"}))
                    print(f"\n[TEST 06] run_task_now result: {result}")
                    
                    mock_loop.run_in_executor.assert_called()
                    self.assertEqual(result, "Task Result")

if __name__ == '__main__':
    unittest.main()
