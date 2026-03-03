from typing import Optional, List, Dict, Any
from backend.services.google_drive_service import GoogleDriveService
from backend.database import SessionLocal
import json

class DriveTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    def list_files(self, folder_id: str = None, limit: int = 10) -> str:
        """
        List files in Google Drive.
        :param folder_id: Optional folder ID to list contents of
        :param limit: Max files to return
        :return: JSON string of files
        """
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            files = service.list_files(self.workspace_id, folder_id, limit)
            if not files:
                return "No files found."
            return json.dumps(files, indent=2)
        except Exception as e:
            return f"Error listing files: {str(e)}"
        finally:
            db.close()

    def read_file(self, file_id: str) -> str:
        """
        Read content of a file (text, doc, sheet).
        :param file_id: ID of the file
        :return: File content as string
        """
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            content = service.read_file(self.workspace_id, file_id)
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
        finally:
            db.close()

    def upload_file(self, name: str, content: str) -> str:
        """
        Upload a new text file to Drive.
        :param name: Filename
        :param content: Text content
        :return: JSON string with file details
        """
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            result = service.upload_file(self.workspace_id, name, content)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error uploading file: {str(e)}"
        finally:
            db.close()

    def search_files(self, query: str, limit: int = 10) -> str:
        """
        Search for files by name.
        :param query: Name query
        :param limit: Max results
        :return: JSON string of results
        """
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            files = service.search_files(self.workspace_id, query, limit)
            if not files:
                return f"No files found matching '{query}'."
            return json.dumps(files, indent=2)
        except Exception as e:
            return f"Error searching files: {str(e)}"
        finally:
            db.close()
