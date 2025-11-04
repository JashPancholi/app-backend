from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from controllers.credit_controller import (
    allocate_points, 
    redeem_points, 
    transaction_history, 
    leaderboard
)
from db import get_db

credit_router = APIRouter()

# Route to allocate points to a user
@credit_router.post('/points/allocate')
async def allocate_points_route(points_data: dict, db: Session = Depends(get_db)):
    return await allocate_points(points_data, db)

# Route to redeem points from a user
@credit_router.post('/points/redeem')
async def redeem_points_route(redeem_data: dict, db: Session = Depends(get_db)):
    return await redeem_points(redeem_data, db)

# Route to get transaction history of a user
@credit_router.post('/transactions/history')
async def transaction_history_route(history_data: dict, db: Session = Depends(get_db)):
    return await transaction_history(history_data, db)

@credit_router.get('/leaderboard')
async def get_leaderboard(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    try:
        return await leaderboard(limit, db)
    except Exception as e:
        print(f"Route Error: {str(e)}")
        return {"error": "Server timeout"}