from livekit.agents import llm
import random

class SearchMixin:
    @llm.function_tool(description="Search the knowledge base for information.")
    async def search_knowledge_base(self, query: str):
        """
        Search the internal knowledge base for specific documents or information.
        
        Args:
            query: The search query or question to find in the knowledge base.
        """
        await self._play_filler(random.choice(["Checking knowledge base...", "Looking that up..."]))
        from backend.knowledge_base import KnowledgeBaseService
        try:
            kb = KnowledgeBaseService()
            res = kb.search(query, workspace_id=self.workspace_id)
            if not res: return "No information found in the knowledge base."
            return "\n\n".join([f"Source: {r.get('filename')}\nContent: {r.get('text')}" for r in res])
        except Exception as e: return f"Error searching knowledge base: {str(e)}"

    @llm.function_tool(description="Search the web for real-time information.")
    async def web_search(self, query: str, max_results: int = 5):
        """
        Search the internet for real-time information, news, or general knowledge.
        
        Args:
            query: The search query to look up on the web.
            max_results: The maximum number of search results to return (default 5).
        """
        await self._play_filler("Searching the web...")
        try:
            from backend.tools.web_search import get_web_search_tool
            tool = get_web_search_tool(workspace_id=self.workspace_id)
            results = tool.search(query, max_results=max_results)
            return str(results)
        except Exception as e: return f"Error during web search: {str(e)}"
