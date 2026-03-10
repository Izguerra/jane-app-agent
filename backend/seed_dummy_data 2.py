"""
Seed script to add dummy customer and campaign data for UI testing
"""
from backend.database import SessionLocal
from backend.models_db import Customer, Campaign, Workspace
from datetime import datetime, timedelta
import random

def seed_dummy_data():
    db = SessionLocal()
    
    try:
        # Get the first workspace (assumes you already have one from seed)
        workspace = db.query(Workspace).first()
        if not workspace:
            print("No workspace found. Please run the main seed script first.")
            return
        
        print(f"Using workspace: {workspace.id}")
        
        # Clear existing dummy data
        db.query(Customer).filter(Customer.workspace_id == workspace.id).delete()
        db.query(Campaign).filter(Campaign.workspace_id == workspace.id).delete()
        db.commit()
        
        # Sample customer data
        customer_data = [
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@techcorp.com",
                "phone": "+1-555-0101",
                "company_name": "TechCorp Solutions",
                "plan": "Professional",
                "status": "active",
                "usage_used": 45,
                "usage_limit": 100
            },
            {
                "first_name": "Michael",
                "last_name": "Chen",
                "email": "m.chen@innovate.io",
                "phone": "+1-555-0102",
                "company_name": "Innovate Inc",
                "plan": "Enterprise",
                "status": "active",
                "usage_used": 87,
                "usage_limit": 200
            },
            {
                "first_name": "Emma",
                "last_name": "Davis",
                "email": "emma.d@startuplab.com",
                "phone": "+1-555-0103",
                "company_name": "Startup Lab",
                "plan": "Starter",
                "status": "active",
                "usage_used": 12,
                "usage_limit": 50
            },
            {
                "first_name": "James",
                "last_name": "Wilson",
                "email": "jwilson@enterprise.com",
                "phone": "+1-555-0104",
                "company_name": "Enterprise Global",
                "plan": "Enterprise",
                "status": "active",
                "usage_used": 156,
                "usage_limit": 200
            },
            {
                "first_name": "Sofia",
                "last_name": "Martinez",
                "email": "sofia@creativestudio.com",
                "phone": "+1-555-0105",
                "company_name": "Creative Studio",
                "plan": "Professional",
                "status": "active",
                "usage_used": 67,
                "usage_limit": 100
            },
            {
                "first_name": "David",
                "last_name": "Brown",
                "email": "dbrown@consulting.com",
                "phone": "+1-555-0106",
                "company_name": "Brown Consulting",
                "plan": "Starter",
                "status": "churned",
                "usage_used": 3,
                "usage_limit": 50
            },
            {
                "first_name": "Lisa",
                "last_name": "Anderson",
                "email": "l.anderson@finance.com",
                "phone": "+1-555-0107",
                "company_name": "Finance Partners",
                "plan": "Professional",
                "status": "active",
                "usage_used": 92,
                "usage_limit": 100
            },
            {
                "first_name": "Robert",
                "last_name": "Taylor",
                "email": "rtaylor@legal.com",
                "phone": "+1-555-0108",
                "company_name": "Taylor Legal",
                "plan": "Enterprise",
                "status": "active",
                "usage_used": 178,
                "usage_limit": 200
            },
        ]
        
        # Create customers
        created_at_base = datetime.now() - timedelta(days=90)
        for i, data in enumerate(customer_data):
            customer = Customer(
                workspace_id=workspace.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                phone=data["phone"],
                company_name=data["company_name"],
                plan=data["plan"],
                status=data["status"],
                usage_used=data["usage_used"],
                usage_limit=data["usage_limit"],
                created_at=created_at_base + timedelta(days=i*10)
            )
            db.add(customer)
        
        db.commit()
        print(f"✅ Created {len(customer_data)} customers")
        
        # Sample campaign data
        campaign_data = [
            {
                "name": "Holiday Promotion 2024",
                "description": "End of year special offers and discounts",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=30),
                "target_audience": "All active customers",
                "total_contacts": 450,
                "completed_contacts": 287,
                "success_rate": 64.5
            },
            {
                "name": "Product Launch - AI Features",
                "description": "Introducing new AI-powered automation features",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=15),
                "end_date": datetime.now() + timedelta(days=45),
                "target_audience": "Enterprise & Professional plans",
                "total_contacts": 230,
                "completed_contacts": 145,
                "success_rate": 72.1
            },
            {
                "name": "Customer Feedback Survey",
                "description": "Quarterly satisfaction and feature request survey",
                "status": "completed",
                "start_date": datetime.now() - timedelta(days=60),
                "end_date": datetime.now() - timedelta(days=15),
                "target_audience": "All customers",
                "total_contacts": 580,
                "completed_contacts": 580,
                "success_rate": 58.3
            },
            {
                "name": "Renewal Reminders - Q1",
                "description": "Automated renewal notifications for Q1 subscriptions",
                "status": "scheduled",
                "start_date": datetime.now() + timedelta(days=15),
                "end_date": datetime.now() + timedelta(days=90),
                "target_audience": "Customers with Q1 renewals",
                "total_contacts": 125,
                "completed_contacts": 0,
                "success_rate": 0.0
            },
            {
                "name": "Upsell Campaign - Enterprise",
                "description": "Promote enterprise features to professional tier customers",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=7),
                "end_date": datetime.now() + timedelta(days=60),
                "target_audience": "Professional plan customers",
                "total_contacts": 340,
                "completed_contacts": 89,
                "success_rate": 45.8
            },
            {
                "name": "Win-back Campaign",
                "description": "Re-engage churned customers with special offers",
                "status": "paused",
                "start_date": datetime.now() - timedelta(days=20),
                "end_date": datetime.now() + timedelta(days=40),
                "target_audience": "Churned customers (last 6 months)",
                "total_contacts": 78,
                "completed_contacts": 34,
                "success_rate": 28.5
            },
        ]
        
        # Create campaigns
        for data in campaign_data:
            campaign = Campaign(
                workspace_id=workspace.id,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                target_audience=data["target_audience"],
                total_contacts=data["total_contacts"],
                completed_contacts=data["completed_contacts"],
                success_rate=data["success_rate"],
                created_at=data["start_date"] - timedelta(days=5)
            )
            db.add(campaign)
        
        db.commit()
        print(f"✅ Created {len(campaign_data)} campaigns")
        
        print("\n🎉 Dummy data seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_dummy_data()
