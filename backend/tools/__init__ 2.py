"""
Backend Tools Package

Centralized tool exports for agent functionality.
"""

# Web Search Tools (requires TAVILY_API_KEY)
from backend.tools.web_search import (
    web_search,
    search_job_listings,
    WebSearchTool,
    get_web_search_tool
)

# Worker Dispatch Tools
from backend.tools.worker_tools import WorkerTools

# Class-based tools (use these by instantiating)
from backend.tools.appointments import AppointmentTools

__all__ = [
    # Web Search
    "web_search",
    "search_job_listings",
    "WebSearchTool",
    "get_web_search_tool",
    # Workers
    "WorkerTools",
    # Classes
    "AppointmentTools"
]
