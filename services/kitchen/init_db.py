from src.db.engine import engine, Base
from src.db.models import *  # Import all models so they are registered

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init_db()
