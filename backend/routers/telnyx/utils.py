import os
from datetime import datetime

def log_debug(msg):
    try:
        log_file = os.path.join(os.getcwd(), "backend/debug_webhook_telnyx.log")
        with open(log_file, "a") as f:
            f.write(f"DEBUG [{datetime.now().isoformat()}]: {msg}\n")
    except Exception as e:
        print(f"FAILED TO LOG: {e}")
