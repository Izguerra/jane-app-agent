"""
End-to-End Backend Test for Agent Context Awareness

This script tests that all wizard configuration fields are properly
injected into agent system prompts for both Standard and OpenClaw agents.
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from backend.agent import AgentManager
from backend.agents.factory import AgentFactory
from backend.database import SessionLocal
import json


def test_standard_agent_context():
    """Test that Standard Agent receives all configured context fields"""
    
    print("\n" + "="*80)
    print("TEST 1: Standard Agent Context Awareness")
    print("="*80)
    
    # Mock settings with all possible fields
    settings = {
        # Identity & Knowledge Base (Step 1)
        "agent_name": "Test Support Agent",
        "voice_id": "alloy",
        "language": "en",
        "business_name": "Acme Corporation",
        "description": "We provide premium software solutions",
        "address": "123 Tech Street, San Francisco, CA 94105",
        "phone": "+1 (555) 123-4567",
        "email": "support@acme.com",
        "website_url": "https://acme.com",
        "services": "Software Development, Cloud Hosting, Technical Support",
        "hours_of_operation": "Monday-Friday 9AM-6PM PST",
        "faq": "Q: What are your hours? A: 9AM-6PM PST weekdays",
        "reference_urls": "https://docs.acme.com, https://help.acme.com",
        
        # Behavior & Rules (Step 2)
        "primaryFunction": "Customer Support Specialist for technical inquiries",
        "conversationStyle": "empathetic",
        "creativity": 50,
        "response_length": "medium",
        "proactiveFollowups": True,
        "handoffMessage": "Let me connect you with a human specialist who can better assist you.",
        "autoEscalate": True,
        "notification_email": "alerts@acme.com",
        
        # Deployment (Step 3)
        "deployment_channel": "web_widget",
        "accent_color": "#3B82F6",
        "prompt_template": "You are a helpful AI assistant for Acme Corporation."
    }
    
    workspace_id = "wrk_test_standard"
    team_id = "team_test"
    
    # Create agent manager
    manager = AgentManager()
    
    try:
        # Create agent instance
        agent = AgentFactory.create_agent(
            settings=settings,
            workspace_id=workspace_id,
            team_id=team_id,
            tools=[],
        )
        
        # Get the system prompt (instructions)
        instructions_list = agent.instructions
        
        # Join instructions if it's a list
        if isinstance(instructions_list, list):
            instructions = "\n".join(str(item) for item in instructions_list)
        else:
            instructions = str(instructions_list)
        
        print("\n✓ Agent created successfully")
        print(f"\nAgent Instructions Length: {len(instructions)} characters")
        print("\n" + "-"*80)
        print("SYSTEM PROMPT CONTENT:")
        print("-"*80)
        print(instructions)
        print("-"*80)
        
        # Verify all expected fields are present
        checks = {
            "Business Name": "Acme Corporation" in instructions,
            "Email": "support@acme.com" in instructions,
            "Phone": "+1 (555) 123-4567" in instructions,
            "Address": "123 Tech Street" in instructions,
            "Website": "https://acme.com" in instructions,
            "Services": "Software Development" in instructions,
            "Business Hours": "Monday-Friday 9AM-6PM PST" in instructions,
            "FAQ": "What are your hours?" in instructions,
            "Description": "premium software solutions" in instructions,
            "Reference URLs": "https://docs.acme.com" in instructions,
            "Primary Function": "Customer Support Specialist" in instructions,
            "Conversation Style": ("empathetic" in instructions.lower() or "empathy" in instructions.lower()),
            "Proactive Follow-ups": "clarifying questions" in instructions,
            "Handoff Message": "connect you with a human specialist" in instructions,
            "Auto-Escalate": "AUTO-ESCALATION" in instructions or "auto-escalate" in instructions.lower(),
        }
        
        print("\n" + "="*80)
        print("VERIFICATION RESULTS:")
        print("="*80)
        
        passed = 0
        failed = 0
        
        for field, present in checks.items():
            status = "✓ PASS" if present else "✗ FAIL"
            print(f"{status}: {field}")
            if present:
                passed += 1
            else:
                failed += 1
        
        print(f"\nResults: {passed}/{len(checks)} checks passed")
        
        if failed > 0:
            print(f"\n⚠️  WARNING: {failed} fields missing from system prompt!")
            return False
        else:
            print("\n✅ All Standard Agent context fields verified!")
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openclaw_agent_context():
    """Test that OpenClaw Agent receives all configured context fields"""
    
    print("\n" + "="*80)
    print("TEST 2: OpenClaw Agent Context Awareness")
    print("="*80)
    
    # Mock settings with OpenClaw-specific fields
    settings = {
        # Identity & Branding (Step 1)
        "agent_name": "Flight Booking Assistant",
        "voice_id": "nova",
        "language": "en",
        "accent_color": "#10B981",
        
        # Job Context (Step 2)
        "primaryFunction": "Book flights and manage travel arrangements with a focus on finding the best deals",
        "user_email": "john.doe@example.com",
        "user_phone": "+1 (555) 987-6543",
        "business_name": "Travel Pro Agency",
        "description": "Premium travel booking service",
        "personalPreferences": """
- Always prefer aisle seats
- Never book flights before 10 AM
- Prefer direct flights when possible
- Budget limit: $500 per ticket
- Dietary restriction: Vegetarian meals only
""",
        
        # Safety & Guardrails (Step 6)
        "whitelisted_domains": ["expedia.com", "kayak.com", "united.com"],
        "maxDepth": 10,
        "handoffMessage": "I've reached my navigation limit. Let me hand this over to a human agent.",
        
        "prompt_template": "You are an AI travel assistant."
    }
    
    workspace_id = "wrk_test_openclaw"
    team_id = "team_test"
    
    # Create agent manager
    manager = AgentManager()
    
    try:
        # Create agent instance
        agent = AgentFactory.create_agent(
            settings=settings,
            workspace_id=workspace_id,
            team_id=team_id,
            tools=[],
        )
        
        # Get the system prompt (instructions)
        instructions_list = agent.instructions
        
        # Join instructions if it's a list
        if isinstance(instructions_list, list):
            instructions = "\n".join(str(item) for item in instructions_list)
        else:
            instructions = str(instructions_list)
        
        print("\n✓ Agent created successfully")
        print(f"\nAgent Instructions Length: {len(instructions)} characters")
        print("\n" + "-"*80)
        print("SYSTEM PROMPT CONTENT:")
        print("-"*80)
        print(instructions)
        print("-"*80)
        
        # Verify OpenClaw-specific fields
        checks = {
            "Primary Function (Browsing Persona)": "Book flights and manage travel" in instructions,
            "User Email": "john.doe@example.com" in instructions,
            "User Phone": "+1 (555) 987-6543" in instructions,
            "Personal Preferences": "aisle seats" in instructions,
            "Preference: No Early Flights": "before 10 AM" in instructions,
            "Preference: Direct Flights": "direct flights" in instructions,
            "Preference: Budget Limit": "$500" in instructions,
            "Preference: Dietary": "Vegetarian" in instructions,
            "Max Depth Navigation Limit": "10" in instructions and "navigate" in instructions.lower(),
            "Handoff Message": "navigation limit" in instructions,
        }
        
        print("\n" + "="*80)
        print("VERIFICATION RESULTS:")
        print("="*80)
        
        passed = 0
        failed = 0
        
        for field, present in checks.items():
            status = "✓ PASS" if present else "✗ FAIL"
            print(f"{status}: {field}")
            if present:
                passed += 1
            else:
                failed += 1
        
        print(f"\nResults: {passed}/{len(checks)} checks passed")
        
        if failed > 0:
            print(f"\n⚠️  WARNING: {failed} fields missing from system prompt!")
            return False
        else:
            print("\n✅ All OpenClaw Agent context fields verified!")
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_styles():
    """Test that all conversation styles are properly mapped"""
    
    print("\n" + "="*80)
    print("TEST 3: Conversation Style Mapping")
    print("="*80)
    
    styles = ["professional", "friendly", "empathetic", "witty"]
    manager = AgentManager()
    
    results = {}
    
    for style in styles:
        settings = {
            "agent_name": f"Test {style.title()} Agent",
            "conversationStyle": style,
            "prompt_template": "You are a helpful assistant."
        }
        
        try:
            agent = AgentFactory.create_agent(
                settings=settings,
                workspace_id="wrk_test",
                team_id="team_test",
                tools=[]
            )
            
            instructions_list = agent.instructions
            
            # Join instructions if it's a list
            if isinstance(instructions_list, list):
                instructions = "\n".join(str(item) for item in instructions_list)
            else:
                instructions = str(instructions_list)
            
            # Check if style is mentioned
            style_present = (
                style.lower() in instructions.lower() or
                "CONVERSATION STYLE" in instructions
            )
            
            results[style] = style_present
            status = "✓ PASS" if style_present else "✗ FAIL"
            print(f"{status}: {style.title()} style")
            
        except Exception as e:
            print(f"✗ FAIL: {style.title()} style - {e}")
            results[style] = False
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All conversation styles verified!")
    else:
        print(f"\n⚠️  Some styles failed: {[k for k, v in results.items() if not v]}")
    
    return all_passed


def test_proactive_followups():
    """Test proactive follow-ups setting (both True and False)"""
    
    print("\n" + "="*80)
    print("TEST 4: Proactive Follow-ups Setting")
    print("="*80)
    
    manager = AgentManager()
    
    # Test with proactiveFollowups = True
    settings_true = {
        "agent_name": "Proactive Agent",
        "proactiveFollowups": True,
        "prompt_template": "You are a helpful assistant."
    }
    
    agent_true = AgentFactory.create_agent(
        settings=settings_true,
        workspace_id="wrk_test",
        team_id="team_test",
        tools=[]
    )
    
    instructions_list = agent_true.instructions
    if isinstance(instructions_list, list):
        instructions_true = "\n".join(str(item) for item in instructions_list)
    else:
        instructions_true = str(instructions_list)
    
    has_proactive_instruction = "clarifying questions" in instructions_true
    
    status_true = "✓ PASS" if has_proactive_instruction else "✗ FAIL"
    print(f"{status_true}: Proactive Follow-ups = True")
    
    # Test with proactiveFollowups = False
    settings_false = {
        "agent_name": "Non-Proactive Agent",
        "proactiveFollowups": False,
        "prompt_template": "You are a helpful assistant."
    }
    
    agent_false = AgentFactory.create_agent(
        settings=settings_false,
        workspace_id="wrk_test",
        team_id="team_test",
        tools=[]
    )
    
    instructions_list = agent_false.instructions
    if isinstance(instructions_list, list):
        instructions_false = "\n".join(str(item) for item in instructions_list)
    else:
        instructions_false = str(instructions_list)
    
    has_no_questions_instruction = "Do NOT ask clarifying questions" in instructions_false
    
    status_false = "✓ PASS" if has_no_questions_instruction else "✗ FAIL"
    print(f"{status_false}: Proactive Follow-ups = False")
    
    both_passed = has_proactive_instruction and has_no_questions_instruction
    
    if both_passed:
        print("\n✅ Proactive follow-ups setting verified!")
    else:
        print("\n⚠️  Proactive follow-ups setting failed!")
    
    return both_passed


def main():
    """Run all E2E tests"""
    
    print("\n" + "="*80)
    print("AGENT CONTEXT AWARENESS - END-TO-END BACKEND TEST")
    print("="*80)
    print("\nTesting that all wizard configuration fields are properly")
    print("injected into agent system prompts.\n")
    
    results = []
    
    # Run all tests
    results.append(("Standard Agent Context", test_standard_agent_context()))
    results.append(("OpenClaw Agent Context", test_openclaw_agent_context()))
    results.append(("Conversation Styles", test_conversation_styles()))
    results.append(("Proactive Follow-ups", test_proactive_followups()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Context awareness is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
