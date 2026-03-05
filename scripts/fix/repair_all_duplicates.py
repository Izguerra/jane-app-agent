
from backend.database import SessionLocal
from backend.models_db import Customer, Communication, Appointment
from sqlalchemy import func

def repair_duplicates():
    db = SessionLocal()
    try:
        # Find all customers with the same email
        # Group by email, having count > 1
        duplicates = db.query(Customer.email, func.count(Customer.id))\
            .filter(Customer.email.isnot(None))\
            .group_by(Customer.email)\
            .having(func.count(Customer.id) > 1)\
            .all()
            
        print(f"Found {len(duplicates)} duplicate sets by email.")
        
        for email, count in duplicates:
            print(f"Processing {email} ({count} records)...")
            records = db.query(Customer).filter(Customer.email == email).order_by(Customer.created_at).all()
            
            # Strategy: Keep the OLDEST record as "Original" (or the one with most data?)
            # Usually we want to keep the one that is "Real".
            # If all are "Real", keep the oldest.
            # However, if we have a Guest and a Real, the Guest usually has NO email.
            # But here we are grouping by EMAIL. So these are multiple records WITH email.
            # This happens if a Guest was "converted" (got email) but NOT merged (new record created).
            
            # We keep the one with the MOST history or just the FIRST one?
            # Let's keep the FIRST one created as the master, merge others into it.
            master = records[0]
            others = records[1:]
            
            print(f"  Merging {len(others)} into Master: {master.id} ({master.first_name})")
            
            for other in others:
                # Reassign Communications
                db.query(Communication).filter(Communication.customer_id == other.id).update(
                    {"customer_id": master.id}
                )
                # Reassign Appointments
                db.query(Appointment).filter(Appointment.customer_id == other.id).update(
                    {"customer_id": master.id}
                )
                
                # Mark as converted
                other.status = "converted"
                other.converted_to_id = master.id
                print(f"  Marked {other.id} as converted.")

        # --- NEW: Merge Guests (No Email) by Name ---
        # Find Guests (no email)
        guests = db.query(Customer).filter(Customer.email == None).all()
        for guest in guests:
            if not guest.first_name or not guest.last_name:
                continue
                
            # Find Potential Real Match (Same Name, Has Email)
            real_match = db.query(Customer).filter(
                Customer.first_name == guest.first_name,
                Customer.last_name == guest.last_name,
                Customer.email != None,
                Customer.status != 'converted'
            ).first()
            
            if real_match:
                print(f"Found Guest-Real Match by Name: {guest.first_name} {guest.last_name}")
                print(f"  Guest: {guest.id} (Phone: {guest.phone})")
                print(f"  Real: {real_match.id} (Email: {real_match.email})")
                
                # Merge logic
                db.query(Communication).filter(Communication.customer_id == guest.id).update({"customer_id": real_match.id})
                db.query(Appointment).filter(Appointment.customer_id == guest.id).update({"customer_id": real_match.id})
                
                guest.status = "converted"
                guest.converted_to_id = real_match.id
                print(f"  Merged Guest {guest.id} into Real {real_match.id}")

        print("Committing...")
        db.commit()
        print("Done.")
        
        # Specific fix for the May Doe Guest (who has NO email)
        # IDs from debug output:
        # Guest: cus_hjkv10itrw744n2t (No email, phone=guest_may_doe)
        # Real: cus_zto6n3hi0ntmc991 (mayd@test.com)
        
        guest_id = "cus_hjkv10itrw744n2t"
        real_id = "cus_zto6n3hi0ntmc991"
        
        guest = db.query(Customer).filter(Customer.id == guest_id).first()
        real = db.query(Customer).filter(Customer.id == real_id).first()
        
        if guest and real and guest.status != 'converted':
            print(f"Performing specific merge for May Doe Guest {guest.id} -> {real.id}")
            db.query(Communication).filter(Communication.customer_id == guest.id).update({"customer_id": real.id})
            db.query(Appointment).filter(Appointment.customer_id == guest.id).update({"customer_id": real.id})
            guest.status = "converted"
            guest.converted_to_id = real.id
            db.commit()
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair_duplicates()
