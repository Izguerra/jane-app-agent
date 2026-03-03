from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BaseConnector(ABC):
    """Abstract base class for all knowledge base source connectors"""
    
    def __init__(self, source_id: str, workspace_id: str, config: Dict[str, Any]):
        self.source_id = source_id
        self.workspace_id = workspace_id
        self.config = config
    
    @abstractmethod
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate the connector configuration.
        
        Returns:
            tuple: (is_valid, error_message)
                - is_valid: True if config is valid, False otherwise
                - error_message: Error message if invalid, None if valid
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to the data source.
        
        Returns:
            tuple: (is_successful, message)
                - is_successful: True if connection successful, False otherwise
                - message: Success or error message
        """
        pass
    
    @abstractmethod
    async def sync(self) -> Dict[str, Any]:
        """
        Fetch and index documents from the source.
        
        Returns:
            dict: Sync results containing:
                - documents_processed: int
                - documents_added: int
                - documents_updated: int
                - documents_failed: int
                - errors: List[str]
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the connector.
        
        Returns:
            dict: Status information containing:
                - status: str ('pending', 'syncing', 'active', 'error', 'paused')
                - last_synced_at: Optional[datetime]
                - document_count: int
                - error_message: Optional[str]
        """
        pass
    
    def _generate_doc_id(self, unique_identifier: str) -> str:
        """Generate a unique document ID"""
        return f"{self.source_id}_{unique_identifier}"
