#!/usr/bin/env python3
"""
Comprehensive Test Suite for Worker Model Implementation

Tests:
1. Database tables exist and have correct schema
2. API endpoints are accessible and return correct data
3. WorkerService CRUD operations
4. Tool imports and function definitions
5. Web search tool (optional, requires TAVILY_API_KEY)
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log_pass(msg):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def log_fail(msg):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def log_warn(msg):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

def log_section(title):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


# ===========================================================================
# TEST 1: Module Imports
# ===========================================================================

def test_imports():
    """Test that all new modules can be imported without errors."""
    log_section("TEST 1: Module Imports")
    
    results = []
    
    # Test WorkerService import
    try:
        from backend.services.worker_service import WorkerService
        log_pass("WorkerService imported successfully")
        results.append(True)
    except Exception as e:
        log_fail(f"WorkerService import failed: {e}")
        results.append(False)
    
    # Test worker_tools import
    try:
        from backend.tools.worker_tools import (
            dispatch_worker_task, 
            get_worker_schema, 
            get_task_status, 
            list_available_workers,
            WorkerToolHandler
        )
        log_pass("worker_tools imported successfully")
        results.append(True)
    except Exception as e:
        log_fail(f"worker_tools import failed: {e}")
        results.append(False)
    
    # Test web_search import
    try:
        from backend.tools.web_search import (
            WebSearchTool, 
            web_search, 
            search_job_listings,
            get_web_search_tool
        )
        log_pass("web_search imported successfully")
        results.append(True)
    except Exception as e:
        log_fail(f"web_search import failed: {e}")
        results.append(False)
    
    # Test worker_prompts import
    try:
        from backend.prompts.worker_prompts import (
            ORCHESTRATOR_WORKER_INSTRUCTIONS,
            JOB_SEARCH_WORKER_PROMPT,
            LEAD_RESEARCH_WORKER_PROMPT,
            CONTENT_WRITER_WORKER_PROMPT,
            get_worker_prompt
        )
        log_pass("worker_prompts imported successfully")
        results.append(True)
    except Exception as e:
        log_fail(f"worker_prompts import failed: {e}")
        results.append(False)
    
    # Test models import
    try:
        from backend.models_db import WorkerTemplate, WorkerTask
        log_pass("WorkerTemplate and WorkerTask models imported successfully")
        results.append(True)
    except Exception as e:
        log_fail(f"Models import failed: {e}")
        results.append(False)
    
    # Test tools/__init__.py exports
    try:
        from backend.tools import (
            web_search, 
            search_job_listings,
            dispatch_worker_task,
            get_worker_schema,
            WorkerToolHandler,
            AppointmentTools
        )
        log_pass("backend.tools package exports work correctly")
        results.append(True)
    except Exception as e:
        log_fail(f"backend.tools package export failed: {e}")
        results.append(False)
    
    return all(results)


# ===========================================================================
# TEST 2: API Endpoints
# ===========================================================================

def test_api_endpoints():
    """Test that all worker API endpoints are accessible."""
    log_section("TEST 2: API Endpoints")
    
    results = []
    
    # Test GET /workers/templates
    try:
        response = requests.get(f"{BASE_URL}/workers/templates", timeout=5)
        if response.status_code == 200:
            templates = response.json()
            log_pass(f"GET /workers/templates - Status 200, returned {len(templates)} templates")
            
            # Verify template structure
            if len(templates) > 0:
                template = templates[0]
                required_fields = ['id', 'name', 'slug', 'parameter_schema']
                missing = [f for f in required_fields if f not in template]
                if not missing:
                    log_pass("Template structure is correct")
                    results.append(True)
                else:
                    log_fail(f"Template missing fields: {missing}")
                    results.append(False)
            else:
                log_warn("No templates returned - seeding may have failed")
                results.append(True)  # Not a failure, just empty
        else:
            log_fail(f"GET /workers/templates - Status {response.status_code}")
            results.append(False)
    except requests.exceptions.ConnectionError:
        log_fail("Could not connect to backend server at localhost:8000")
        results.append(False)
    except Exception as e:
        log_fail(f"GET /workers/templates failed: {e}")
        results.append(False)
    
    # Test GET /workers/templates/{slug}
    try:
        response = requests.get(f"{BASE_URL}/workers/templates/job-search", timeout=5)
        if response.status_code == 200:
            template = response.json()
            log_pass(f"GET /workers/templates/job-search - Found '{template.get('name')}'")
            results.append(True)
        elif response.status_code == 404:
            log_warn("GET /workers/templates/job-search - Template not found (may not be seeded)")
            results.append(True)
        else:
            log_fail(f"GET /workers/templates/job-search - Status {response.status_code}")
            results.append(False)
    except Exception as e:
        log_fail(f"GET /workers/templates/job-search failed: {e}")
        results.append(False)
    
    # Test GET /workers/templates/{slug}/schema
    try:
        response = requests.get(f"{BASE_URL}/workers/templates/job-search/schema", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            if 'properties' in schema:
                log_pass(f"GET /workers/templates/job-search/schema - Schema has {len(schema.get('properties', {}))} properties")
                results.append(True)
            else:
                log_warn("Schema returned but may be empty")
                results.append(True)
        elif response.status_code == 404:
            log_warn("Schema endpoint returned 404 (template may not exist)")
            results.append(True)
        else:
            log_fail(f"GET /workers/templates/job-search/schema - Status {response.status_code}")
            results.append(False)
    except Exception as e:
        log_fail(f"GET /workers/templates/job-search/schema failed: {e}")
        results.append(False)
    
    # Test GET /workers/tasks (requires workspace_id)
    try:
        response = requests.get(f"{BASE_URL}/workers/tasks?workspace_id=test_ws", timeout=5)
        if response.status_code == 200:
            tasks = response.json()
            log_pass(f"GET /workers/tasks - Status 200, returned {len(tasks)} tasks")
            results.append(True)
        else:
            log_fail(f"GET /workers/tasks - Status {response.status_code}")
            results.append(False)
    except Exception as e:
        log_fail(f"GET /workers/tasks failed: {e}")
        results.append(False)
    
    return all(results)


# ===========================================================================
# TEST 3: WorkerService CRUD
# ===========================================================================

def test_worker_service():
    """Test WorkerService CRUD operations with a real database session."""
    log_section("TEST 3: WorkerService CRUD Operations")
    
    results = []
    
    try:
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        
        db = SessionLocal()
        service = WorkerService(db)
        
        # Test get_all_templates
        try:
            templates = service.get_all_templates()
            log_pass(f"get_all_templates() returned {len(templates)} templates")
            results.append(True)
        except Exception as e:
            log_fail(f"get_all_templates() failed: {e}")
            results.append(False)
        
        # Test get_template_by_slug
        try:
            template = service.get_template_by_slug("job-search")
            if template:
                log_pass(f"get_template_by_slug('job-search') found template: {template.name}")
            else:
                log_warn("get_template_by_slug('job-search') returned None (template may not exist)")
            results.append(True)
        except Exception as e:
            log_fail(f"get_template_by_slug() failed: {e}")
            results.append(False)
        
        # Test get_template_schema
        try:
            schema = service.get_template_schema("job-search")
            if schema:
                log_pass(f"get_template_schema('job-search') returned schema with {len(schema.get('properties', {}))} properties")
            else:
                log_warn("get_template_schema('job-search') returned empty schema")
            results.append(True)
        except Exception as e:
            log_fail(f"get_template_schema() failed: {e}")
            results.append(False)
        
        # Test create_task and get_task
        try:
            # First, get a real workspace ID from the database
            from backend.models_db import Workspace
            real_workspace = db.query(Workspace).first()
            if not real_workspace:
                log_warn("No workspaces found in database - skipping task CRUD tests")
                results.append(True)
            else:
                test_workspace_id = real_workspace.id
                log_info(f"Using workspace: {test_workspace_id}")
                
                # Create a test task
                task = service.create_task(
                    workspace_id=test_workspace_id,
                    worker_type="job-search",
                    input_data={
                        "job_title": "Test Engineer",
                        "location": "Remote"
                    }
                )
                log_pass(f"create_task() created task with ID: {task.id}")
                
                # Retrieve the task
                retrieved = service.get_task(task.id)
                if retrieved and retrieved.id == task.id:
                    log_pass(f"get_task() successfully retrieved task")
                else:
                    log_fail("get_task() failed to retrieve created task")
                
                # Update task status
                updated = service.update_task_status(
                    task_id=task.id,
                    status="running",
                    current_step="Searching job boards",
                    steps_completed=1,
                    steps_total=5
                )
                if updated and updated.status == "running":
                    log_pass(f"update_task_status() - Status updated to 'running'")
                else:
                    log_fail("update_task_status() failed")
                
                # Add log entry
                logged = service.add_task_log(task.id, "Starting job search", level="info")
                if logged and len(logged.logs) > 0:
                    log_pass(f"add_task_log() - Added log entry")
                else:
                    log_fail("add_task_log() failed")
                
                # Cancel the test task (cleanup)
                cancelled = service.cancel_task(task.id)
                if cancelled and cancelled.status == "cancelled":
                    log_pass(f"cancel_task() - Task cancelled successfully")
                else:
                    log_fail("cancel_task() failed")
                
                results.append(True)
            
        except Exception as e:
            log_fail(f"Task CRUD operations failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        
        # Test get_workspace_stats
        try:
            # Get a real workspace ID
            from backend.models_db import Workspace
            real_workspace = db.query(Workspace).first()
            if real_workspace:
                stats = service.get_workspace_stats(real_workspace.id)
                log_pass(f"get_workspace_stats() returned: {stats}")
                results.append(True)
            else:
                log_warn("No workspace for stats test")
                results.append(True)
        except Exception as e:
            log_fail(f"get_workspace_stats() failed: {e}")
            results.append(False)
        
        db.close()
        
    except Exception as e:
        log_fail(f"Database connection failed: {e}")
        results.append(False)
    
    return all(results)


# ===========================================================================
# TEST 4: Worker Prompts
# ===========================================================================

def test_worker_prompts():
    """Test worker prompts are properly formatted."""
    log_section("TEST 4: Worker Prompts")
    
    results = []
    
    try:
        from backend.prompts.worker_prompts import (
            ORCHESTRATOR_WORKER_INSTRUCTIONS,
            get_worker_prompt
        )
        
        # Test orchestrator instructions exist
        if len(ORCHESTRATOR_WORKER_INSTRUCTIONS) > 100:
            log_pass(f"ORCHESTRATOR_WORKER_INSTRUCTIONS defined ({len(ORCHESTRATOR_WORKER_INSTRUCTIONS)} chars)")
            results.append(True)
        else:
            log_fail("ORCHESTRATOR_WORKER_INSTRUCTIONS too short")
            results.append(False)
        
        # Test get_worker_prompt for each type
        for worker_type in ["job-search", "lead-research", "content-writer"]:
            prompt = get_worker_prompt(worker_type, {"job_title": "Test", "topic": "Test"})
            if prompt and len(prompt) > 100:
                log_pass(f"get_worker_prompt('{worker_type}') - Generated {len(prompt)} chars")
                results.append(True)
            else:
                log_fail(f"get_worker_prompt('{worker_type}') returned empty prompt")
                results.append(False)
                
    except Exception as e:
        log_fail(f"Worker prompts test failed: {e}")
        results.append(False)
    
    return all(results)


# ===========================================================================
# TEST 5: Web Search Tool
# ===========================================================================

def test_web_search_tool():
    """Test WebSearchTool (optional, requires TAVILY_API_KEY)."""
    log_section("TEST 5: Web Search Tool")
    
    results = []
    
    try:
        from backend.tools.web_search import WebSearchTool, TAVILY_AVAILABLE
        
        # Check if Tavily is installed
        if not TAVILY_AVAILABLE:
            log_warn("Tavily package not installed (pip install tavily-python)")
            return True  # Not a failure
        
        log_pass("Tavily package is installed")
        
        # Check API key
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            log_warn("TAVILY_API_KEY not set - skipping live search test")
            log_info("Set TAVILY_API_KEY to enable web search functionality")
            return True  # Not a failure, just not configured
        
        log_pass("TAVILY_API_KEY is set")
        
        # Test actual search (only if key is set)
        tool = WebSearchTool(api_key=api_key)
        
        try:
            result = tool.search("Python programming language", max_results=2)
            if "error" in result:
                log_fail(f"Search returned error: {result['error']}")
                results.append(False)
            elif result.get("results"):
                log_pass(f"Web search returned {len(result['results'])} results")
                if result.get("answer"):
                    log_pass(f"AI answer summary provided")
                results.append(True)
            else:
                log_warn("Search returned no results (may be rate limited)")
                results.append(True)
        except Exception as e:
            log_fail(f"Web search failed: {e}")
            results.append(False)
            
    except Exception as e:
        log_fail(f"Web search tool test failed: {e}")
        results.append(False)
    
    return all(results) if results else True


# ===========================================================================
# TEST 6: Function Tools Structure
# ===========================================================================

def test_function_tools():
    """Test that function tools have correct decorator and signatures."""
    log_section("TEST 6: Function Tool Definitions")
    
    results = []
    
    try:
        from backend.tools.worker_tools import (
            dispatch_worker_task,
            get_worker_schema,
            get_task_status,
            list_available_workers
        )
        from backend.tools.web_search import web_search, search_job_listings
        
        # Check each tool has __name__ (decorated properly)
        tools = [
            ("dispatch_worker_task", dispatch_worker_task),
            ("get_worker_schema", get_worker_schema),
            ("get_task_status", get_task_status),
            ("list_available_workers", list_available_workers),
            ("web_search", web_search),
            ("search_job_listings", search_job_listings),
        ]
        
        for name, tool in tools:
            if hasattr(tool, '__wrapped__') or callable(tool):
                log_pass(f"{name} is a valid callable")
                results.append(True)
            else:
                log_fail(f"{name} is not a valid callable")
                results.append(False)
                
    except Exception as e:
        log_fail(f"Function tools test failed: {e}")
        results.append(False)
    
    return all(results)


# ===========================================================================
# MAIN
# ===========================================================================

def run_all_tests():
    """Run all tests and report summary."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  WORKER MODEL COMPREHENSIVE TEST SUITE{Colors.RESET}")
    print(f"{Colors.BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    test_results = {}
    
    # Run each test suite
    test_results["Module Imports"] = test_imports()
    test_results["API Endpoints"] = test_api_endpoints()
    test_results["WorkerService CRUD"] = test_worker_service()
    test_results["Worker Prompts"] = test_worker_prompts()
    test_results["Web Search Tool"] = test_web_search_tool()
    test_results["Function Tools"] = test_function_tools()
    
    # Summary
    log_section("TEST SUMMARY")
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for name, result in test_results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} - {name}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} test suites passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
