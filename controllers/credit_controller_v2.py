from fastapi import HTTPException
from sqlalchemy.orm import Session
from services.credit_service import CreditService, InsufficientBalanceError, ConcurrentModificationError
from services.leaderboard_service import LeaderboardService
from models.credit_models import TransactionType
from datetime import datetime
import csv
import io
from typing import Optional

async def allocate_credits_v2(data: dict, db: Session):
    """
    Allocate credits with atomic transaction
    
    Request body:
    {
        "user_id": "target_user_id",
        "amount": 100,
        "initiated_by": "admin_or_sales_id",
        "reference_id": "optional_reference",
        "description": "optional_description",
        "metadata": {"key": "value"}
    }
    """
    try:
        user_id = data.get('user_id')
        amount = data.get('amount')
        initiated_by = data.get('initiated_by')
        reference_id = data.get('reference_id')
        description = data.get('description')
        metadata = data.get('metadata')
        
        if not all([user_id, amount, initiated_by]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: user_id, amount, initiated_by"
            )
        
        transaction = CreditService.allocate_credits(
            user_id=user_id,
            amount=int(amount),
            initiated_by=initiated_by,
            db=db,
            reference_id=reference_id,
            description=description,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": f"Successfully allocated {amount} credits",
            "transaction": {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "balance_after": transaction.balance_after,
                "timestamp": transaction.created_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except ConcurrentModificationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Allocation failed: {str(e)}")

async def redeem_credits_v2(data: dict, db: Session):
    """
    Redeem credits with atomic transaction
    
    Request body:
    {
        "user_id": "user_id",
        "amount": 50,
        "initiated_by": "user_id_or_admin",
        "reference_id": "optional_reference",
        "description": "optional_description",
        "metadata": {"key": "value"}
    }
    """
    try:
        user_id = data.get('user_id')
        amount = data.get('amount')
        initiated_by = data.get('initiated_by')
        reference_id = data.get('reference_id')
        description = data.get('description')
        metadata = data.get('metadata')
        
        if not all([user_id, amount, initiated_by]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: user_id, amount, initiated_by"
            )
        
        transaction = CreditService.redeem_credits(
            user_id=user_id,
            amount=int(amount),
            initiated_by=initiated_by,
            db=db,
            reference_id=reference_id,
            description=description,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": f"Successfully redeemed {amount} credits",
            "transaction": {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "balance_after": transaction.balance_after,
                "timestamp": transaction.created_at.isoformat()
            }
        }
    
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except ConcurrentModificationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redemption failed: {str(e)}")

async def get_transaction_history_v2(
    user_id: str,
    db: Session,
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None
):
    """
    Get transaction history with pagination
    
    Query params:
    - limit: Number of records per page (default: 50)
    - offset: Pagination offset (default: 0)
    - transaction_type: Filter by type (ALLOCATE, REDEEM, etc.)
    """
    try:
        # Convert transaction_type string to enum if provided
        type_filter = None
        if transaction_type:
            try:
                type_filter = TransactionType[transaction_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transaction type: {transaction_type}"
                )
        
        transactions, total = CreditService.get_transaction_history(
            user_id=user_id,
            db=db,
            limit=limit,
            offset=offset,
            transaction_type=type_filter
        )
        
        # Get current balance
        current_balance = CreditService.get_balance(user_id, db)
        
        # Format transactions
        formatted_transactions = []
        for t in transactions:
            formatted_transactions.append({
                "id": t.id,
                "type": t.transaction_type.value,
                "amount": t.amount,
                "balance_before": t.balance_before,
                "balance_after": t.balance_after,
                "status": t.status.value,
                "initiated_by": t.initiated_by,
                "reference_id": t.reference_id,
                "description": t.description,
                "metadata": t.metadata,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            })
        
        return {
            "user_id": user_id,
            "current_balance": current_balance,
            "transactions": formatted_transactions,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

async def export_transaction_history_csv(user_id: str, db: Session):
    """
    Export transaction history as CSV
    
    Returns CSV content as string
    """
    try:
        transactions, total = CreditService.get_transaction_history(
            user_id=user_id,
            db=db,
            limit=10000  # Export all
        )
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Transaction ID',
            'Type',
            'Amount',
            'Balance Before',
            'Balance After',
            'Status',
            'Initiated By',
            'Reference ID',
            'Description',
            'Created At',
            'Completed At'
        ])
        
        # Write data
        for t in transactions:
            writer.writerow([
                t.id,
                t.transaction_type.value,
                t.amount,
                t.balance_before,
                t.balance_after,
                t.status.value,
                t.initiated_by,
                t.reference_id or '',
                t.description or '',
                t.created_at.isoformat(),
                t.completed_at.isoformat() if t.completed_at else ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

async def get_leaderboard_v2(
    db: Session,
    limit: int = 10,
    force_refresh: bool = False
):
    """
    Get leaderboard with TTL cache
    
    Query params:
    - limit: Number of top users (default: 10, max: 100)
    - force_refresh: Skip cache and force refresh (default: false)
    """
    try:
        if limit > 100:
            limit = 100
        
        result = LeaderboardService.get_leaderboard(
            db=db,
            limit=limit,
            force_refresh=force_refresh
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard error: {str(e)}")

async def get_user_rank(user_id: str, db: Session):
    """Get specific user's rank in leaderboard"""
    try:
        rank_data = LeaderboardService.get_user_rank(user_id, db)
        
        if not rank_data:
            return {
                "user_id": user_id,
                "ranked": False,
                "message": "User not in leaderboard (no credits)"
            }
        
        return {
            "user_id": user_id,
            "ranked": True,
            **rank_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rank lookup failed: {str(e)}")

async def get_cache_stats(db: Session):
    """Get leaderboard cache statistics"""
    try:
        stats = LeaderboardService.get_cache_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

async def invalidate_leaderboard_cache(db: Session):
    """Invalidate all leaderboard cache entries"""
    try:
        LeaderboardService.invalidate_cache(db)
        return {"message": "Cache invalidated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalidation failed: {str(e)}")