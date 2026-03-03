import asyncio
import logging
import os
import sys
import uvicorn
import json
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
from openai import AsyncOpenAI

# Configuration from Environment
PORT = int(os.getenv("PORT", "8000"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:8000")
API_KEY = os.getenv("LLM_API_KEY") 
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-5-sonnet")
WORKER_AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN") # Scoped JWT
MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenClawContainer")

app = FastAPI(title="OpenClaw Container Worker")

# Initialize LLM Client
llm_client = None
if API_KEY:
    # Check if we should use OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        llm_client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        llm_client = AsyncOpenAI(api_key=API_KEY)

# --- Status & State ---
class WorkerState:
    is_busy: bool = False
    current_task_id: Optional[str] = None
    task_count: int = 0

state = WorkerState()

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for the provisioner."""
    return {
        "status": "ok", 
        "worker_type": "openclaw", 
        "busy": state.is_busy,
        "model": LLM_MODEL,
        "authenticated": bool(WORKER_AUTH_TOKEN)
    }

@app.get("/")
async def root():
    return {"name": "OpenClaw Secure Worker", "version": "1.0.0", "model": LLM_MODEL}

# --- Browser Agent Loop ---

from playwright.async_api import async_playwright, Page, Browser

class OpenClawAgent:
    def __init__(self, page: Page, goal: str, client: AsyncOpenAI, model: str):
        self.page = page
        self.goal = goal
        self.client = client
        self.model = model
        self.history = []
        self.steps = 0

    async def get_page_state(self):
        """Extract current state from the page."""
        title = await self.page.title()
        url = self.page.url
        
        # Simplified DOM representation
        elements = await self.page.evaluate("""() => {
            const items = [];
            const interactive = document.querySelectorAll('a, button, input, select, textarea, [role="button"]');
            interactive.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    items.push({
                        id: index,
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText || el.value || el.placeholder || el.ariaLabel || "",
                        type: el.type || "",
                        href: el.href || ""
                    });
                }
            });
            return items;
        }""")
        
        print(f"DEBUG: Page type: {type(self.page)}")
        try:
             import inspect
             print(f"DEBUG: Screenshot sig: {inspect.signature(self.page.screenshot)}")
        except:
             print("DEBUG: Could not get signature")

        print("DEBUG: ABOUT TO CALL SCREENSHOT NO ARGS")
        screenshot_bytes = await self.page.screenshot()
        print("DEBUG: SCREENSHOT SUCCESS")
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return {
            "title": title,
            "url": url,
            "elements": elements,
            "screenshot": screenshot_b64
        }

    async def run(self):
        """Execute the autonomous loop."""
        logger.info(f"Running agent loop for goal: {self.goal}")
        
        while self.steps < MAX_STEPS:
            self.steps += 1
            logger.info(f"Step {self.steps}/{MAX_STEPS}")
            
            page_state = await self.get_page_state()
            
            # Formulate Prompt
            system_prompt = f"""
            You are an autonomous browser agent. Your goal is: {self.goal}
            
            Available tools:
            1. click(element_id): Click an element by its ID.
            2. type(element_id, text): Type text into an input.
            3. navigate(url): Go to a specific URL.
            4. scroll(direction): Scroll 'up' or 'down'.
            5. wait(seconds): Wait for fixed duration.
            6. finish(summary): Finish the task and provide a final summary of what you found or achieved.
            
            Current URL: {page_state['url']}
            Page Title: {page_state['title']}
            
            Respond with JSON ONLY in the following format:
            {{
                "thought": "Your reasoning for the next action",
                "action": "click|type|navigate|scroll|wait|finish",
                "params": {{ ... }}
            }}
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Current interactive elements: {json.dumps(page_state['elements'][:50])}"}
            ]
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                
                decision = json.loads(response.choices[0].message.content)
                logger.info(f"Decision: {decision['thought']}")
                
                action = decision.get("action")
                params = decision.get("params", {})
                
                if action == "finish":
                    return {"status": "success", "summary": params.get("summary", "Goal achieved.")}
                
                await self.execute_action(action, params)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in step {self.steps}: {e}")
                return {"status": "failed", "error": str(e)}

        return {"status": "failed", "error": f"Exceeded maximum steps ({MAX_STEPS})"}

    async def execute_action(self, action: str, params: dict):
        try:
            if action == "navigate":
                target_url = params.get("url")
                if target_url:
                    await self.page.goto(target_url, wait_until="domcontentloaded")
            elif action == "click":
                idx = params.get("element_id")
                await self.page.evaluate(f"document.querySelectorAll('a, button, input, select, textarea, [role=\"button\"]')[{idx}]?.click()")
            elif action == "type":
                idx = params.get("element_id")
                text = params.get("text")
                await self.page.evaluate(f"(idx, txt) => {{ const el = document.querySelectorAll('a, button, input, select, textarea, [role=\"button\"]')[idx]; if(el) {{ el.value = txt; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }} }}", idx, text)
            elif action == "scroll":
                direction = params.get("direction", "down")
                val = 500 if direction == "down" else -500
                await self.page.evaluate(f"window.scrollBy(0, {val})")
            elif action == "wait":
                await asyncio.sleep(params.get("seconds", 2))
        except Exception as e:
            logger.warning(f"Action {action} failed: {e}")

async def execute_task(task: Dict[str, Any]):
    """
    Execute the browser automation task using the AutonomousAgent.
    """
    task_id = task.get("id")
    input_data = task.get("input_data", {})
    goal = input_data.get("goal")
    url = input_data.get("url")
    
    logger.info(f"Starting Task {task_id}: {goal}")
    state.is_busy = True
    state.current_task_id = task_id
    
    if not llm_client:
        await report_failure(task_id, "No LLM API Key provided to worker.")
        state.is_busy = False
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            if url:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except:
                    logger.warning(f"Initial navigation to {url} timed out, continuing...")
            
            agent = OpenClawAgent(page, goal, llm_client, LLM_MODEL)
            result = await agent.run()
            
            if result["status"] == "success":
                await report_completion(task_id, {"summary": result["summary"]})
            else:
                await report_failure(task_id, result.get("error", "Unknown error"))
                 
            await browser.close()
            
        state.task_count += 1
        logger.info(f"Task {task_id} finished.")

    except Exception as e:
        logger.error(f"Task failed: {e}")
        await report_failure(task_id, str(e))
    finally:
        state.is_busy = False
        state.current_task_id = None

async def report_completion(task_id: str, output: Dict[str, Any]):
    """Send results back to backend."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {WORKER_AUTH_TOKEN}"}
            base_url = BACKEND_URL.rstrip("/")
            
            response = await client.post(
                f"{base_url}/workers/tasks/{task_id}/complete",
                json={
                    "output_data": output,
                    "status": "completed",
                    "tokens_used": 0 
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
            headers = {"Authorization": f"Bearer {WORKER_AUTH_TOKEN}"}
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
    workspace_id = os.getenv("WORKSPACE_ID")
    
    logger.info(f"Worker started. Model: {LLM_MODEL}. Authenticated: {bool(WORKER_AUTH_TOKEN)}")
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                if not state.is_busy:
                    headers = {"Authorization": f"Bearer {WORKER_AUTH_TOKEN}"}
                    base_url = BACKEND_URL.rstrip("/")
                    
                    params = {
                        "status": "pending",
                        "worker_type": "openclaw"
                    }
                    if workspace_id:
                        params["workspace_id"] = workspace_id
                        
                    response = await client.get(
                        f"{base_url}/workers/tasks",
                        params=params,
                        headers=headers,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Handle both list and dict wrapper
                        tasks = data.get("tasks", []) if isinstance(data, dict) else data
                        
                        if isinstance(tasks, list) and tasks:
                            logger.info(f"Found {len(tasks)} pending tasks. Executing first one...")
                            task = tasks[0]
                            await execute_task(task)
                    elif response.status_code == 401 or response.status_code == 403:
                         logger.error(f"Auth failed while polling: {response.text}")
                         await asyncio.sleep(60) 
                
            except Exception as e:
                import traceback
                logger.error(f"Polling error: {repr(e)}")
                traceback.print_exc()
            
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    logger.info(f"OpenClaw Container starting on port {PORT}")
    asyncio.create_task(poll_for_tasks())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
