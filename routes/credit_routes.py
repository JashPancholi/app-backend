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

# Route to get transaction history of a user (POST - backward compatibility)
@credit_router.post('/transactions/history')
async def transaction_history_route_post(history_data: dict, db: Session = Depends(get_db)):
    user_id = history_data.get('user_id')
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="user_id is required")
    return await transaction_history(user_id, db)

# Route to get transaction history of a user (GET - RESTful)
@credit_router.get('/history/{user_id}')
async def transaction_history_route_get(
    user_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    transaction_type: str = Query(default=None, description="Filter by type (ALLOCATE/REDEEM)"),
    start_date: str = Query(default=None, description="Start date (ISO format)"),
    end_date: str = Query(default=None, description="End date (ISO format)"),
    format: str = Query(default="json", description="Response format (json/csv)"),
    db: Session = Depends(get_db)
):
    return await transaction_history(user_id, db, page, limit, transaction_type, start_date, end_date, format)

@credit_router.get('/leaderboard')
async def get_leaderboard(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    try:
        return await leaderboard(limit, db)
    except Exception as e:
        print(f"Route Error: {str(e)}")
        return {"error": "Server timeout"}