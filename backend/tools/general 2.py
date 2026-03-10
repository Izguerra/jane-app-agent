import logging
import random
from livekit.agents import llm
from backend.services import get_kb_service

logger = logging.getLogger("general-tools")

class GeneralTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    @llm.function_tool(description="Search the knowledge base for information about the business, policies, or specific documents.")
    def search_knowledge_base(self, query: str) -> str:
        """
        Search the knowledge base for relevant documents.
        Args:
            query: The search query.
        """
        try:
            kb_service = get_kb_service()
            # Pass workspace_id if KB service supports multi-tenancy (assumed yes)
            results = kb_service.search(query, top_k=3) # Add workspace_id filter if supported
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            # Format results
            context = "\n\n".join([f"Source: {res.get('filename', 'Unknown')}\nContent: {res.get('text', '')}" for res in results])
            return context
        except Exception as e:
            logger.error(f"KB Search Error: {e}")
            return f"Error searching knowledge base: {str(e)}"

    @llm.function_tool(description="Get the current weather for a specific location")
    def get_weather(self, location: str) -> str:
        """
        Get the current weather for a location.
        Args:
            location: The city or region to get weather for.
        """
        # Mock weather data for demonstration
        conditions = ["sunny", "cloudy", "rainy", "snowy"]
        temps = range(10, 30)
        
        weather = {
            "location": location,
            "temperature": random.choice(temps),
            "condition": random.choice(conditions),
            "unit": "Celsius"
        }
        
        return f"The weather in {location} is {weather['condition']} with a temperature of {weather['temperature']} degrees {weather['unit']}."

    @llm.function_tool(description="Check the status of a user's application")
    def check_application_status(self, application_id: str) -> str:
        """
        Check the status of a credit application.
        Args:
            application_id: The ID of the application to check.
        """
        # Mock status check
        statuses = ["pending", "approved", "rejected", "under_review"]
        status = random.choice(statuses)
        
        return f"Application {application_id} is currently {status}."
