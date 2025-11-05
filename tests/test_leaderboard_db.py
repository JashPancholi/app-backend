# tests/test_leaderboard_db.py
import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv() 
DATABASE_URL: str = os.getenv("DATABASE_URL") or ""
engine = create_engine(DATABASE_URL, future=True)

@pytest.fixture(scope="module")
def conn():
    conn = engine.connect()
    yield conn
    conn.close()

def test_insert_and_rank(conn):
    # Clean test entries
    conn.execute(text("DELETE FROM leaderboard WHERE user_id >= 999"))
    conn.commit()

    # Insert sample users
    data = [
        {"u": 999, "n": "anushree", "p": 15},
        {"u": 1000, "n": "beta", "p": 30},
        {"u": 1001, "n": "gamma", "p": 20},
    ]
    conn.execute(
        text("INSERT INTO leaderboard (user_id, username, points) VALUES (:u,:n,:p)"),
        data,
    )
    conn.commit()

    res = conn.execute(
        text("SELECT username, points FROM leaderboard ORDER BY points DESC")
    ).fetchall()

    assert res[0].points >= res[1].points
    print("[LOG] Leaderboard test passed:", res)
