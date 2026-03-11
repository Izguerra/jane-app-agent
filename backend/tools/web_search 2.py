"""
Web Search Tool

Provides web search capabilities for autonomous worker agents using Tavily API.
Optimized for AI agent use cases with structured, relevant results.
"""

import os
from typing import Optional, List, Dict, Any

# Try to import agents SDK, but provide fallback for testing
try:
    from agents import function_tool
except ImportError:
    # Fallback decorator when agents SDK is not available
    def function_tool(func):
        """Fallback decorator when agents SDK is not available."""
        return func


# Check if tavily is available
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None


from backend.services.integration_service import IntegrationService

class WebSearchTool:
    """
    Web search tool for AI agents using Tavily API.
    
    Tavily is optimized for AI/LLM use cases, providing clean, 
    structured search results without raw HTML.
    
    Usage:
        tool = WebSearchTool(workspace_id="ws_123")
        results = tool.search("job openings for software engineers in NYC")
    """
    
    def __init__(self, workspace_id: Optional[str] = None):
        self.workspace_id = workspace_id
        self.api_key = IntegrationService.get_provider_key(
            workspace_id=self.workspace_id,
            provider="tavily",
            env_fallback="TAVILY_API_KEY"
        )
        self._client = None
        
        if not self.api_key:
            print("Warning: TAVILY_API_KEY not set. Web search will be unavailable.")

    def is_available(self) -> bool:
        """Check if web search is available (API key configured)."""
        return bool(self.client)
    
    @property
    def client(self) -> Optional['TavilyClient']:
        """Lazy-load Tavily client."""
        if self._client is None and self.api_key and TAVILY_AVAILABLE:
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        topic: str = "general"
    ) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: Search query string
            search_depth: "basic" or "advanced" (more thorough)
            max_results: Maximum number of results (1-10)
            include_answer: Include AI-generated answer summary
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
            topic: "general", "news", or "finance"
            
        Returns:
            Dict with 'answer' (AI summary) and 'results' (list of sources)
        """
        if not self.client:
            return {
                "error": "Web search unavailable. TAVILY_API_KEY not configured.",
                "answer": None,
                "results": []
            }
        
        try:
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                topic=topic
            )
            
            return {
                "answer": response.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content"),
                        "score": r.get("score")
                    }
                    for r in response.get("results", [])
                ]
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "answer": None,
                "results": []
            }
    
    def search_news(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search for recent news articles."""
        return self.search(
            query=query,
            topic="news",
            max_results=max_results,
            search_depth="advanced"
        )
    
    def search_jobs(
        self,
        job_title: str,
        location: str = "Remote",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for job listings.
        
        Note: For better results, this searches job boards specifically.
        """
        query = f"{job_title} jobs {location}"
        
        job_domains = [
            "linkedin.com",
            "indeed.com",
            "glassdoor.com",
            "lever.co",
            "greenhouse.io",
            "workday.com",
            "wellfound.com"
        ]
        
        return self.search(
            query=query,
            include_domains=job_domains,
            max_results=max_results,
            search_depth="advanced"
        )


# =========================================================================
# Function Tool Wrapper for Agents SDK
# =========================================================================

# Global instance for function tool
_web_search_tool = None

def get_web_search_tool() -> WebSearchTool:
    """Get or create singleton WebSearchTool instance."""
    global _web_search_tool
    if _web_search_tool is None:
        _web_search_tool = WebSearchTool()
    return _web_search_tool


@function_tool
def web_search(query: str, max_results: int = 5, topic: str = "general") -> dict:
    """
    Search the web for information using Tavily.
    
    Args:
        query: The search query to find information about
        max_results: Number of results to return (1-10, default 5)
        topic: Type of search - "general", "news", or "finance"
        
    Returns:
        A dict with 'answer' (AI summary) and 'results' (list of sources)
    """
    tool = get_web_search_tool()
    return tool.search(
        query=query,
        max_results=max_results,
        topic=topic,
        include_answer=True
    )


@function_tool
def search_job_listings(
    job_title: str,
    location: str = "Remote",
    max_results: int = 10
) -> dict:
    """
    Search job boards for job listings.
    
    Args:
        job_title: The job title to search for (e.g., "Software Engineer")
        location: Location preference (e.g., "New York", "Remote")
        max_results: Maximum number of job listings to return
        
    Returns:
        A dict with job listing results from major job boards
    """
    tool = get_web_search_tool()
    return tool.search_jobs(
        job_title=job_title,
        location=location,
        max_results=max_results
    )
