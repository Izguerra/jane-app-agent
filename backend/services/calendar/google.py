import json
from datetime import datetime
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.security import decrypt_text

class GoogleCalendarProvider:
    @staticmethod
    def get_service(integration):
        creds_data = json.loads(decrypt_text(integration.credentials))
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes")
        )
        return build('calendar', 'v3', credentials=creds)

    @classmethod
    def fetch_events(cls, integration, start, end):
        try:
            service = cls.get_service(integration)
            tz = ZoneInfo("America/Toronto")
            if start.tzinfo is None: start = start.replace(tzinfo=tz)
            if end.tzinfo is None: end = end.replace(tzinfo=tz)
            
            events_result = service.events().list(
                calendarId='primary', timeMin=start.isoformat(), timeMax=end.isoformat(),
                singleEvents=True, orderBy='startTime'
            ).execute()
            
            return [{
                "id": e['id'], "title": e.get('summary', 'No Title'),
                "start": e['start'].get('dateTime', e['start'].get('date')),
                "end": e['end'].get('dateTime', e['end'].get('date')),
                "provider": "google_calendar", "description": e.get('description', '')
            } for e in events_result.get('items', [])]
        except Exception as e:
            print(f"Error fetching Google events: {e}")
            return []

    @classmethod
    def create_event(cls, integration, title, start, end, description, attendees=None):
        service = cls.get_service(integration)
        tz = ZoneInfo("America/Toronto")
        if start.tzinfo is None: start = start.replace(tzinfo=tz)
        if end.tzinfo is None: end = end.replace(tzinfo=tz)
        
        event = {
            'summary': title, 'description': description,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'America/Toronto'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'America/Toronto'}
        }
        if attendees: event['attendees'] = [{'email': email} for email in attendees]
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "id": event['id'], "title": event.get('summary'),
            "start": event['start'].get('dateTime'), "end": event['end'].get('dateTime'),
            "provider": "google_calendar", "status": "confirmed"
        }

    @classmethod
    def update_event(cls, integration, event_id, start=None, end=None, title=None, description=None):
        service = cls.get_service(integration)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if title: event['summary'] = title
        if description: event['description'] = description
        if start and end:
            tz = ZoneInfo("America/Toronto")
            if start.tzinfo is None: start = start.replace(tzinfo=tz)
            if end.tzinfo is None: end = end.replace(tzinfo=tz)
            event['start'] = {'dateTime': start.isoformat(), 'timeZone': 'America/Toronto'}
            event['end'] = {'dateTime': end.isoformat(), 'timeZone': 'America/Toronto'}
            
        updated = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return {
            "id": updated['id'], "title": updated.get('summary'),
            "start": updated['start'].get('dateTime'), "end": updated['end'].get('dateTime'),
            "provider": "google_calendar", "status": "confirmed"
        }

    @classmethod
    def delete_event(cls, integration, event_id):
        service = cls.get_service(integration)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
