import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db.engine import engine
from sqlalchemy import text

def migrate():
    print("Running manual migration...")
    with engine.connect() as conn:
        try:
            print("Adding 'category' to articles...")
            conn.execute(text("ALTER TABLE articles ADD COLUMN IF NOT EXISTS category TEXT;"))
            
            print("Adding 'category' to courses...")
            conn.execute(text("ALTER TABLE courses ADD COLUMN IF NOT EXISTS category TEXT;"))
            
            conn.commit()
            print("Migration success!")
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
