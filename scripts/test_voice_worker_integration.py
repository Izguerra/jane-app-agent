#!/usr/bin/env python3
"""
Voice Agent Worker Integration Test Suite

Tests the integration of worker tools with the voice/chat agent.
"""

import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log_pass(msg):
    print(f"✓ {msg}")

def log_fail(msg):
    print(f"✗ {msg}")

def log_section(title):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print('='*60 + "\n")


def test_tool_discovery():
    """Test 1: Agent Tools Discovery"""
    log_section("Agent Tools Discovery")
    results = []
    
    try:
        from livekit.agents import llm
        from backend.agent_tools import AgentTools
        
        tools = AgentTools(workspace_id='test', customer_id='test')
        found_tools = llm.find_function_tools(tools)
        
        log_pass(f"find_function_tools discovered {len(found_tools)} tools")
        results.append(True)
        
        # Check for worker tools specifically
        tool_names = [str(t) for t in found_tools]
        worker_tool_count = sum(1 for t in tool_names if 'worker' in t.lower() or 'task' in t.lower() or 'dispatch' in t.lower())
        
        if worker_tool_count >= 4:
            log_pass(f"Found {worker_tool_count} worker-related tools")
            results.append(True)
        else:
            log_fail(f"Only found {worker_tool_count} worker tools, expected 4")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Tool discovery failed: {e}")
        results.append(False)
    
    return all(results)


def test_list_workers():
    """Test 2: List Available Workers"""
    log_section("List Available Workers")
    results = []
    
    try:
        from backend.agent_tools import AgentTools
        tools = AgentTools(workspace_id='wrk__000V7dCbbMJVHLzTWb9HFWlNzR', customer_id=None)
        
        result = asyncio.run(tools.list_available_workers())
        
        if "Workers" in result or "job-search" in result.lower():
            log_pass(f"list_available_workers returned: {result[:100]}...")
            results.append(True)
        else:
            log_fail(f"Unexpected result: {result}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"list_available_workers failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    return all(results)


def test_get_schema():
    """Test 3: Get Worker Schema"""
    log_section("Get Worker Schema")
    results = []
    
    try:
        from backend.agent_tools import AgentTools
        tools = AgentTools(workspace_id='wrk__000V7dCbbMJVHLzTWb9HFWlNzR', customer_id=None)
        
        result = asyncio.run(tools.get_worker_schema(worker_type="job-search"))
        
        if "Parameters" in result or "job_title" in result.lower():
            log_pass(f"get_worker_schema returned schema info")
            results.append(True)
        else:
            log_fail(f"Unexpected result: {result}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"get_worker_schema failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    return all(results)


def test_dispatch_validation():
    """Test 4: Dispatch Validation"""
    log_section("Dispatch Validation")
    results = []
    
    try:
        from backend.agent_tools import AgentTools
        tools = AgentTools(workspace_id='wrk__000V7dCbbMJVHLzTWb9HFWlNzR', customer_id=None)
        
        # Test missing required field
        result = asyncio.run(tools.dispatch_worker_task(worker_type="job-search"))
        
        if "Error" in result or "required" in result.lower():
            log_pass(f"Properly caught missing job_title")
            results.append(True)
        else:
            log_fail(f"Did not catch missing field: {result}")
            results.append(False)
        
        # Test unknown worker type
        result2 = asyncio.run(tools.dispatch_worker_task(worker_type="unknown-worker"))
        
        if "Unknown" in result2 or "not found" in result2.lower():
            log_pass(f"Properly caught unknown worker type")
            results.append(True)
        else:
            log_fail(f"Did not catch unknown type: {result2}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Dispatch validation failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    return all(results)


def test_task_status():
    """Test 5: Get Task Status"""
    log_section("Get Task Status")
    results = []
    
    try:
        from backend.agent_tools import AgentTools
        tools = AgentTools(workspace_id='wrk__000V7dCbbMJVHLzTWb9HFWlNzR', customer_id=None)
        
        # Test with non-existent task (use valid UUID format)
        result = asyncio.run(tools.get_task_status(task_id="00000000-0000-0000-0000-000000000000"))
        
        if "not found" in result.lower():
            log_pass(f"Properly handled missing task")
            results.append(True)
        else:
            log_fail(f"Unexpected result: {result}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"get_task_status failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    return all(results)


def test_prompt_includes_worker_capabilities():
    """Test 6: Agent Prompt Capability"""
    log_section("Agent Prompt Capability")
    results = []
    
    try:
        # Check that worker capabilities can be described
        from backend.prompts.worker_prompts import ORCHESTRATOR_WORKER_INSTRUCTIONS
        
        if ORCHESTRATOR_WORKER_INSTRUCTIONS and len(ORCHESTRATOR_WORKER_INSTRUCTIONS) > 100:
            log_pass(f"Orchestrator worker instructions available ({len(ORCHESTRATOR_WORKER_INSTRUCTIONS)} chars)")
            results.append(True)
        else:
            log_fail("Orchestrator worker instructions not found or too short")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Prompt check failed: {e}")
        results.append(False)
    
    return all(results)


def main():
    """Run all tests."""
    from datetime import datetime
    
    print("\n" + "="*60)
    print("  VOICE AGENT WORKER INTEGRATION TEST SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_results = {
        "Tool Discovery": test_tool_discovery(),
        "List Workers": test_list_workers(),
        "Get Schema": test_get_schema(),
        "Dispatch Validation": test_dispatch_validation(),
        "Task Status": test_task_status(),
        "Prompt Capability": test_prompt_includes_worker_capabilities(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    for name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"  {icon} {status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResult: {passed}/{len(test_results)} test suites passed")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
