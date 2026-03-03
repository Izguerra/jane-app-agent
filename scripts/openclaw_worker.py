import asyncio
import logging
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx


# Configuration
PORT = 49182
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# TEMPORARY: Use a user token for verification until worker auth is fully implemented
AUTH_TOKEN = os.getenv("AUTH_TOKEN") 
WORKSPACE_ID = os.getenv("WORKSPACE_ID", "wrk_000V7dMzXJLzP5mYgdf7FzjA3J")

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenClawWorker")

app = FastAPI(title="OpenClaw Reference Worker")

# --- Status & State ---
class WorkerState:
    is_busy: bool = False
    current_task_id: Optional[str] = None

state = WorkerState()

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for the connection service."""
    return {"status": "ok", "worker_type": "openclaw", "busy": state.is_busy}

@app.get("/")
async def root():
    return {"name": "OpenClaw Worker", "version": "1.0.0"}

# --- Task Execution Logic ---

from playwright.async_api import async_playwright

async def execute_task(task: Dict[str, Any]):
    """
    Execute the browser automation task using Playwright.
    """
    task_id = task.get("id")
    input_data = task.get("input_data", {})
    goal = input_data.get("goal")
    url = input_data.get("url")

    logger.info(f"Starting Task {task_id}: {goal}")
    state.is_busy = True
    state.current_task_id = task_id

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            if url:
                logger.info(f"Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded")
                
                # Extract basic info
                title = await page.title()
                content = await page.evaluate("document.body.innerText")
                screenshot_bytes = await page.screenshot()
                import base64
                screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                # Truncate content to avoid huge payloads
                content_preview = content[:2000] + "..." if len(content) > 2000 else content
                
                result = {
                    "page_title": title,
                    "extracted_text": content_preview,
                    "screenshot_base64": screenshot, # Optional: return screenshot
                    "status": "success",
                    "url": page.url
                }
                logger.info(f"Task completed successfully: {title}")
                await report_completion(task_id, result)
            
            else:
                # If no URL, maybe it's a general instruction (not supported yet in this simple version)
                await report_failure(task_id, "No URL provided in task input")
                
            await browser.close()

    except Exception as e:
        logger.error(f"Task failed: {e}")
        await report_failure(task_id, str(e))
    finally:
        state.is_busy = False
        state.current_task_id = None
        logger.info(f"Task {task_id} finished processing.")


async def report_completion(task_id: str, output: Dict[str, Any]):
    """Send results back to backend."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            # FastAPI on 8000 usually doesn't have /api prefix unless configured in main.py
            # Based on main.py, it's just /workers
            base_url = BACKEND_URL.rstrip("/")
            
            response = await client.post(
                f"{base_url}/workers/tasks/{task_id}/complete",
                json={
                    "output_data": output, # Schema expects output_data
                    "status": "completed",
                    "tokens_used": 150
                },
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Reported completion for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to report completion: {e}")

async def report_failure(task_id: str, error: str):
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            base_url = BACKEND_URL.rstrip("/")
            
            await client.post(
                f"{base_url}/workers/tasks/{task_id}/complete",
                json={
                    "output_data": {},
                    "error_message": error,
                    "status": "failed"
                },
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to report failure: {e}")

# --- Polling Loop ---

async def poll_for_tasks():
    """Independent loop to fetch pending tasks from backend."""
    if not AUTH_TOKEN:
        logger.warning("No AUTH_TOKEN provided. Polling disabled.")
        return

    logger.info(f"Starting polling loop for workspace {WORKSPACE_ID}")
    
    async with httpx.AsyncClient() as client:
        while True:
            if not state.is_busy:
                try:
                    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
                    base_url = BACKEND_URL.rstrip("/")
                    
                    params = {
                        "status": "pending",
                        "worker_type": "openclaw"
                    }
                    if WORKSPACE_ID:
                        params["workspace_id"] = WORKSPACE_ID
                        
                    response = await client.get(
                        f"{base_url}/workers/tasks",
                        params=params,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        tasks = response.json()
                        # Backend returns a list directly
                        if isinstance(tasks, list) and tasks:
                            logger.info(f"Found {len(tasks)} pending tasks.")
                            task = tasks[0]
                            logger.info(f"Executing task: {task['id']}")
                            await execute_task(task)
                        elif isinstance(tasks, dict) and "tasks" in tasks:
                            # Handle pagination wrapper if present (though my code returned list)
                             _tasks = tasks.get("tasks", [])
                             if _tasks:
                                 await execute_task(_tasks[0])
                        
                except Exception as e:
                    logger.error(f"Polling error: {e}")
            
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    logger.info(f"OpenClaw Worker starting on port {PORT}")
    asyncio.create_task(poll_for_tasks())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)

