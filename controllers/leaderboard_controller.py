# controllers/leaderboard_controller.py
import time
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from models.database import CacheDB

CACHE_KEY = "leaderboard"
CACHE_TTL = 45  # seconds

def fetch_leaderboard(limit: int, db: Session):
    try:
        current_time = int(time.time())

        # --- Check Cache ---
        cached_data = db.query(CacheDB).filter(CacheDB.key == CACHE_KEY).first()
        if cached_data:
            age = current_time - cached_data.last_updated
            if age < CACHE_TTL:
                return {
                    "data": cached_data.value.get("rankings", [])[:limit],
                    "count": len(cached_data.value.get("rankings", [])),
                    "cached": True,
                    "cache_age": age
                }

        # --- Fetch Fresh Data (no ORM) ---
        query = text("""
            SELECT unique_id AS id,
                   CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) AS name,
                   COALESCE(credits, 0) AS credits
            FROM users
            ORDER BY credits DESC, unique_id ASC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).fetchall()

        leaderboard_data = [
            {"id": row.id, "name": row.name.strip(), "credits": row.credits}
            for row in result
        ]

        # --- Update Cache ---
        if leaderboard_data:
            if cached_data:
                cached_data.value = {"rankings": leaderboard_data}
                cached_data.last_updated = current_time
            else:
                new_cache = CacheDB(
                    key=CACHE_KEY,
                    value={"rankings": leaderboard_data},
                    last_updated=current_time
                )
                db.add(new_cache)
            db.commit()

        return {
            "data": leaderboard_data,
            "count": len(leaderboard_data),
            "cached": False,
            "updated_at": current_time
        }

    except Exception as e:
        print(f"Leaderboard Error: {str(e)}")
        raise HTTPException(status_code=503, detail="Leaderboard temporarily unavailable")
