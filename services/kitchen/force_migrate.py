from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Direct Supabase connection
DB_URL = "postgresql://postgres.mlvnacjtnfrfjehghqlz:letsconnectnowhuh@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE courses ADD COLUMN IF NOT EXISTS language VARCHAR"))
        conn.commit()
        print("✓ Added language column to courses table")
    except Exception as e:
        print(f"Migration error: {e}")
