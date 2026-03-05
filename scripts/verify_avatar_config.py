import os
import sys

# Ensure root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def check_env():
    print("Checking Environment Variables...")
    required = ["TAVUS_API_KEY", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "LIVEKIT_URL", "GOOGLE_API_KEY"]
    for var in required:
        val = os.getenv(var)
        status = "✅ Present" if val else "❌ Missing"
        print(f"  {var}: {status}")

def check_db():
    print("\nChecking Database Schema...")
    try:
        from backend.database import SessionLocal
        from backend.models_db import Communication, Integration
        
        db = SessionLocal()
        
        # Check Integration Table
        print("  Querying Integrations table...")
        integs = db.query(Integration).filter(Integration.provider == 'tavus').all()
        print(f"  Found {len(integs)} Tavus integrations enabled.")
        
        # Check Communication Table Column (channel)
        print("  Checking Communication 'channel' column support...")
        try:
             # Just a dummy query to ensure column exists
             db.query(Communication).filter(Communication.channel == 'video_avatar').first()
             print("  ✅ Communication.channel column handles 'video_avatar'")
        except Exception as e:
            print(f"  ❌ Communication.channel check failed: {e}")
            
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def check_services():
    print("\nChecking Service Imports...")
    try:
        from backend.services.tavus_service import TavusService
        print("  ✅ TavusService imported")
        
        # Check method existence
        if getattr(TavusService, "create_conversation", None):
             print("  ✅ TavusService.create_conversation exists")
        else:
             print("  ❌ TavusService.create_conversation MISSING")
             
    except ImportError as e:
        print(f"  ❌ Failed to import TavusService: {e}")

    try:
        from livekit.plugins import google
        print("  ✅ livekit.plugins.google imported")
        if hasattr(google, "LLM") and hasattr(google, "TTS"):
             print("  ✅ Google LLM and TTS classes exist")
        else:
             print("  ❌ Google LLM/TTS classes MISSING")
    except ImportError as e:
         print(f"  ❌ Failed to import livekit.plugins.google: {e}")

    try:
        from backend.avatar_agent import entrypoint
        print("  ✅ Avatar Agent Entrypoint importable")
    except ImportError as e:
        print(f"  ❌ Failed to import Avatar Agent: {e}")

if __name__ == "__main__":
    print("=== AI Avatar Configuration Check ===\n")
    check_env()
    check_services()
    check_db()
    print("\n=== Check Complete ===")
