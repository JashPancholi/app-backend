# test_connection.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv() 
DATABASE_URL: str = os.getenv("DATABASE_URL") or ""
engine = create_engine(DATABASE_URL, future=True)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()
        print("[LOG] Database connected successfully:", result)
except Exception as e:
    print("[ERROR] Database connection failed:", e)
