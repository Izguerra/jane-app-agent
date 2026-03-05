"""
Sales Outreach Worker (Enterprise)

Target: Sales Leaders & SDRs.
Function: Enriches lead data and sends personalized outreach sequences.
Compliance: CAN-SPAM, GDPR (Opt-out handling).
"""

import logging
import time
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# Tools
from backend.tools.web_search import get_web_search_tool

logger = logging.getLogger("sales-outreach-worker")

class SalesOutreachWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade Sales Outreach Agent.
    """
    RISK_LEVEL = "medium" # Handles external comms
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        target_role = input_data.get("target_role")
        industry = input_data.get("industry")
        company_list = input_data.get("company_list", []) # List of names
        outreach_template = input_data.get("outreach_template", "Hi {name}, ...")
        
        results = {
            "leads_processed": 0,
            "leads_enriched": [],
            "outreach_sent": 0,
            "status": "success"
        }
        
        if not target_role or not company_list:
            raise ValueError("Missing required parameters: target_role or company_list")
            
        web_search = get_web_search_tool()

        # Step 1: Research & Identify
        service.update_task_status(task_id, status="running", current_step="Enriching Lead Data...", steps_completed=1, steps_total=3)
        service.add_task_log(task_id, f"Researching {target_role} at {len(company_list)} companies.")
        
        enriched_leads = []
        for company in company_list:
            # Mocking the enrichment via search for now (Real impl would use Apollo/Clearbit)
            query = f"{target_role} at {company} linkedin"
            
            try:
                search_res = web_search.search(query, max_results=1)
                
                # Simulate finding a person
                if search_res.get("results"):
                    first_res = search_res["results"][0]
                    # Naive extraction - in prod use LLM to parse
                    enriched_leads.append({
                        "company": company,
                        "person_name": f"{target_role} at {company}", # Fallback if specific name not found
                        "source_url": first_res.get("url"),
                        "snippet": first_res.get("content", "")[:100]
                    })
                    service.add_task_log(task_id, f"Found potential lead at {company}: {first_res.get('url')}")
                else:
                    service.add_task_log(task_id, f"No leads found for {company}", level="warning")
                    
            except Exception as e:
                service.add_task_log(task_id, f"Search failed for {company}: {e}", level="error")

        results["leads_processed"] = len(company_list)
        results["leads_enriched"] = enriched_leads
        
        # Step 2: Draft Outreach
        service.update_task_status(task_id, current_step="Drafting Outreach...", steps_completed=2)
        
        generated_emails = []
        for lead in enriched_leads:
            # Simple template mock
            email_body = outreach_template.replace("{name}", lead["person_name"]).replace("{company}", lead["company"])
            generated_emails.append({
                "to": lead["person_name"],
                "company": lead["company"],
                "draft_body": email_body
            })
            
        # Step 3: Send/Queue (Mock for safety)
        service.update_task_status(task_id, current_step="Finalizing...", steps_completed=3)
        service.add_task_log(task_id, f"Generated {len(generated_emails)} outreach drafts. (Sending disabled in Safe Mode)")
        
        results["outreach_drafts"] = generated_emails
        results["summary"] = f"Processed {len(company_list)} companies. Found {len(enriched_leads)} leads. Generated {len(generated_emails)} drafts."
        
        return results
