
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

import bcrypt

# Add current directory to path so we can import backend modules
sys.path.append(os.getcwd())

# from backend.auth import get_password_hash # Removed import

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    sys.exit(1)

# Helper for IDs
import random
import string
def generate_id(prefix, length=12):
    chars = string.ascii_lowercase + string.digits
    return prefix + ''.join(random.choice(chars) for _ in range(length))

def create_test_user():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(text("SELECT id FROM users WHERE email = 'test@test.com'")).fetchone()
        if result:
            print(f"User test@test.com already exists (ID: {result[0]}).")
            
            # Ensure team member role is owner
            user_id = result[0]
            conn.execute(text("UPDATE team_members SET role = 'owner' WHERE user_id = :uid"), {"uid": user_id})
            conn.commit()
            print("Updated role to owner.")
            return

        print("Creating test user...")
        user_id = generate_id('usr_')
        password_hash = get_password_hash('password')
        
        # Create User
        conn.execute(text("""
            INSERT INTO users (id, email, password_hash, role, name)
            VALUES (:id, 'test@test.com', :ph, 'owner', 'Test User')
        """), {"id": user_id, "ph": password_hash})
        
        # Create Team
        team_id = generate_id('tm_')
        conn.execute(text("""
            INSERT INTO teams (id, name, subscription_status)
            VALUES (:id, 'Test Team', 'active')
        """), {"id": team_id})
        
        # Create Team Member
        conn.execute(text("""
            INSERT INTO team_members (id, user_id, team_id, role)
            VALUES (:id, :uid, :tid, 'owner')
        """), {"id": generate_id('mem_'), "uid": user_id, "tid": team_id})

        # Create Workspace
        workspace_id = generate_id('ws_')
        conn.execute(text("""
            INSERT INTO workspaces (id, team_id, name)
            VALUES (:id, :tid, 'Test Workspace')
        """), {"id": workspace_id, "tid": team_id})
        
        conn.commit()
        print(f"User created successfully. ID: {user_id}")
        print(f"Team ID: {team_id}")
        print(f"Workspace ID: {workspace_id}")

if __name__ == "__main__":
    create_test_user()
