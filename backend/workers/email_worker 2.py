"""
Email Process Worker

Autonomous agent that manages mailbox interactions:
- Checking/Searching emails
- Summarizing threads
- Drafting and sending replies
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.tools.mailbox_tools import MailboxTools
from backend.prompts.worker_prompts import get_worker_prompt

logger = logging.getLogger("email-worker")

class EmailWorker:
    """
    Email Worker implementation (Real LLM).
    """;
    
    @staticmethod
    def execute(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the email workflow using Mistral.
        """
        return asyncio.run(EmailWorker._execute_async(task_id, input_data, service))

    @staticmethod
    async def _execute_async(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService
    ) -> Dict[str, Any]:
        
        action = input_data.get("action", "search")
        
        # Auto-infer send action if missing but parameters exist
        if action == "search" and (input_data.get("recipient") or input_data.get("to")):
             logger.info("Auto-inferring action='send' based on input parameters")
             action = "send"
             
        query = input_data.get("query", "")
        scope = input_data.get("scope", "week")
        limit = input_data.get("limit", 10)
        
        # Get workspace ID
        task = service.get_task(task_id)
        if not task:
            raise Exception("Task context lost")
        workspace_id = task.workspace_id
        
        # Init Tools
        # Init Client
        try:
            from backend.lib.ai_client import get_ai_client
            client, model_name = get_ai_client(async_mode=True)
        except Exception as e:
            raise Exception(f"Failed to get AI client for email: {e}")

        results = {
            "processed_count": 0,
            "action": action,
            "emails_found": [],
            "summary": ""
        }
        
        # Step 1: Fetch Emails
        service.update_task_status(task_id, status="running", current_step="Fetching emails...", steps_completed=1, steps_total=4)
        
        # Instantiate MailboxTools
        mailbox = MailboxTools(workspace_id=workspace_id)
        
        # Use simple logic to get emails
        if query:
            raw_emails = mailbox.search_emails(query, limit=limit)
        elif scope == "unread":
            raw_emails = mailbox.search_emails("is:unread", limit=limit)
        else:
            raw_emails = mailbox.list_emails(limit=limit)
            
        try:
            email_list = json.loads(raw_emails) if isinstance(raw_emails, str) and raw_emails.startswith("[") else []
        except:
             service.add_task_log(task_id, f"Failed to parse email results", level="error")
             return {"error": "Failed to parse emails"}
             
        if not email_list and action != "send":
            service.add_task_log(task_id, "No emails found.")
            results["summary"] = "No emails found matching criteria."
            return results

        service.add_task_log(task_id, f"Found {len(email_list)} emails. Analyzing...")
        
        processed_emails = []
        full_text_context = ""
        
        # Fetch content
        for email in email_list:
            content = email.get("snippet", "")
            # If reply/summarize, try to get full content (mock logic in real app would verify provider)
            # For this agent, snippet is often enough for "search", but "reply" needs context.
            # We'll stick to snippet for speed unless it's very short.
            processed_emails.append({
                "from": email.get("from"),
                "subject": email.get("subject"),
                "content": content
            })
            full_text_context += f"From: {email.get('from')}\nSubject: {email.get('subject')}\nContent: {content}\n---\n"

        results["emails_found"] = processed_emails
        results["processed_count"] = len(processed_emails)

        # Step 2: LLM Processing
        service.update_task_status(task_id, current_step=f"Processing action: {action}...", steps_completed=3)
        
        prompt = get_worker_prompt("email-worker", input_data)
        
        final_summary = ""
        
        if action == "summarize":
            service.add_task_log(task_id, "Summarizing emails with LLM...")
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Here are the emails to summarize:\n{full_text_context}"}
            ]
            response = await client.chat.completions.create(model=model_name, messages=messages)
            final_summary = response.choices[0].message.content

        elif action == "reply":
            service.add_task_log(task_id, "Generating drafts for all results in a single batch...")
            
            emails_to_batch = processed_emails[:5] # Increase to 5 since it's one call
            batch_context = ""
            for i, email in enumerate(emails_to_batch):
                batch_context += f"Email #{i+1}:\nFrom: {email['from']}\nSubject: {email['subject']}\nContent: {email['content']}\n---\n"
            
            batch_prompt = f"""
            Analyze these {len(emails_to_batch)} emails and provide a concise, professional draft reply for EACH.
            
            Requirements:
            - Tone: Professional & helpful.
            - Sign off as 'SupaAgent'.
            - Include a clear call to action if appropriate.
            
            {batch_context}
            
            Return ONLY a JSON object where keys are "email_1", "email_2", etc. and values are the draft text.
            """
            
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": batch_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                import json
                draft_data = json.loads(response.choices[0].message.content)
                
                drafts_formatted = ""
                for key, draft in draft_data.items():
                    idx = int(key.split("_")[1]) - 1
                    if idx < len(emails_to_batch):
                        email = emails_to_batch[idx]
                        drafts_formatted += f"\n\n### Draft for {email['from']}\n{draft}\n"
                
                final_summary = f"Generated {len(draft_data)} drafts in a single batch:\n{drafts_formatted}"
                service.add_task_log(task_id, f"Successfully batched {len(draft_data)} drafts.")
                
            except Exception as e:
                service.add_task_log(task_id, f"Batch drafting failed: {e}. Falling back to search summary.", level="error")
                final_summary = f"Found {len(processed_emails)} emails, but failed to generate drafts."

        elif action == "send":
            # Direct send capability
            recipient = input_data.get("recipient") or input_data.get("to")
            subject = input_data.get("subject", "No Subject")
            body = input_data.get("body") or input_data.get("message")
            cc = input_data.get("cc") # List expected
            bcc = input_data.get("bcc") # List expected
            
            # Parse is_html
            is_html = input_data.get("is_html", False)
            if isinstance(is_html, str):
                is_html = is_html.lower() == "true"

            if not recipient or not body:
                 return {"error": "Recipient and Body required for sending."}

            service.add_task_log(task_id, f"Sending email to {recipient}...")
            result = mailbox.send_email(
                to_email=recipient, 
                subject=subject, 
                body=body,
                cc=cc if isinstance(cc, list) else ([cc] if cc else None),
                bcc=bcc if isinstance(bcc, list) else ([bcc] if bcc else None),
                is_html=is_html
            )
            final_summary = f"Send Result: {result}"

        else:
             final_summary = f"Found {len(processed_emails)} emails. \n\n" + "\n".join([f"- {e['subject']} ({e['from']})" for e in processed_emails])

        results["summary"] = final_summary
        
        # Step 3: Done
        service.update_task_status(task_id, status="completed", current_step="Done", steps_completed=4)
        
        return results
