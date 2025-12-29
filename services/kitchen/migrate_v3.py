from src.db.engine import engine, Base
from src.db.models import KitchenStatus
from sqlalchemy import text

def migrate():
    print("Migrating V3 (KitchenStatus)...")
    # Quickest way: just create all tables, SQLAlchemy skips existing
    # But we want to ensure table exists
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    migrate()
