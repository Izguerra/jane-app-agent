import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class KnowledgeBaseService:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "jane-agent")
        
        # Pinecone Initialization
        if not self.pinecone_api_key or "placeholder" in self.pinecone_api_key:
            print("Warning: PINECONE_API_KEY is not set or is a placeholder. Knowledge Base disabled.")
            self.pc = None
            self.index = None
        else:
            try:
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                self.index = self.pc.Index(self.index_name)
            except Exception as e:
                print(f"Error initializing Pinecone: {e}. Knowledge Base disabled.")
                self.pc = None
                self.index = None

        # OpenAI Initialization
        if not self.openai_api_key or "placeholder" in self.openai_api_key:
            print("Warning: OPENAI_API_KEY is not set or is a placeholder. AI features disabled.")
            self.openai_client = None
        else:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                print(f"Error initializing OpenAI: {e}. AI features disabled.")
                self.openai_client = None

    def embed_text(self, text: str) -> List[float]:
        if not self.openai_client:
            return [0.0] * 1536 # Mock embedding
        
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def upsert_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        if not self.index:
            print(f"Skipping upsert for {doc_id}: Pinecone not initialized.")
            return

        embedding = self.embed_text(text)
        if metadata is None:
            metadata = {}
        metadata["text"] = text
        
        self.index.upsert(vectors=[(doc_id, embedding, metadata)])

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.index:
            return []

        embedding = self.embed_text(query)
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        return [match.metadata for match in results.matches]
