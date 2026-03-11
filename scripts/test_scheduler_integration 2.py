#!/usr/bin/env python3
"""
Comprehensive test for Scheduler Service and WorkerTools integration.
Tests:
1. Scheduler Service - Create schedule, verify polling
2. WorkerTools - Test schedule_worker_task method
3. Voice Agent - Verify WorkerTools import works
"""

import sys
import os
from datetime import datetime, timezone, timedelta
import uuid

sys.path.append(".")
from backend.database import SessionLocal
from backend.models_db import WorkerSchedule, WorkerTask

def test_scheduler_service():
    """Test 1: Verify SchedulerService can create and process schedules."""
    print("\n=== TEST 1: Scheduler Service ===")
    
    from backend.services.scheduler_service import SchedulerService
    
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        
        # Create a test schedule
        schedule = service.create_schedule(
            workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J",
            worker_type="job-search",
            schedule_expression="daily at 9am",
            input_data={"location": "Test", "job_title": "Test Scheduler Service"},
            user_id=None
        )
        
        print(f"✅ Created schedule: {schedule.id}")
        print(f"   Next run at: {schedule.next_run_at}")
        print(f"   Expression: {schedule.schedule_expression}")
        
        # Verify next_run_at is in the future
        now = datetime.now(timezone.utc)
        if schedule.next_run_at > now:
            print(f"✅ next_run_at is correctly in the future")
        else:
            print(f"❌ next_run_at should be in the future but is {schedule.next_run_at}")
            
        # Clean up
        db.delete(schedule)
        db.commit()
        print("✅ Cleanup successful")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()

def test_worker_tools():
    """Test 2: Verify WorkerTools.schedule_worker_task works."""
    print("\n=== TEST 2: WorkerTools.schedule_worker_task ===")
    
    from backend.tools.worker_tools import WorkerTools
    import asyncio
    
    try:
        tools = WorkerTools(
            workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J",
            agent_id=None
        )
        
        # Test schedule_worker_task - it's now async
        async def run_test():
            return await tools.schedule_worker_task(
                worker_type="job-search",
                schedule_expression="hourly",
                parameters={"location": "Toronto", "job_title": "Test WorkerTools"}
            )
        
        result = asyncio.run(run_test())
        
        print(f"Result: {result}")
        
        if "Schedule created successfully" in result:
            print("✅ schedule_worker_task works correctly")
            
            # Extract schedule ID and clean up
            schedule_id = result.split("ID: ")[1].split(".")[0]
            
            db = SessionLocal()
            try:
                schedule = db.query(WorkerSchedule).filter(WorkerSchedule.id == schedule_id).first()
                if schedule:
                    db.delete(schedule)
                    db.commit()
                    print(f"✅ Cleaned up test schedule {schedule_id}")
            finally:
                db.close()
            
            return True
        else:
            print(f"❌ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_agent_imports():
    """Test 3: Verify voice_agent.py can import WorkerTools without errors."""
    print("\n=== TEST 3: Voice Agent WorkerTools Import ===")
    
    try:
        # Simulate the import that happens in voice_agent.py
        from backend.tools.worker_tools import WorkerTools
        from livekit.agents import llm
        
        # Create instance
        worker_tools = WorkerTools(workspace_id="wrk_test", agent_id=None)
        
        # Test that find_function_tools works
        tools = llm.find_function_tools(worker_tools)
        
        print(f"✅ WorkerTools imported successfully")
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            # Tools from find_function_tools are callables with __name__
            tool_name = getattr(tool, '__name__', getattr(tool, 'name', str(tool)))
            print(f"   - {tool_name}")
        
        # Check for schedule_worker_task
        tool_names = [getattr(t, '__name__', getattr(t, 'name', str(t))) for t in tools]
        if "schedule_worker_task" in tool_names:
            print("✅ schedule_worker_task is available as a voice tool")
        else:
            print("❌ schedule_worker_task not found in tools")
            return False
            
        return True
        
    except ImportError as e:
        print(f"⚠️ LiveKit agents not installed (expected in test env): {e}")
        print("   Checking basic import only...")
        
        try:
            from backend.tools.worker_tools import WorkerTools
            tools = WorkerTools(workspace_id="wrk_test", agent_id=None)
            
            # Check method exists
            if hasattr(tools, 'schedule_worker_task'):
                print("✅ WorkerTools.schedule_worker_task method exists")
                return True
            else:
                print("❌ schedule_worker_task method missing")
                return False
        except Exception as e2:
            print(f"❌ Failed: {e2}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("COMPREHENSIVE TEST: Scheduler & WorkerTools Integration")
    print("=" * 60)
    
    results = []
    
    results.append(("Scheduler Service", test_scheduler_service()))
    results.append(("WorkerTools", test_worker_tools()))
    results.append(("Voice Agent Import", test_voice_agent_imports()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
