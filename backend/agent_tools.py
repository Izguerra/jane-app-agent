import random
from livekit.agents import llm

class AgentTools:
    @llm.function_tool(
        description="Get the current weather for a specific location",
    )
    async def get_weather(self, location: str):
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

    @llm.function_tool(
        description="Check the status of a user's application",
    )
    async def check_application_status(self, application_id: str):
        """
        Check the status of a credit application.
        Args:
            application_id: The ID of the application to check.
        """
        # Mock status check
        statuses = ["pending", "approved", "rejected", "under_review"]
        status = random.choice(statuses)
        
        return f"Application {application_id} is currently {status}."

    @llm.function_tool(
        description="Get information about the business (name, address, phone, hours, services, etc.)",
    )
    async def get_business_info(self):
        """
        Get comprehensive information about the business including contact details, hours, and services.
        """
        import requests
        try:
            response = requests.get("http://127.0.0.1:8000/clinics/context")
            if response.status_code == 200:
                data = response.json()
                
                # Format the response
                info = f"Business Name: {data.get('name', 'N/A')}\n"
                info += f"Address: {data.get('address', 'N/A')}\n"
                info += f"Phone: {data.get('phone', 'N/A')}\n"
                info += f"Website: {data.get('website', 'N/A')}\n"
                
                if data.get('description'):
                    info += f"\nDescription: {data['description']}\n"
                
                if data.get('services'):
                    info += f"\nServices: {data['services']}\n"
                
                if data.get('business_hours'):
                    info += "\nBusiness Hours:\n"
                    for day, hours in data['business_hours'].items():
                        if isinstance(hours, dict):
                            info += f"  {day.capitalize()}: {hours.get('open', 'Closed')} - {hours.get('close', 'Closed')}\n"
                
                return info
            else:
                return "Unable to retrieve business information at this time."
        except Exception as e:
            return f"Error retrieving business information: {str(e)}"

    @llm.function_tool(
        description="Search the business knowledge base for answers to specific questions (FAQ, documents, etc.)",
    )
    async def search_knowledge_base(self, query: str):
        """
        Search the business knowledge base including FAQ and uploaded documents.
        Args:
            query: The question or topic to search for.
        """
        import requests
        try:
            response = requests.get("http://127.0.0.1:8000/clinics/context")
            if response.status_code == 200:
                data = response.json()
                
                # Search FAQ
                faq = data.get('faq', [])
                for item in faq:
                    if query.lower() in item.get('question', '').lower():
                        return f"Q: {item['question']}\nA: {item['answer']}"
                
                # Search documents (simple keyword match)
                documents = data.get('documents', [])
                for doc in documents:
                    content = doc.get('content', '')
                    if query.lower() in content.lower():
                        # Return relevant snippet
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if query.lower() in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                snippet = '\n'.join(lines[start:end])
                                return f"From {doc['filename']}:\n{snippet}"
                
                return "No specific information found in the knowledge base for that query. Try asking about business hours, services, or contact information."
            else:
                return "Unable to search knowledge base at this time."
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"

