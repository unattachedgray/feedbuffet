import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv('services/kitchen/.env')
url = os.getenv("DATABASE_URL")
print(f"URL: {url}")

try:
    engine = sqlalchemy.create_engine(url)
    with engine.connect() as conn:
        print("Connected!")
except Exception as e:
    print(f"Error: {e}")
