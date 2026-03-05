import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

class KnowledgeBaseService:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "supaagent-1024")
        
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

        # Embedding Service Initialization
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if self.mistral_api_key or self.openrouter_key:
             from backend.lib.ai_client import get_ai_client
             # We use the generic AI client which is Mistral-compatible
             try:
                 self.ai_client, _ = get_ai_client(async_mode=False)
                 self.embedding_model = "mistral-embed" if self.mistral_api_key else "mistralai/mistral-embed"
                 self.embedding_dim = 1024
             except:
                 self.ai_client = None
        else:
             print("CRITICAL: Mistral API Key not found. Knowledge Base disabled.")
             self.ai_client = None

    def embed_text(self, text: str) -> List[float]:
        if not self.ai_client:
            print("Warning: Embedding client not initialized. returning mock vector.")
            return [0.0] * 1024 # Mock embedding (defaulting to 1024 to match likely new index)
        
        import time
        max_retries = 3
        
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                # Prepare arguments based on provider
                kwargs = {
                    "input": text,
                    "model": self.embedding_model
                }
                # Mistral embeddings are fixed at 1024
                response = self.ai_client.embeddings.create(**kwargs)
                return response.data[0].embedding
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "rate_limit" in error_str.lower() or "insufficient_quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"Rate limit or Quota hit, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"Rate limit exceeded after {max_retries} attempts, returning empty embedding")
                        return [0.0] * self.embedding_dim  # Return empty embedding to allow conversation to continue
                else:
                    return [0.0] * self.embedding_dim # Graceful failure for all embedding errors
        
        # Fallback if all retries failed
        return [0.0] * 1024

    def upsert_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None, workspace_id: str = None, source_id: str = None):
        if not self.index:
            print(f"Skipping upsert for {doc_id}: Pinecone not initialized.")
            return

        embedding = self.embed_text(text)
        if metadata is None:
            metadata = {}
        
        # Add workspace_id and source_id to metadata for filtering
        if workspace_id:
            metadata["workspace_id"] = workspace_id
        if source_id:
            metadata["source_id"] = source_id
        
        metadata["text"] = text
        
        # Ensure metadata values are primitives for Pinecone
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            elif isinstance(v, list):
                # Pinecone supports list of strings
                if v and isinstance(v[0], str):
                    clean_metadata[k] = v
                else:
                    clean_metadata[k] = str(v)
            else:
                clean_metadata[k] = str(v)
        
        self.index.upsert(vectors=[(doc_id, embedding, clean_metadata)])

    def delete_document(self, doc_id: str):
        if not self.index:
            return
        try:
            self.index.delete(ids=[doc_id])
        except Exception as e:
            print(f"Error deleting from Pinecone: {e}")
    
    def delete_by_source(self, source_id: str):
        """Delete all documents for a specific source"""
        if not self.index:
            return
        try:
            # Pinecone doesn't support delete by metadata filter directly
            # This would require fetching all IDs first, then deleting
            # For now, just log a warning
            print(f"Warning: delete_by_source not fully implemented. Source: {source_id}")
        except Exception as e:
            print(f"Error deleting source documents: {e}")

    def search(self, query: str, top_k: int = 3, filter: Dict[str, Any] = None, workspace_id: str = None) -> List[Dict[str, Any]]:
        if not self.index:
            return []

        embedding = self.embed_text(query)
        
        query_args = {
            "vector": embedding,
            "top_k": top_k,
            "include_metadata": True
        }
        
        # Build filter with workspace_id if provided
        if workspace_id:
            if filter is None:
                filter = {}
            filter["workspace_id"] = workspace_id
        
        if filter:
            query_args["filter"] = filter
            
        try:
            results = self.index.query(**query_args)
            return [match.metadata for match in results.matches]
        except Exception as e:
            if "dimension" in str(e).lower():
                print("DEBUG: Knowledge Base dimension mismatch (1024 vs 512). Search disabled until re-sync.")
            else:
                print(f"DEBUG: Knowledge Base search error: {e}")
            return []

