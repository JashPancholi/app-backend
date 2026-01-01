from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from controllers.credit_controller_v2 import (
    allocate_credits_v2,
    redeem_credits_v2,
    get_transaction_history_v2,
    export_transaction_history_csv,
    get_leaderboard_v2,
    get_user_rank,
    get_cache_stats,
    invalidate_leaderboard_cache
)
from db import get_db
from datetime import datetime

credit_router_v2 = APIRouter(prefix="/credits/v2", tags=["credits-v2"])

@credit_router_v2.post('/allocate')
async def allocate_credits_route(data: dict, db: Session = Depends(get_db)):
    """
    Allocate credits to a user with atomic transaction
    
    **Request Body:**
    ```json
    {
        "user_id": "target_user_id",
        "amount": 100,
        "initiated_by": "admin_or_sales_id",
        "reference_id": "order_123",  // optional
        "description": "Purchase reward",  // optional
        "metadata": {"product": "item_1"}  // optional
    }
    ```
    
    **Features:**
    - Atomic database transaction
    - Optimistic locking to prevent race conditions
    - Automatic retry on conflicts
    - Vendor balance validation for SALES role
    - Complete audit trail
    """
    return await allocate_credits_v2(data, db)

@credit_router_v2.post('/redeem')
async def redeem_credits_route(data: dict, db: Session = Depends(get_db)):
    """
    Redeem credits from a user with atomic transaction
    
    **Request Body:**
    ```json
    {
        "user_id": "user_id",
        "amount": 50,
        "initiated_by": "user_id_or_admin",
        "reference_id": "redemption_456",  // optional
        "description": "Product purchase",  // optional
        "metadata": {"item": "coffee"}  // optional
    }
    ```
    
    **Features:**
    - Atomic database transaction
    - Insufficient balance protection
    - Optimistic locking to prevent double-spend
    - Complete audit trail
    """
    return await redeem_credits_v2(data, db)

@credit_router_v2.get('/history/{user_id}')
async def get_transaction_history_route(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Records per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    transaction_type: str = Query(default=None, description="Filter by type: ALLOCATE, REDEEM, etc."),
    db: Session = Depends(get_db)
):
    """
    Get transaction history with pagination
    
    **Query Parameters:**
    - `limit`: Number of records per page (1-500, default: 50)
    - `offset`: Pagination offset (default: 0)
    - `transaction_type`: Filter by type (ALLOCATE, REDEEM, REFUND, ADJUSTMENT)
    
    **Response includes:**
    - Current balance
    - Paginated transactions
    - Pagination metadata
    """
    return await get_transaction_history_v2(user_id, db, limit, offset, transaction_type)

@credit_router_v2.get('/history/{user_id}/export')
async def export_transaction_history_route(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Export complete transaction history as CSV
    
    **Returns:** CSV file with all transactions
    """
    csv_content = await export_transaction_history_csv(user_id, db)
    
    filename = f"transactions_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@credit_router_v2.get('/leaderboard')
async def get_leaderboard_route(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top users"),
    force_refresh: bool = Query(default=False, description="Skip cache and force refresh"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard with 45-second TTL cache
    
    **Query Parameters:**
    - `limit`: Number of top users to return (1-100, default: 10)
    - `force_refresh`: Skip cache and force fresh data (default: false)
    
    **Cache Behavior:**
    - Cache TTL: 45 seconds
    - Automatic expiration
    - Cache hit tracking
    - Background cleanup of expired entries
    
    **Response includes:**
    - Leaderboard data (rank, name, balance)
    - Cache metadata (age, TTL remaining, hit count)
    - Whether data was served from cache
    """
    return await get_leaderboard_v2(db, limit, force_refresh)

@credit_router_v2.get('/leaderboard/rank/{user_id}')
async def get_user_rank_route(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific user's rank in leaderboard
    
    **Returns:**
    - User's current rank
    - Balance
    - Percentile
    - Total users in leaderboard
    """
    return await get_user_rank(user_id, db)

@credit_router_v2.get('/leaderboard/cache/stats')
async def get_cache_stats_route(db: Session = Depends(get_db)):
    """
    Get leaderboard cache statistics
    
    **Returns:**
    - Total cache entries
    - Active entries
    - Expired entries
    - Total cache hits
    - Hit rate
    """
    return await get_cache_stats(db)

@credit_router_v2.post('/leaderboard/cache/invalidate')
async def invalidate_cache_route(db: Session = Depends(get_db)):
    """
    Invalidate all leaderboard cache entries
    
    **Use cases:**
    - Manual cache refresh
    - After bulk operations
    - Testing
    """
    return await invalidate_leaderboard_cache(db)