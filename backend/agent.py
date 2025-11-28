from typing import Optional, Iterator
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from backend.knowledge_base import KnowledgeBaseService
from backend.settings_store import get_settings
import os
import requests

class AgentManager:
    def __init__(self):
        self.kb = KnowledgeBaseService()
        self.model_id = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # We no longer maintain a single self.agent instance to support dynamic settings
        # and multi-tenancy.

    def _create_agent(self, settings: dict) -> Agent:
        """Create a new agent instance with the provided settings."""
        instructions = [
            "Always be polite, professional, and empathetic.",
            "Use the provided context to answer questions accurately.",
            "If the answer is not in the context, politely state that you don't have that information.",
            "Keep responses concise and relevant to the healthcare setting."
        ]
        
        # Add system prompt from settings if available
        if settings.get("prompt_template"):
             instructions.insert(0, settings["prompt_template"])

        # REMOVED: Explicit language instruction.
        # We now rely on the system prompt to instruct the agent to match the user's language dynamically.
        # if settings.get("language") and settings["language"] != "en":
        #     instructions.append(f"You must respond in {settings['language']} language.")
            
        return Agent(
            model=OpenAIChat(id=self.model_id),
            description="You are Jane, an AI assistant for a healthcare practice.",
            instructions=instructions,
            markdown=True
        )

    def chat(self, message: str, stream: bool = False) -> str | Iterator[str]:
        # 1. Fetch current settings (from DB)
        # In a real multi-tenant app, we would pass the clinic_id/user_id here
        settings = get_settings()
        
        # 2. Create agent with fresh settings
        agent = self._create_agent(settings)
        
        # 3. Retrieve relevant context from Knowledge Base
        context_docs = self.kb.search(message)
        context_text = ""
        if context_docs:
            context_text = "\n\n---\n".join([doc.get("text", "") for doc in context_docs])
        
        # 4. Fetch business profile context
        business_context = ""
        try:
            response = requests.get("http://127.0.0.1:8000/clinics/context")
            if response.status_code == 200:
                data = response.json()
                business_context = f"""
Business Information:
- Name: {data.get('name', 'N/A')}
- Address: {data.get('address', 'N/A')}
- Phone: {data.get('phone', 'N/A')}
- Website: {data.get('website', 'N/A')}
- Description: {data.get('description', '')}
- Services: {data.get('services', '')}
"""
                if data.get('business_hours'):
                    business_context += "\nBusiness Hours:\n"
                    for day, hours in data.get('business_hours', {}).items():
                        if isinstance(hours, dict):
                            business_context += f"  {day.capitalize()}: {hours.get('open', 'Closed')} - {hours.get('close', 'Closed')}\n"
                
                if data.get('faq'):
                    business_context += "\nFrequently Asked Questions:\n"
                    for item in data.get('faq', []):
                        business_context += f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}\n\n"
        except Exception as e:
            print(f"Error fetching business context: {e}")
        
        # 5. Construct the prompt with context
        full_message = message
        combined_context = business_context
        if context_text:
            combined_context += f"\n\n---\nKnowledge Base:\n{context_text}"
        
        if combined_context:
            full_message = f"""Context information is below:
---------------------
{combined_context}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {message}
"""
        
        # 5. Run the agent
        if stream:
            return agent.run(full_message, stream=True)
        else:
            response = agent.run(full_message)
            return response.content
