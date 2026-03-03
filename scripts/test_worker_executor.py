#!/usr/bin/env python3
"""
Worker Execution Engine Comprehensive Test Suite

Tests the WorkerExecutor, JobSearchWorker, and end-to-end task processing.
"""

import os
import sys
import time
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def log_pass(msg):
    print(f"✓ {msg}")

def log_fail(msg):
    print(f"✗ {msg}")

def log_info(msg):
    print(f"ℹ {msg}")

def log_section(title):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print('='*60 + "\n")


def test_imports():
    """Test 1: Module Imports"""
    log_section("Module Imports")
    results = []
    
    # WorkerExecutor
    try:
        from backend.workers import WorkerExecutor, get_executor, start_executor, stop_executor
        log_pass("WorkerExecutor imports work")
        results.append(True)
    except Exception as e:
        log_fail(f"WorkerExecutor import failed: {e}")
        results.append(False)
    
    # JobSearchWorker
    try:
        from backend.workers import JobSearchWorker
        log_pass("JobSearchWorker imports work")
        results.append(True)
    except Exception as e:
        log_fail(f"JobSearchWorker import failed: {e}")
        results.append(False)
    
    # Test executor creation
    try:
        from backend.workers import get_executor
        executor = get_executor()
        status = executor.get_status()
        log_pass(f"Executor status: running={status['running']}, handlers={len(executor._handlers)}")
        results.append(True)
    except Exception as e:
        log_fail(f"Executor creation failed: {e}")
        results.append(False)
    
    # Test handler registration
    try:
        from backend.workers import get_executor
        executor = get_executor()
        if "job-search" in executor._handlers:
            log_pass("job-search handler registered")
            results.append(True)
        else:
            log_fail("job-search handler NOT registered")
            results.append(False)
    except Exception as e:
        log_fail(f"Handler check failed: {e}")
        results.append(False)
    
    return all(results)


def test_executor_lifecycle():
    """Test 2: Executor Start/Stop"""
    log_section("Executor Lifecycle")
    results = []
    
    try:
        from backend.workers import WorkerExecutor
        executor = WorkerExecutor(poll_interval=1)
        
        # Start
        executor.start()
        time.sleep(0.5)
        status = executor.get_status()
        if status["running"]:
            log_pass("Executor started successfully")
            results.append(True)
        else:
            log_fail("Executor not running after start()")
            results.append(False)
        
        # Stop
        executor.stop()
        time.sleep(0.5)
        status = executor.get_status()
        if not status["running"]:
            log_pass("Executor stopped successfully")
            results.append(True)
        else:
            log_fail("Executor still running after stop()")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Lifecycle test failed: {e}")
        results.append(False)
    
    return all(results)


def test_job_search_worker_direct():
    """Test 3: JobSearchWorker Direct Execution"""
    log_section("JobSearchWorker Direct Execution")
    results = []
    
    try:
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        from backend.workers import JobSearchWorker
        import uuid
        
        db = SessionLocal()
        service = WorkerService(db)
        
        # Get a workspace ID
        from backend.models_db import Workspace
        workspace = db.query(Workspace).first()
        if not workspace:
            log_fail("No workspace found for testing")
            return False
        
        workspace_id = workspace.id
        
        # Create a task
        task = service.create_task(
            workspace_id=workspace_id,
            worker_type="job-search",
            input_data={"job_title": "Python Developer", "location": "Remote"}
        )
        log_pass(f"Created test task: {task.id}")
        
        # Execute worker directly
        result = JobSearchWorker.execute(
            task_id=task.id,
            input_data=task.input_data,
            service=service,
            db=db
        )
        
        if "jobs_found" in result:
            log_pass(f"Worker returned {len(result.get('jobs_found', []))} jobs")
            results.append(True)
        else:
            log_fail("Worker did not return jobs_found")
            results.append(False)
        
        if "summary" in result:
            log_pass(f"Worker generated summary: {result['summary'][:50]}...")
            results.append(True)
        else:
            log_fail("Worker did not generate summary")
            results.append(False)
        
        # Check task was updated
        updated_task = service.get_task(task.id)
        if updated_task.steps_completed > 0:
            log_pass(f"Task progress updated: {updated_task.steps_completed}/{updated_task.steps_total}")
            results.append(True)
        else:
            log_fail("Task progress not updated")
            results.append(False)
        
        # Cleanup
        service.cancel_task(task.id)
        log_pass("Test task cleaned up")
        
        db.close()
        
    except Exception as e:
        log_fail(f"Direct execution test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    return all(results)


def test_api_task_creation():
    """Test 4: API Task Creation"""
    log_section("API Task Creation")
    results = []
    
    try:
        # Get workspace ID
        from backend.database import SessionLocal
        from backend.models_db import Workspace
        db = SessionLocal()
        workspace = db.query(Workspace).first()
        db.close()
        
        if not workspace:
            log_fail("No workspace found")
            return False
        
        workspace_id = workspace.id
        
        # Create task via API
        resp = requests.post(
            f"{BASE_URL}/workers/tasks",
            params={"workspace_id": workspace_id},
            json={"worker_type": "job-search", "input_data": {"job_title": "Engineer"}}
        )
        
        if resp.status_code == 200:
            task_data = resp.json()
            log_pass(f"Created task via API: {task_data['id']}")
            results.append(True)
            
            # Check status
            if task_data["status"] in ["pending", "running"]:
                log_pass(f"Task status: {task_data['status']}")
                results.append(True)
            else:
                log_fail(f"Unexpected status: {task_data['status']}")
                results.append(False)
            
            # Cancel to cleanup
            cancel_resp = requests.post(f"{BASE_URL}/workers/tasks/{task_data['id']}/cancel")
            if cancel_resp.status_code == 200:
                log_pass("Task cancelled for cleanup")
            
        else:
            log_fail(f"API task creation failed: {resp.status_code} - {resp.text}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"API test failed: {e}")
        results.append(False)
    
    return all(results)


def test_task_polling():
    """Test 5: Task Polling via API"""
    log_section("Task Polling")
    results = []
    
    try:
        # Get workspace ID
        from backend.database import SessionLocal
        from backend.models_db import Workspace
        db = SessionLocal()
        workspace = db.query(Workspace).first()
        db.close()
        
        if not workspace:
            log_fail("No workspace found")
            return False
        
        workspace_id = workspace.id
        
        # Get tasks
        resp = requests.get(
            f"{BASE_URL}/workers/tasks",
            params={"workspace_id": workspace_id}
        )
        
        if resp.status_code == 200:
            tasks = resp.json()
            log_pass(f"Fetched {len(tasks)} tasks via API")
            results.append(True)
        else:
            log_fail(f"Task polling failed: {resp.status_code}")
            results.append(False)
        
        # Get stats
        stats_resp = requests.get(
            f"{BASE_URL}/workers/stats",
            params={"workspace_id": workspace_id}
        )
        
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            log_pass(f"Stats: total_tasks={stats.get('total_tasks')}, tokens={stats.get('total_tokens_used')}")
            results.append(True)
        else:
            log_fail(f"Stats fetch failed: {stats_resp.status_code}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Polling test failed: {e}")
        results.append(False)
    
    return all(results)


def test_worker_prompts():
    """Test 6: Worker Prompts with Reward Model"""
    log_section("Worker Prompts")
    results = []
    
    try:
        from backend.prompts import get_worker_prompt, WORKER_REWARD_MODEL
        
        # Test prompt generation
        prompt = get_worker_prompt("job-search", {"job_title": "Developer"})
        
        if len(prompt) > 1000:
            log_pass(f"Generated prompt: {len(prompt)} chars")
            results.append(True)
        else:
            log_fail("Prompt too short")
            results.append(False)
        
        # Check reward model included
        if "Quality Reward System" in prompt:
            log_pass("Reward model included in prompt")
            results.append(True)
        else:
            log_fail("Reward model NOT included in prompt")
            results.append(False)
        
        # Check it can be disabled
        prompt_no_reward = get_worker_prompt("job-search", {}, include_reward_model=False)
        if "Quality Reward System" not in prompt_no_reward:
            log_pass("Reward model can be disabled")
            results.append(True)
        else:
            log_fail("Reward model cannot be disabled")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Prompt test failed: {e}")
        results.append(False)
    
    return all(results)


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  WORKER EXECUTION ENGINE TEST SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_results = {
        "Module Imports": test_imports(),
        "Executor Lifecycle": test_executor_lifecycle(),
        "JobSearchWorker Direct": test_job_search_worker_direct(),
        "API Task Creation": test_api_task_creation(),
        "Task Polling": test_task_polling(),
        "Worker Prompts": test_worker_prompts(),
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
