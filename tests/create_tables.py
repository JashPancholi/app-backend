# create_tables.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TIMESTAMP, func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("Set DATABASE_URL in environment or .env")

engine = create_engine(DATABASE_URL, future=True)

meta = MetaData()

# Generic leaderboard table if you don't have models yet
leaderboard = Table(
    "leaderboard", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("username", String(128), nullable=True),
    Column("points", Integer, nullable=False, default=0),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

meta.create_all(engine)
print("[LOG] Tables created (or already existed).")
