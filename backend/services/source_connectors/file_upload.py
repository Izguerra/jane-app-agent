import os
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import PyPDF2
import csv

from .base_connector import BaseConnector
from backend.knowledge_base import KnowledgeBaseService

class FileUploadConnector(BaseConnector):
    """Connector for processing uploaded files (PDF, TXT, CSV, MD)"""
    
    def __init__(self, source_id: str, workspace_id: str, config: Dict[str, Any]):
        super().__init__(source_id, workspace_id, config)
        self.kb_service = KnowledgeBaseService()
        self.supported_extensions = ['.pdf', '.txt', '.csv', '.md']
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate file upload configuration"""
        if 'file_path' not in self.config:
            return False, "file_path is required"
        
        file_path = self.config['file_path']
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_extensions:
            return False, f"Unsupported file type: {ext}. Supported: {', '.join(self.supported_extensions)}"
        
        return True, None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test if file is accessible and readable"""
        file_path = self.config['file_path']
        
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            if not os.access(file_path, os.R_OK):
                return False, f"File is not readable: {file_path}"
            
            file_size = os.path.getsize(file_path)
            return True, f"File accessible ({file_size} bytes)"
        
        except Exception as e:
            return False, f"Error accessing file: {str(e)}"
    
    async def sync(self) -> Dict[str, Any]:
        """Process and index the uploaded file"""
        file_path = self.config['file_path']
        storage_type = self.config.get('storage_type', 'local')
        original_filename = self.config.get('original_filename', os.path.basename(file_path))
        ext = Path(original_filename).suffix.lower()
        
        documents_processed = 0
        documents_added = 0
        documents_failed = 0
        errors = []
        
        temp_file_path = None
        
        try:
            # Handle S3/Remote files
            if storage_type == 's3':
                from backend.services.storage_service import get_storage_service
                storage = get_storage_service()
                
                # Create temp file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    temp_file_path = tmp.name
                
                # Download from S3
                if not storage.download_file(file_path, temp_file_path):
                    raise Exception(f"Failed to download file from storage: {file_path}")
                
                processing_path = temp_file_path
            else:
                # Local file
                processing_path = file_path
                if not os.path.exists(processing_path):
                     raise Exception(f"File not found: {processing_path}")

            # Extract text based on file type
            if ext == '.pdf':
                text = self._extract_pdf(processing_path)
            elif ext == '.txt':
                text = self._extract_txt(processing_path)
            elif ext == '.md':
                text = self._extract_txt(processing_path)  # Markdown is plain text
            elif ext == '.csv':
                text = self._extract_csv(processing_path)
            else:
                return {
                    'documents_processed': 0,
                    'documents_added': 0,
                    'documents_updated': 0,
                    'documents_failed': 1,
                    'errors': [f"Unsupported file type: {ext}"]
                }
            
            if not text or len(text) < 10:
                return {
                    'documents_processed': 0,
                    'documents_added': 0,
                    'documents_updated': 0,
                    'documents_failed': 1,
                    'errors': ["No content extracted from file"]
                }
            
            # Generate document ID from filename/source
            # Use original filename hash + source_id to ensure uniqueness but consistency
            file_hash = hashlib.md5(original_filename.encode()).hexdigest()[:12]
            doc_id = self._generate_doc_id(file_hash)
            
            # Store in knowledge base
            self.kb_service.upsert_document(
                doc_id=doc_id,
                text=text,
                metadata={
                    'filename': original_filename,
                    'file_type': ext,
                    'file_size': os.path.getsize(processing_path),
                    'source_type': 'file_upload',
                    'storage_key': file_path if storage_type == 's3' else None,
                    'uploaded_at': datetime.now().isoformat()
                },
                workspace_id=self.workspace_id,
                source_id=self.source_id
            )
            
            documents_processed = 1
            documents_added = 1
        
        except Exception as e:
            documents_failed = 1
            errors.append(f"Error processing file: {str(e)}")
            
        finally:
            # Cleanup temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        return {
            'documents_processed': documents_processed,
            'documents_added': documents_added,
            'documents_updated': 0,
            'documents_failed': documents_failed,
            'errors': errors
        }
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
        return text.strip()
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT/MD file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        text_lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text_lines.append(' | '.join(row))
        except Exception as e:
            raise Exception(f"Error extracting CSV: {str(e)}")
        return '\n'.join(text_lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get file upload status"""
        return {
            'status': 'active',
            'last_synced_at': datetime.now(),
            'document_count': 1,
            'error_message': None
        }
