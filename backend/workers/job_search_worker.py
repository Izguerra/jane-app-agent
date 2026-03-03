"""
Job Search Worker

Autonomous agent that searches for job listings matching user criteria.
"""

import logging
import os
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from backend.services.worker_service import WorkerService
from backend.prompts.worker_prompts import get_worker_prompt
from backend.tools.web_search import get_web_search_tool

logger = logging.getLogger("job-search-worker")

class JobSearchWorker:
    """
    Job Search Worker implementation (Real LLM Summary).
    """
    
    @staticmethod
    def execute(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the job search workflow.
        """
        return asyncio.run(JobSearchWorker._execute_async(task_id, input_data, service))

    @staticmethod
    async def _execute_async(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService
    ) -> Dict[str, Any]:
        
        job_title = input_data.get("job_title", "Software Engineer")
        location = input_data.get("location", "Remote")
        experience_level = input_data.get("experience_level", "")
        job_type = input_data.get("job_type", "full-time")
        
        results = {
            "job_title": job_title,
            "location": location,
            "jobs_found": [],
            "summary": "",
            "search_timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 1: Initialize
        service.update_task_status(task_id, status="running", current_step="Initializing search...", steps_completed=1, steps_total=5)
        service.add_task_log(task_id, f"Starting job search for: {job_title} in {location}")
        
        web_search = get_web_search_tool()
        
        # Step 2: Search
        service.update_task_status(task_id, status="running", current_step=f"Searching job boards...", steps_completed=2)
        
        search_queries = [
            f"{job_title} {job_type} positions in {location} {experience_level}"
        ]
            
        all_job_results = []
        for query in search_queries:
            try:
                # Sync tool call, no await
                search_results = web_search.search(query, max_results=10)

                if search_results.get("results"):
                    for result in search_results["results"]:
                        all_job_results.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": result.get("content", ""),
                            "source": result.get("url", "").split("/")[2] if "/" in result.get("url", "") else "Unknown"
                        })
            except Exception as e:
                service.add_task_log(task_id, f"Search error for {query}: {e}", level="warning")

        # Deduplicate
        seen_urls = set()
        unique_jobs = []
        for job in all_job_results:
             if job["url"] not in seen_urls:
                 seen_urls.add(job["url"])
                 unique_jobs.append(job)
        
        results["jobs_found"] = unique_jobs[:10] # Top 10
        
        # Step 3: LLM Analysis & Summary
        service.update_task_status(task_id, status="running", current_step="Analyzing results with AI...", steps_completed=4)
        
        if not unique_jobs:
             results["summary"] = f"No jobs found for {job_title} in {location}."
        else:
            try:
                from backend.lib.ai_client import get_ai_client
                client, model_name = get_ai_client(async_mode=True)
                prompt = get_worker_prompt("job-search", input_data)
                
                # Format jobs for LLM
                job_list_text = "\n".join([f"- {j['title']} at {j['source']}: {j['url']}\n  Snippet: {j['snippet'][:150]}..." for j in unique_jobs[:5]])
                
                user_msg = f"Here are the search results found:\n{job_list_text}\n\nPlease analyze and verify if they match the user's criteria. Flag any issues."
                
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_msg}
                    ]
                )
                results["summary"] = response.choices[0].message.content
            except Exception as e:
                service.add_task_log(task_id, f"LLM Summary failed: {e}", level="error")
                results["summary"] = "Found jobs, but failed to generate AI summary."

        # Step 4: Done
        service.update_task_status(task_id, status="completed", current_step="Done", steps_completed=5)
        
        return results
