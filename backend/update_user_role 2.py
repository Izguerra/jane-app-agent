from backend.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    email = "Customer1@hotmail.com"
    new_role = "member" 
    
    print(f"Updating role for {email} to '{new_role}'...")

    # Update users table
    db.execute(text("UPDATE users SET role = :role WHERE email = :email"), {"role": new_role, "email": email})
    
    # Get user ID to update team_members
    result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).fetchone()
    
    if result:
        user_id = result[0]
        # Update team_members table
        db.execute(text("UPDATE team_members SET role = :role WHERE user_id = :uid"), {"role": new_role, "uid": user_id})
        
        db.commit()
        print(f"SUCCESS: Updated role to '{new_role}' for user {email} (ID: {user_id})")
        
        # Verify the update
        verify_user = db.execute(text("SELECT role FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
        verify_member = db.execute(text("SELECT role FROM team_members WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        print(f"VERIFICATION: User Role={verify_user[0]}, Team Role={verify_member[0]}")
        
    else:
        print(f"User {email} not found.")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
