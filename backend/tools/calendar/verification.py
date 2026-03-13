import json
from backend.models_db import Integration

class CalendarVerification:
    @staticmethod
    def check_permission(db, workspace_id: int, permission_type: str) -> bool:
        """
        Check if the workspace has the required permission enabled in Google Calendar integration.
        permission_type: 'view', 'edit', 'delete'
        """
        try:
            integration = db.query(Integration).filter(
                Integration.workspace_id == workspace_id,
                Integration.provider == "google_calendar",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return False
                
            if not integration.settings:
                return True
                
            settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
            
            key_map = {
                "view": "can_view_own_events",
                "edit": "can_edit_own_events",
                "delete": "can_delete_own_events"
            }
            
            key = key_map.get(permission_type)
            if not key: return False
            
            return settings.get(key, False)
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False
