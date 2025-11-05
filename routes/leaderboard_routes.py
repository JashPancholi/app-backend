# routes/leaderboard_route.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models.database import get_db
from controllers.leaderboard_controller import fetch_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/")
def get_leaderboard(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """
    Returns the top users based on credits (cached for 45 seconds).
    """
    return fetch_leaderboard(limit, db)
