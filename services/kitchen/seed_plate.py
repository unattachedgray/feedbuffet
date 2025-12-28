from src.db.engine import SessionLocal
from src.db.models import Plate
import uuid
import json

def seed_plate():
    db = SessionLocal()
    try:
        # Check if any plate exists
        existing = db.query(Plate).first()
        if existing:
            print(f"Plate already exists: {existing.id}")
            return existing.id

        new_plate = Plate(
            id=str(uuid.uuid4()),
            name="Tech Daily",
            visibility="public",
            rules_json=json.dumps({"description": "Latest tech news"})
        )
        db.add(new_plate)
        db.commit()
        db.refresh(new_plate)
        print(f"Created Plate: {new_plate.id}")
        return new_plate.id
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_plate()
