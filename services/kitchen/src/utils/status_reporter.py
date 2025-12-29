import time
from sqlalchemy.orm import Session
from src.db.models import KitchenStatus

def update_kitchen_status(db: Session, status: str, progress: int, is_active: bool = True):
    """Upsert the singleton status row"""
    try:
        # Check for existing row
        row = db.query(KitchenStatus).first()
        if not row:
            row = KitchenStatus(status_text=status, progress_percent=progress, is_active=is_active)
            db.add(row)
        else:
            row.status_text = status
            row.progress_percent = progress
            row.is_active = is_active
        
        db.commit()
    except Exception as e:
        print(f"Status Update Failed: {e}")
        db.rollback()
