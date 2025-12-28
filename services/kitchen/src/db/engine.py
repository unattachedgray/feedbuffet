import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment.")

# Robustly handle connection string
try:
    # Try to parse securely
    from sqlalchemy.engine.url import make_url
    
    # If DATABASE_URL is raw and contains unencoded chars, make_url might fail or parse wrong.
    # But usually it's best to rely on standard parsing.
    # We will try to rely on make_url.
    # If the user put unencoded chars in .env, we might need to handle it.
    
    # Let's try to assume the env var is "mostly" correct but maybe needs prefix fix.
    
    url_obj = make_url(DATABASE_URL)
    
    if url_obj.drivername == 'postgres':
        url_obj = url_obj.set(drivername='postgresql')
        
    # Fix host if needed (the missing db. case). 
    # Only do this if it looks like a project reference (contains supabase.co but NOT pooler)
    if url_obj.host and 'supabase.co' in url_obj.host and 'pooler' not in url_obj.host and not url_obj.host.startswith('db.'):
         url_obj = url_obj.set(host='db.' + url_obj.host)
         
    engine = create_engine(url_obj, echo=False)

except Exception as e:
    print(f"Error creating engine url: {e}")
    # Fallback
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
