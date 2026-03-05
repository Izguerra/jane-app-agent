
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_phase_4():
    print("Verifying Phase 4 Cleanup (Import Checks)...")
    
    errors = []
    
    # Check 1: Verify meta_webhooks imports without AgentTools
    print("\n1. Checking 'backend.routers.meta_webhooks'...")
    try:
        import backend.routers.meta_webhooks
        print("✅ 'backend.routers.meta_webhooks' imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import meta_webhooks: {e}")
        errors.append(f"meta_webhooks: {e}")
    except Exception as e:
        print(f"❌ unexpected error importing meta_webhooks: {e}")
        errors.append(f"meta_webhooks: {e}")

    # Check 2: Verify voice_agent imports without AgentTools
    print("\n2. Checking 'backend.voice_agent'...")
    try:
        # Mocking livekit to avoid runtime errors during pure import check if SDK missing
        # But assuming env handles it.
        import backend.voice_agent
        print("✅ 'backend.voice_agent' imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import voice_agent: {e}")
        errors.append(f"voice_agent: {e}")
    except Exception as e:
        print(f"❌ unexpected error importing voice_agent: {e}")
        errors.append(f"voice_agent: {e}")

    # Check 3: Verify agent_tools is GONE
    print("\n3. Verifying 'backend.agent_tools' deletion...")
    try:
        import backend.agent_tools
        print("❌ 'backend.agent_tools' still exists and was imported!")
        errors.append("agent_tools still exists")
    except ImportError:
        print("✅ 'backend.agent_tools' correctly failed to import (file deleted).")

    if errors:
        print("\n❌ Verification FAILED with errors:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("\n✅ Phase 4 Verification PASSED: System clean.")

if __name__ == "__main__":
    verify_phase_4()
