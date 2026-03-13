from .calendar.read import CalendarReadTools
from .calendar.write import CalendarWriteTools

class CalendarTools:
    def __init__(self, workspace_id: int, customer_id: str = None):
        self.workspace_id = workspace_id
        self.customer_id = customer_id
        self.read_tools = CalendarReadTools(workspace_id)
        self.write_tools = CalendarWriteTools(workspace_id)

    def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None) -> str:
        return self.read_tools.list_appointments(date, verify_name, verify_phone, verify_email)

    def get_availability(self, date: str = None) -> str:
        return self.read_tools.get_availability(date)

    def create_appointment(self, title: str, start_time: str, duration_minutes: int = 60, description: str = "", attendee_name: str = None, attendee_email: str = None, attendee_phone: str = None) -> str:
        return self.write_tools.create_appointment(title, start_time, duration_minutes, description, attendee_name, attendee_email, attendee_phone)

    def cancel_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str) -> str:
        return self.write_tools.cancel_appointment(appointment_id, verify_name, verify_phone, verify_email)

    def edit_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str, new_start_time: str = None, new_duration_minutes: int = None, new_title: str = None, new_description: str = None) -> str:
        return self.write_tools.edit_appointment(appointment_id, verify_name, verify_phone, verify_email, new_start_time, new_duration_minutes, new_title, new_description)
