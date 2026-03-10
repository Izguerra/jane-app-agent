from typing import List, Dict, Any, Optional
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io
import json
import logging
from backend.models_db import Integration
from backend.security import decrypt_text

logger = logging.getLogger("drive-service")

class GoogleDriveService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int) -> Optional[Integration]:
        return self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.provider == "google_drive",
            Integration.is_active == True
        ).first()

    def _get_service(self, integration: Integration):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        if not integration.credentials:
            raise Exception("No credentials found for Drive integration")

        creds_data = json.loads(decrypt_text(integration.credentials) if isinstance(integration.credentials, str) else json.dumps(integration.credentials))
        
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes")
        )
        
        return build('drive', 'v3', credentials=creds)

    def _check_permission(self, integration: Integration, permission: str) -> bool:
        if not integration.settings:
            return False
        settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
        return settings.get(permission, False)

    def list_files(self, workspace_id: int, folder_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Drive integration not found")

        if not self._check_permission(integration, "can_list_files"):
            raise Exception("Permission denied: Cannot list files")

        try:
            service = self._get_service(integration)
            query = "trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = service.files().list(
                q=query,
                pageSize=limit,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, createdTime, size)"
            ).execute()
            
            items = results.get('files', [])
            files = []
            for item in items:
                files.append({
                    "id": item['id'],
                    "name": item['name'],
                    "mimeType": item['mimeType'],
                    "link": item.get('webViewLink'),
                    "created": item.get('createdTime'),
                    "size": item.get('size'),
                    "provider": "google_drive"
                })
            return files
        except Exception as e:
            logger.error(f"Error listing Drive files: {e}")
            raise e

    def read_file(self, workspace_id: int, file_id: str) -> str:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Drive integration not found")

        if not self._check_permission(integration, "can_read_files"):
            raise Exception("Permission denied: Cannot read files")

        try:
            service = self._get_service(integration)
            
            # Get metadata first to check type
            file_meta = service.files().get(fileId=file_id).execute()
            mime_type = file_meta.get('mimeType')
            
            # Export Google Docs/Sheets to plain text/CSV
            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(fileId=file_id, mimeType='text/plain')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = service.files().export_media(fileId=file_id, mimeType='text/csv')
            else:
                # Binary or text file
                request = service.files().get_media(fileId=file_id)
                
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            return file_content.getvalue().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error reading Drive file: {e}")
            raise e

    def upload_file(self, workspace_id: int, name: str, content: str, mime_type: str = 'text/plain') -> Dict[str, Any]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Drive integration not found")

        if not self._check_permission(integration, "can_upload_files"):
            raise Exception("Permission denied: Cannot upload files")

        try:
            service = self._get_service(integration)
            
            file_metadata = {'name': name}
            media = MediaIoBaseUpload(io.BytesIO(content.encode('utf-8')), mimetype=mime_type, resumable=True)
            
            file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            
            return {
                "id": file.get('id'),
                "link": file.get('webViewLink'),
                "provider": "google_drive"
            }
        except Exception as e:
            logger.error(f"Error uploading Drive file: {e}")
            raise e

    def search_files(self, workspace_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Drive integration not found")

        if not self._check_permission(integration, "can_search_files"):
            raise Exception("Permission denied: Cannot search files")

        try:
            service = self._get_service(integration)
            
            # Simple name search or full text if supported
            q = f"name contains '{query}' and trashed = false"
            
            results = service.files().list(
                q=q,
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            files = []
            for item in items:
                files.append({
                    "id": item['id'],
                    "name": item['name'],
                    "mimeType": item['mimeType'],
                    "link": item.get('webViewLink'),
                    "provider": "google_drive"
                })
            return files
        except Exception as e:
            logger.error(f"Error searching Drive files: {e}")
            raise e
