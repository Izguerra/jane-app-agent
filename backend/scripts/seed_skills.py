from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models_db import Skill
from backend.lib.id_service import IdService

def seed_skills():
    db = SessionLocal()
    try:
        skills_data = [
            # 🔍 Research & Intelligence (4)
            {
                "name": "Web Research",
                "slug": "web-research",
                "category": "Research",
                "description": "Search the web during calls/chats for real-time info",
                "icon": "Globe",
                "instructions": "Use the web_search tool to find accurate and up-to-date information requested by the user. Summarize findings clearly.",
                "allowed_tools": ["web_search"]
            },
            {
                "name": "Lead Research",
                "slug": "lead-research",
                "category": "Research",
                "description": "Deep-dive a lead's company before or during calls",
                "icon": "UserSearch",
                "instructions": "Research the caller's company or business background using web_search. Focus on services, size, and recent news to build rapport.",
                "allowed_tools": ["web_search", "search_customers"]
            },
            {
                "name": "Competitor Analysis",
                "slug": "competitor-analysis",
                "category": "Research",
                "description": "Research competitors' pricing and features",
                "icon": "Compare",
                "instructions": "Research competitor offerings using web_search. Compare pricing, features, and positioning to help the user handle competitive conversations.",
                "allowed_tools": ["web_search"]
            },
            {
                "name": "Market Intelligence",
                "slug": "market-intelligence",
                "category": "Research",
                "description": "Gather industry trends and market data",
                "icon": "TrendingUp",
                "instructions": "Gather industry trends and news using web_search. Provide high-level market context to support business discussions.",
                "allowed_tools": ["web_search"]
            },
            # 💬 Communication & Outreach (5)
            {
                "name": "Email Composer",
                "slug": "email-composer",
                "category": "Communication",
                "description": "Draft and send professional emails",
                "icon": "Mail",
                "instructions": "Draft professional emails based on conversation outcomes. Use the send_email tool when requested or appropriate for follow-up.",
                "allowed_tools": ["send_email"]
            },
            {
                "name": "SMS Messaging",
                "slug": "sms-messaging",
                "category": "Communication",
                "description": "Send SMS follow-ups and reminders",
                "icon": "MessageSquare",
                "instructions": "Send SMS confirmations or follow-up messages using the send_sms tool. Keep messages concise and action-oriented.",
                "allowed_tools": ["send_sms"]
            },
            {
                "name": "Follow-Up Scheduler",
                "slug": "follow-up-scheduler",
                "category": "Communication",
                "description": "Auto-schedule follow-up touchpoints",
                "icon": "CalendarClock",
                "instructions": "Identify the need for a follow-up and use calendar/CRM tools to schedule a touchpoint. Ensure the user is notified of the next step.",
                "allowed_tools": ["create_event", "update_customer"]
            },
            {
                "name": "Objection Handler",
                "slug": "objection-handler",
                "category": "Communication",
                "description": "Recognize and handle sales objections",
                "icon": "ShieldAlert",
                "instructions": "Recognize verbal objections and search the knowledge base for approved rebuttals and handling strategies. Remain polite and informative.",
                "allowed_tools": ["search_knowledge_base"]
            },
            {
                "name": "Multi-Language",
                "slug": "multi-language",
                "category": "Communication",
                "description": "Handle conversations in multiple languages",
                "icon": "Languages",
                "instructions": "Detect the speaker's language and respond fluently. Use the translation worker for complex translations if necessary.",
                "allowed_tools": ["translate_text"]
            },
            # 📊 CRM & Sales (4)
            {
                "name": "Lead Qualifier",
                "slug": "lead-qualifier",
                "category": "Sales",
                "description": "Ask qualifying questions and score leads",
                "icon": "UserCheck",
                "instructions": "Ask predefined qualifying questions. Evaluate responses to score the lead 1-10. Update the CRM status accordingly.",
                "allowed_tools": ["update_customer", "search_knowledge_base"]
            },
            {
                "name": "Deal Manager",
                "slug": "deal-manager",
                "category": "Sales",
                "description": "Create and update sales deals",
                "icon": "DollarSign",
                "instructions": "Create or update deals based on conversation outcomes. Set appropriate deal stages and estimated values.",
                "allowed_tools": ["create_deal", "update_deal"]
            },
            {
                "name": "Customer Profiler",
                "slug": "customer-profiler",
                "category": "Sales",
                "description": "Build rich profiles from conversation data",
                "icon": "UserPlus",
                "instructions": "Extract key facts, preferences, and details from the conversation to build a comprehensive customer profile in the CRM.",
                "allowed_tools": ["update_customer", "search_customers"]
            },
            {
                "name": "Appointment Booker",
                "slug": "appointment-booker",
                "category": "Sales",
                "description": "Book and modify appointments",
                "icon": "Calendar",
                "instructions": "Check availability and book appointments using calendar tools. Confirm details with the customer before finalizing.",
                "allowed_tools": ["get_availability", "create_event"]
            },
            # 📄 Content & Documents (5)
            {
                "name": "Content Writer",
                "slug": "content-writer",
                "category": "Content",
                "description": "Generate marketing and social media copy",
                "icon": "PenTool",
                "instructions": "Generate blog posts, social media updates, or marketing copy based on business requirements and brand voice.",
                "allowed_tools": []
            },
            {
                "name": "Document Generator",
                "slug": "document-generator",
                "category": "Content",
                "description": "Create proposals and SOPs from templates",
                "icon": "FileText",
                "instructions": "Generate formal documents like proposals or quotes from standard templates using conversation data.",
                "allowed_tools": ["create_file"]
            },
            {
                "name": "FAQ Builder",
                "slug": "faq-builder",
                "category": "Content",
                "description": "Auto-build FAQ from common questions",
                "icon": "HelpCircle",
                "instructions": "Identify frequently asked questions during interactions and add them to a draft FAQ document for review.",
                "allowed_tools": ["update_knowledge_base"]
            },
            {
                "name": "Presentation Creator",
                "slug": "presentation-creator",
                "category": "Content",
                "description": "Create branded slide decks and proposals",
                "icon": "Presentation",
                "instructions": "Generate structured slide content for presentations or LinkedIn carousels using branded styles.",
                "allowed_tools": ["create_file"]
            },
            {
                "name": "SOP Generator",
                "slug": "sop-generator",
                "category": "Content",
                "description": "Create runbooks and decision trees",
                "icon": "ClipboardList",
                "instructions": "Formalize processes discussed into step-by-step SOP documents, runbooks, or decision trees.",
                "allowed_tools": ["create_file"]
            },
            # 🛠️ Workflow & Automation (6)
            {
                "name": "Task Dispatcher",
                "slug": "task-dispatcher",
                "category": "Workflow",
                "description": "Delegate background tasks to workers",
                "icon": "Zap",
                "instructions": "Recognize when a task should be handled by an external worker and dispatch it with the necessary context.",
                "allowed_tools": ["dispatch_worker"]
            },
            {
                "name": "Campaign Manager",
                "slug": "campaign-manager",
                "category": "Workflow",
                "description": "Manage drip campaigns and reporting",
                "icon": "BarChart2",
                "instructions": "Monitor campaign status, start or pause drips, and report on engagement metrics extracted from CRM data.",
                "allowed_tools": ["search_campaigns", "update_campaign"]
            },
            {
                "name": "Data Entry",
                "slug": "data-entry",
                "category": "Workflow",
                "description": "Automate CRM and form filling",
                "icon": "Database",
                "instructions": "Extract structured data from logs or transcripts and enter it directly into the CRM or external forms.",
                "allowed_tools": ["update_customer", "update_deal"]
            },
            {
                "name": "Escalation Router",
                "slug": "escalation-router",
                "category": "Workflow",
                "description": "Route to human agents when needed",
                "icon": "ArrowUpRight",
                "instructions": "Identify when a request is too complex and route the conversation to the appropriate human team member.",
                "allowed_tools": ["route_to_human"]
            },
            {
                "name": "Custom Skill Creator",
                "slug": "custom-skill-creator",
                "category": "Workflow",
                "description": "Define reusable skills via guided flow",
                "icon": "PlusCircle",
                "instructions": "Guide the user through creating their own specialized skill, defining instructions and allowed tools.",
                "allowed_tools": []
            },
            {
                "name": "Event Triggers",
                "slug": "event-triggers",
                "category": "Workflow",
                "description": "Automate 'When X -> Y' action chains",
                "icon": "Activity",
                "instructions": "Set up or execute automation chains triggered by specific conversational events or status changes.",
                "allowed_tools": ["dispatch_worker"]
            }
        ]
        
        for data in skills_data:
            existing = db.query(Skill).filter(Skill.slug == data["slug"]).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                skill = Skill(
                    id=IdService.generate("skll"),
                    is_system=True,
                    **data
                )
                db.add(skill)
        
        db.commit()
        print(f"Successfully seeded {len(skills_data)} system skills.")
    except Exception as e:
        import traceback
        print(f"Error seeding skills: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_skills()
