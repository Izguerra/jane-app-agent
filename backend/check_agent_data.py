from backend.database import SessionLocal
from backend.models_db import Communication, Agent, User, Customer

def check_data():
    db = SessionLocal()
    try:
        # Get one customer that likely has data (or just list all comms)
        print("Checking Communications...")
        comms = db.query(Communication).limit(10).all()
        
        for comm in comms:
            print(f"Comm ID: {comm.id}, Type: {comm.type}, Agent ID: {comm.agent_id}")
            
            if comm.agent_id:
                agent = db.query(Agent).filter(Agent.id == comm.agent_id).first()
                user = db.query(User).filter(User.id == comm.agent_id).first()
                
                if agent:
                    print(f"  -> Found in Agent table: {agent.name}")
                elif user:
                    print(f"  -> Found in User table: {user.name}")
                else:
                    print(f"  -> NOT FOUND in either table")
            else:
                print("  -> No Agent ID")
                
        print("\nChecking Users...")
        users = db.query(User).limit(5).all()
        for u in users:
            print(f"User ID: {u.id}, Name: {u.name}")

        print("\nChecking Agents...")
        agents = db.query(Agent).limit(5).all()
        for a in agents:
            print(f"Agent ID: {a.id}, Name: {a.name}")

    finally:
        db.close()

if __name__ == "__main__":
    check_data()
