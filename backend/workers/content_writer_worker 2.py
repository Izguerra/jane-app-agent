"""
Content Writer Worker

Autonomous agent that generates marketing content using LLMs.
"""

import logging
import time
import os
import asyncio
from typing import Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from backend.services.worker_service import WorkerService
from backend.prompts.worker_prompts import get_worker_prompt

logger = logging.getLogger("content-writer-worker")

class ContentWriterWorker:
    """
    Content Writer Worker implementation (Real LLM).
    """
    
    @staticmethod
    def execute(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the content writing workflow using Mistral.
        """
        # Run async logic in sync wrapper if needed, or if this is called from thread it's sync blocking
        # but we need to run async code.
        # WorkerExecutor runs this in a thread. We can use asyncio.run
        return asyncio.run(ContentWriterWorker._execute_async(task_id, input_data, service))

    @staticmethod
    async def _execute_async(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService
    ) -> Dict[str, Any]:
        
        topic = input_data.get("topic", "Generative AI")
        content_type = input_data.get("content_type", "Blog Post")
        tone = input_data.get("tone", "Professional")
        
        # Step 1: Initialize
        service.update_task_status(
            task_id,
            status="running",
            current_step=f"Analyzing brief for: {topic}...",
            steps_completed=1,
            steps_total=3
        )
        service.add_task_log(task_id, f"Drafting {content_type} about {topic} with {tone} tone")
        
        # Step 2: Call LLM
        service.update_task_status(
            task_id,
            status="running",
            current_step="Generating quality content...",
            steps_completed=2
        )
        
        try:
            from backend.lib.ai_client import get_ai_client
            client, model_name = get_ai_client(async_mode=True)
        except Exception as e:
            error_msg = f"Failed to get AI client for content: {e}"
            service.add_task_log(task_id, error_msg, level="error")
            raise Exception(error_msg)
        
        # specific prompt
        system_prompt = get_worker_prompt("content-writer", input_data)
        
        try:
            start_time = time.time()
            response = await client.chat.completions.create(
                model=model_name, # High quality model from universal selection
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Write the {content_type} about {topic}."}
                ],
                temperature=0.7
            )
            duration = time.time() - start_time
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            service.add_task_log(task_id, f"Content generated in {duration:.1f}s using {tokens_used} tokens")
            
             # Step 3: Finalize
            service.update_task_status(
                task_id,
                status="completed",
                current_step="Done",
                steps_completed=3
            )
            
            # Simple word count
            word_count = len(content.split())
            
            return {
                "topic": topic,
                "content": content,
                "word_count": word_count,
                "is_stub": False,
                "summary": f"Generated {content_type} on '{topic}' ({word_count} words)."
            }
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            service.add_task_log(task_id, f"LLM Error: {str(e)}", level="error")
            raise e
