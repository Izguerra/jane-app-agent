
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from backend.services.outlook_service import OutlookService
    from backend.services.icloud_service import ICloudService
    from backend.services.calendar_service import CalendarService
    print("Services imported successfully.")
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
