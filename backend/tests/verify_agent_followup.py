
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.agent import AgentManager

class TestAgentFollowUpLogic(unittest.TestCase):
    def test_agent_instructions_for_missing_params(self):
        """
        Verify that the Agent is explicitly instructed to ASK for missing parameters
        instead of guessing or calling tools with partial data.
        """
        manager = AgentManager()
        
        # Capture the construction of the Agent to inspect instructions
        with patch('backend.agent.Agent') as MockAgent:
            manager._create_agent(settings={}, team_id=1)
            
            call_args = MockAgent.call_args
            _, kwargs = call_args
            instructions = kwargs.get('instructions', [])
            full_text = " ".join(instructions)
            
            print("\n--- Agent Instruction Check ---")
            
            # Key phrases we added in the optimization phase
            required_phrases = [
                "BEFORE calling ANY tool",
                "parameter is missing",
                "ASK the user for it",
                "Do NOT guess"
            ]
            
            for phrase in required_phrases:
                if phrase in full_text:
                    print(f"PASS: Found instruction '{phrase}'")
                else:
                    self.fail(f"FAIL: Missing instruction '{phrase}' in Agent Prompt")

if __name__ == '__main__':
    unittest.main()
