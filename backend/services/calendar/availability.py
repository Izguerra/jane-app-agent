import json
from datetime import datetime, timedelta

class CalendarAvailability:
    @staticmethod
    def get_free_slots(db, workspace_id, date, list_events_fn):
        from backend.models_db import Workspace
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        
        # 1. Resolve Business Hours
        if not workspace or not workspace.business_hours:
            open_time = datetime.strptime("09:00", "%H:%M").time()
            close_time = datetime.strptime("17:00", "%H:%M").time()
        else:
            try:
                business_hours = json.loads(workspace.business_hours)
            except:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                business_hours = {day: workspace.business_hours for day in days}
            
            day_name = date.strftime("%A")
            hours = business_hours.get(day_name) or business_hours.get(day_name.lower())
            
            if not hours:
                open_time = datetime.strptime("09:00", "%H:%M").time()
                close_time = datetime.strptime("17:00", "%H:%M").time()
            elif isinstance(hours, str):
                if hours.lower() == "closed": return [f"Closed on {day_name}"]
                try:
                    parts = hours.split(" - ")
                    open_time = datetime.strptime(parts[0].strip(), "%I:%M %p").time()
                    close_time = datetime.strptime(parts[1].strip(), "%I:%M %p").time()
                except:
                    open_time, close_time = datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()
            elif isinstance(hours, dict):
                if not hours.get("open") or not hours.get("close"): return [f"Closed on {day_name}"]
                open_time = datetime.strptime(hours["open"], "%H:%M").time()
                close_time = datetime.strptime(hours["close"], "%H:%M").time()
            else:
                open_time, close_time = datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()

        # 2. Get Events for the Day
        start_of_day = date.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)
        end_of_day = date.replace(hour=close_time.hour, minute=close_time.minute, second=0, microsecond=0)
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = date.replace(hour=23, minute=59, second=59)
        events = list_events_fn(workspace_id, day_start, day_end)

        # 3. Calculate Free Slots
        free_slots = []
        current_slot = start_of_day
        while current_slot < end_of_day:
            slot_end = current_slot + timedelta(hours=1)
            if slot_end > end_of_day: break
            
            is_busy = False
            for event in events:
                evt_start = datetime.fromisoformat(event['start']) if isinstance(event['start'], str) else event['start']
                evt_end = datetime.fromisoformat(event['end']) if isinstance(event['end'], str) else event['end']
                evt_start, evt_end = evt_start.replace(tzinfo=None), evt_end.replace(tzinfo=None)
                if current_slot < evt_end and slot_end > evt_start:
                    is_busy = True
                    break
            
            if not is_busy:
                free_slots.append(f"{current_slot.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}")
            current_slot = slot_end

        return free_slots if free_slots else ["No available slots for this date."]
