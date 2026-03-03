import os
from typing import Optional
from sqlalchemy.orm import Session
from backend.models_db import WorkspaceLLMConfig
from backend.lib.id_service import IdService

class LLMProviderService:
    @staticmethod
    def get_config(db: Session, workspace_id: str) -> Optional[WorkspaceLLMConfig]:
        return db.query(WorkspaceLLMConfig).filter(WorkspaceLLMConfig.workspace_id == workspace_id).first()

    @staticmethod
    def save_config(db: Session, workspace_id: str, data: dict) -> WorkspaceLLMConfig:
        config = db.query(WorkspaceLLMConfig).filter(WorkspaceLLMConfig.workspace_id == workspace_id).first()
        
        if not config:
            config = WorkspaceLLMConfig(
                id=IdService.generate("lcfg"),
                workspace_id=workspace_id
            )
            db.add(config)
        
        config.provider = data.get("provider", "openai")
        config.model = data.get("model", "gpt-4o")
        config.is_byok = data.get("is_byok", False)
        if data.get("api_key"):
            # TODO: Add real AES encryption here for production security.
            # For now, we store in the encrypted-at-rest DB.
            config.api_key_encrypted = data.get("api_key")
            
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def get_llm_client_params(db: Session, workspace_id: str):
        """Returns API key and model for LLM client initialization"""
        config = LLMProviderService.get_config(db, workspace_id)
        if config and config.is_byok and config.api_key_encrypted:
            return {
                "api_key": config.api_key_encrypted,
                "model": config.model,
                "provider": config.provider
            }
        
        # Default to SupaAgent managed
        return {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o",
            "provider": "openai"
        }
