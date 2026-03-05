import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Set up test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.agent import AgentManager
from backend.models_db import MCPServer, Base
from backend.database import engine, SessionLocal

class TestMCPE2E(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.workspace_id = "test_ws"
        self.team_id = "test_team"
        
        # Create a mock MCP server in the DB
        self.server = MCPServer(
            id="mcp_123",
            workspace_id=self.workspace_id,
            name="TestMCP",
            url="https://mock-mcp.com/sse",
            transport="sse",
            status="connected",
            is_active=True,
            tools_cache=[
                {
                    "name": "get_secret_info",
                    "description": "Returns secret information"
                }
            ]
        )
        self.db.add(self.server)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    async def test_mcp_tool_discovery_and_execution(self):
        """Test that MCP tools are discovered and can be executed by the agent."""
        manager = AgentManager()
        
        # We need to mock the chat method's data fetching to use our test DB
        with patch("backend.agent.SessionLocal", return_value=self.db), \
             patch("httpx.AsyncClient") as MockClient:
            
            # Mock the HTTP response for the tool call
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": "The secret is 42"}]
                }
            }
            
            # AsyncMock for the post method
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            # Test message that should trigger tool lookup
            # We bypass the actual message processing and verify _create_agent behavior
            settings = {
                "name": "SupaAgent",
                "business_name": "Test Office",
                "soul": "You are a helpful assistant."
            }
            
            # Create agent with tools gathered from our mock DB
            # Note: We need to ensure _create_agent is called with mcp_servers
            # We can test the chat() flow directly which gathers the servers
            
            # We mock the LLM response to simulate calling the tool
            with patch("backend.agent.Agent") as MockAgnoAgent:
                # Set up the mock agent instance and its arun method
                mock_agent_instance = MockAgnoAgent.return_value
                mock_agent_instance.arun = AsyncMock()
                mock_agent_instance.arun.return_value = MagicMock(content="The secret is 42")

                # Test message that should trigger tool lookup
                await manager.chat(
                    message="Tell me the secret",
                    workspace_id=self.workspace_id,
                    team_id=self.team_id,
                    db=self.db
                )
                
                # Check call arguments
                call_args = MockAgnoAgent.call_args
                tools = call_args.kwargs.get("tools", [])
                
                # Verify our dynamic MCP tool is in the list
                mcp_tool_names = [t.__name__ for t in tools if callable(t)]
                self.assertIn("mcp_testmcp_get_secret_info", mcp_tool_names)
                
                # Now test the tool execution itself
                mcp_tool = next(t for t in tools if t.__name__ == "mcp_testmcp_get_secret_info")
                result = await mcp_tool(query="test")
                
                self.assertEqual(result, "The secret is 42")
                
                # Verify HTTP call parameters
                mock_client_instance.post.assert_called_once()
                call_json = mock_client_instance.post.call_args.kwargs.get("json")
                self.assertEqual(call_json["method"], "tools/call")
                self.assertEqual(call_json["params"]["name"], "get_secret_info")

        print("✅ SUCCESS: MCP tool discovery and execution verified.")

if __name__ == "__main__":
    unittest.main()
