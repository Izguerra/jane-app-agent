from backend.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    email = "Customer1@hotmail.com"
    # Use raw SQL since User model might not be defined in Python ORM
    result = db.execute(text("SELECT id, name, email, role FROM users WHERE email = :email"), {"email": email}).fetchone()
    
    if result:
        print(f"User Found: ID={result[0]}, Name={result[1]}, Email={result[2]}, Role={result[3]}")
        
        # Check team membership
        member = db.execute(text("SELECT team_id, role FROM team_members WHERE user_id = :uid"), {"uid": result[0]}).fetchone()
        if member:
            print(f"Team Member Role: {member[1]}")
            print(f"Team ID: {member[0]}")
        else:
            print("User is not a member of any team.")
    else:
        print(f"User with email {email} NOT FOUND.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
