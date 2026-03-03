"""
Seed Enterprise Workers

Populates the 'worker_templates' table with the 15 Enterprise Worker definitions.
This allows the Orchestrator (Chat/Voice) to discover and dispatch them.
"""

import sys
import os
import logging
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.database import SessionLocal
from backend.models_db import WorkerTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# WORKER DEFINITIONS
# =============================================================================

WORKERS = [
    # --- BATCH A: Customer & Sales ---
    {
        "slug": "sales-outreach",
        "name": "Sales Outreach Worker",
        "category": "sales",
        "description": "Autonomous sales agent that enriches leads and sends personalized outreach sequences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_role": {"type": "string", "description": "e.g. VP of Marketing"},
                "industry": {"type": "string"},
                "company_list": {"type": "array", "items": {"type": "string"}},
                "outreach_template": {"type": "string"}
            },
            "required": ["target_role"]
        },
        "icon": "zap",
        "color": "blue"
    },
    {
        "slug": "faq-resolution",
        "name": "FAQ Resolution Worker",
        "category": "support",
        "description": "Answers customer questions using the internal Knowledge Base and drafts responses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "customer_id": {"type": "string"}
            },
            "required": ["question"]
        },
        "icon": "help-circle",
        "color": "green"
    },
    {
        "slug": "meeting-coordination",
        "name": "Meeting Coordination Worker",
        "category": "productivity",
        "description": "Coordinates complex scheduling, finds mutual availability, and sends calendar invites.",
        "input_schema": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}},
                "duration_minutes": {"type": "integer", "default": 30},
                "topic": {"type": "string"}
            },
            "required": ["participants"]
        },
        "icon": "calendar",
        "color": "orange"
    },

    # --- BATCH B: Operations & HR ---
    {
        "slug": "hr-onboarding",
        "name": "HR & Onboarding Worker",
        "category": "hr",
        "description": "Manages candidate screening, offer letters, and new employee onboarding checklists.",
        "input_schema": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string"},
                "role": {"type": "string"},
                "action": {"type": "string", "enum": ["screen", "offer", "onboard"]}
            },
            "required": ["candidate_name", "action"]
        },
        "icon": "users",
        "color": "purple"
    },
    {
        "slug": "order-status",
        "name": "Order Status Worker",
        "category": "support",
        "description": "Retrieves real-time order tracking and shipping updates from E-commerce integrations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {"type": "string"},
                "customer_email": {"type": "string"}
            },
            "required": ["order_number"]
        },
        "icon": "package",
        "color": "yellow"
    },
    {
        "slug": "payment-billing",
        "name": "Payment & Billing Worker",
        "category": "finance",
        "description": "Handles invoice generation, payment status checks, and refund processing (PCI Compliant).",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "action": {"type": "string", "enum": ["check_status", "refund", "invoice"]},
                "amount": {"type": "number"}
            },
            "required": ["action"]
        },
        "icon": "credit-card",
        "color": "red"
    },
    {
        "slug": "it-support",
        "name": "IT Support Worker",
        "category": "it",
        "description": "Internal IT agent for password resets, software provisioning, and troubleshooting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_type": {"type": "string", "enum": ["password_reset", "software", "hardware"]},
                "employee_id": {"type": "string"}
            },
            "required": ["issue_type"]
        },
        "icon": "monitor",
        "color": "gray"
    },

    # --- RETAINED LEGACY (For general use) ---
    {
        "slug": "job-search",
        "name": "Individual Job Search",
        "category": "general",
        "description": "Helps you find personal job opportunities.",
        "input_schema": {}, # Schema logic is handled in code for legacy
        "icon": "briefcase",
        "color": "blue"
    },
    {
        "slug": "lead-research-legacy",
        "name": "General Lead Research",
        "category": "general",
        "description": "General purpose web research agent.",
        "input_schema": {},
        "icon": "search",
        "color": "blue"
    },
    
    # ... Add placeholders for the other 8 Enterprise workers to verify the list ...
    {
       "slug": "intelligent-routing",
       "name": "Intelligent Routing Worker",
       "category": "operations",
       "description": "Routes tickets and calls based on sentiment and intent analysis.",
       "input_schema": {},
       "icon": "shuffle",
       "color": "indigo" 
    },
    {
       "slug": "data-entry",
       "name": "Data Entry Worker",
       "category": "operations",
       "description": "Automates CRM updates and data enrichment.",
       "input_schema": {},
       "icon": "database",
       "color": "cyan" 
    },
    {
       "slug": "document-processing",
       "name": "Document Processing Worker",
       "category": "operations",
       "description": "OCR and classification of business documents.",
       "input_schema": {},
       "icon": "file-text",
       "color": "orange" 
    },
    {
       "slug": "content-moderation",
       "name": "Content Moderation Worker",
       "category": "security",
       "description": "Automated moderation of user-generated content.",
       "input_schema": {},
       "icon": "shield",
       "color": "red" 
    },
    {
       "slug": "sentiment-escalation",
       "name": "Sentiment & Escalation Worker",
       "category": "support",
       "description": "Detects angry customers and triggers urgent escalation.",
       "input_schema": {},
       "icon": "heart",
       "color": "pink" 
    },
    {
       "slug": "translation-localization",
       "name": "Translation Worker",
       "category": "general",
       "description": "Enterprise-grade translation and localization.",
       "input_schema": {},
       "icon": "globe",
       "color": "teal" 
    },
    {
       "slug": "compliance-risk",
       "name": "Compliance & Risk Worker",
       "category": "security",
       "description": "Monitors system usage for compliance violations (SOC 2).",
       "input_schema": {},
       "icon": "lock",
       "color": "black" 
    },
    {
       "slug": "sms-messaging",
       "name": "SMS Messaging Agent",
       "category": "productivity",
       "description": "Sends SMS or WhatsApp messages to customers or team members.",
       "input_schema": {
           "type": "object",
           "properties": {
               "recipient_number": {"type": "string", "description": "Phone number with country code"},
               "message": {"type": "string"},
               "force_whatsapp": {"type": "boolean", "default": False}
           },
           "required": ["recipient_number", "message"]
       },
       "icon": "message-square",
       "color": "green"
    }
]

def seed_workers():
    db = SessionLocal()
    try:
        logger.info("Starting Enterprise Worker Seeding...")
        
        count_new = 0
        count_updated = 0
        
        for w_def in WORKERS:
            try:
                # Check if exists by slug
                existing = db.query(WorkerTemplate).filter(WorkerTemplate.slug == w_def["slug"]).first()
                
                if existing:
                    logger.info(f"Updating worker: {w_def['slug']}")
                    existing.name = w_def["name"]
                    existing.description = w_def["description"]
                    existing.category = w_def["category"]
                    existing.parameter_schema = w_def["input_schema"]
                    existing.icon = w_def["icon"]
                    existing.color = w_def["color"]
                    count_updated += 1
                else:
                    logger.info(f"Creating NEW worker: {w_def['slug']}")
                    new_worker = WorkerTemplate(
                        id=str(uuid4()),
                        slug=w_def["slug"],
                        name=w_def["name"],
                        description=w_def["description"],
                        category=w_def["category"],
                        parameter_schema=w_def["input_schema"],
                        icon=w_def["icon"],
                        color=w_def["color"],
                        is_active=True
                    )
                    db.add(new_worker)
                    count_new += 1
                
                # Commit after each one to isolate failures and ensure persistence
                db.commit()
                
            except Exception as inner_e:
                logger.error(f"Failed to process worker {w_def['slug']}: {inner_e}")
                db.rollback()
                continue
        
        logger.info(f"Seeding Complete. New: {count_new}, Updated: {count_updated}")
        
    except Exception as e:
        logger.error(f"Seeding failed globally: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_workers()
