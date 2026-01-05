from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.role_model import Role
from models.user_model import User
from models.database import UserDB, CacheDB
import time

async def allocate_points(points_data: dict, db: Session):
    """Allocate points with atomic transaction and row-level locking"""
    try:
            # extract the current user (who is allocating the points) and the target user
            current_user_id = points_data.get('current_user_id')
            target_user_id = points_data.get('target_user_id')
            points = int(points_data.get('points'))

            if points <= 0:
                raise HTTPException(status_code=400, detail="Points must be positive")

            # Fetch current user with row-level lock
            current_user_db = db.query(UserDB).with_for_update().filter(
                UserDB.unique_id == current_user_id
            ).first()

            if not current_user_db:
                raise HTTPException(status_code=404, detail="Current user not found")

            # Convert to User model
            current_user = User.get_by_id(current_user_id, db)
            if not current_user:
                raise HTTPException(status_code=404, detail="Current user not found")

            # check if the current user has the proper role (SALES or ADMIN)
            if current_user.role not in [Role.SALES, Role.ADMIN]:
                raise HTTPException(status_code=403, detail="Unauthorized: Only SALES or ADMIN can allocate points")

            # ensure the user is not allocating points to themselves
            if current_user_id == target_user_id:
                raise HTTPException(status_code=400, detail="You cannot allocate points to yourself")

            # Fetch target user with row-level lock
            target_user_db = db.query(UserDB).with_for_update().filter(
                UserDB.unique_id == target_user_id
            ).first()

            if not target_user_db:
                raise HTTPException(status_code=404, detail="Target user not found")
            
            # Convert to User model
            target_user = User.get_by_id(target_user_id, db)
            if not target_user:
                raise HTTPException(status_code=404, detail="Target user not found")
            
            # Handle SALES balance deduction atomically
            if current_user.role == Role.SALES:
                if current_user.balance < points:
                    raise HTTPException(status_code=400, detail="Insufficient balance to allocate points")
                current_user.balance -= points
                current_user.save(db)

            # allocate points to the target user
            target_user.update_credits(points, "ALLOCATE", current_user_id, db)

            # Commit transaction
            db.commit()
            
            return {"message": f"Points successfully allocated to user {target_user_id}"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

async def redeem_points(redeem_data: dict, db: Session):
    """Redeem points with atomic transaction and row-level locking"""
    try:
            # extract user ID and points to redeem
            current_user_id = redeem_data.get('current_user_id')
            points = int(redeem_data.get('points'))

            if points <= 0:
                raise HTTPException(status_code=400, detail="Points must be positive")

            # Fetch user with row-level lock to prevent race conditions
            user_db = db.query(UserDB).with_for_update().filter(
                UserDB.unique_id == current_user_id
            ).first()

            if not user_db:
                raise HTTPException(status_code=404, detail="User not found")

            # Convert to User model
            current_user = User.get_by_id(current_user_id, db)
            if not current_user:
                raise HTTPException(status_code=404, detail="User not found")

            # ensure the user has enough credits (check with locked row)
            current_credits = current_user.get_current_credits()
            if current_credits < points:
                raise HTTPException(status_code=400, detail="Insufficient credits to redeem")

            # redeem the points (deduct them from user's credits)
            current_user.update_credits(-points, "REDEEM", current_user_id, db)

            # Commit transaction
            db.commit()
            
            return {"message": "Points redeemed successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

async def transaction_history(user_id: str, db: Session, page: int = 1, limit: int = 20, 
                              transaction_type: str = None, start_date: str = None, 
                              end_date: str = None, format: str = "json"):
    """Get transaction history with pagination, filtering, and CSV export"""
    try:
        from datetime import datetime
        import csv
        from io import StringIO
        from fastapi.responses import Response
        
        # fetch user from the database
        user = User.get_by_id(user_id, db)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get transaction history
        transactions = user.transaction_history or []
        
        # Apply filters
        if transaction_type:
            transactions = [t for t in transactions if t.get("type") == transaction_type]
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                transactions = [t for t in transactions if datetime.fromisoformat(t.get("timestamp", "").replace('Z', '+00:00')) >= start_dt]
            except:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                transactions = [t for t in transactions if datetime.fromisoformat(t.get("timestamp", "").replace('Z', '+00:00')) <= end_dt]
            except:
                pass
        
        # Reverse to show newest first
        transactions.reverse()
        
        # Handle CSV export
        if format == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "transaction_id", "type", "points", "balance_before", 
                "balance_after", "timestamp", "action_user", "status"
            ])
            writer.writeheader()
            for t in transactions:
                writer.writerow({
                    "transaction_id": t.get("transaction_id", ""),
                    "type": t.get("type", ""),
                    "points": t.get("points", 0),
                    "balance_before": t.get("balance_before", 0),
                    "balance_after": t.get("balance_after", 0),
                    "timestamp": t.get("timestamp", ""),
                    "action_user": t.get("action_user", ""),
                    "status": t.get("status", "")
                })
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=transactions_{user_id}.csv"}
            )
        
        # Pagination for JSON response
        total = len(transactions)
        offset = (page - 1) * limit
        paginated_transactions = transactions[offset:offset + limit]
        has_more = offset + limit < total
        
        return {
            "transaction_history": paginated_transactions,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": has_more
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def leaderboard(limit: int, db: Session):
    try:
        current_time = int(time.time())
        
        # check cache
        cached_data = db.query(CacheDB).filter(CacheDB.key == 'leaderboard').first()
        
        if cached_data:
            last_updated = cached_data.last_updated
            cache_age = current_time - last_updated
            print(f"Cache age: {cache_age} seconds")
            
            # return cached data if less than 45 seconds old
            if cache_age < 45:
                leaderboard_data = cached_data.value.get('rankings', [])[:limit]
                print(f"Using cached data from {last_updated}")
                return {
                    "data": leaderboard_data,
                    "count": len(leaderboard_data),
                    "cached": True,
                    "cache_age": cache_age
                }
        
        # Cache expired or doesn't exist, fetch fresh data
        print("Fetching fresh leaderboard data")
        users = db.query(UserDB).order_by(
            UserDB.credits.desc(),
            UserDB.unique_id.asc()
        ).limit(limit).all()
        
        leaderboard_data = []
        for user in users:
            entry = {
                'id': user.unique_id,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                'credits': user.credits or 0
            }
            leaderboard_data.append(entry)
        
        # Update cache with new data
        if leaderboard_data:
            print(f"Updating cache at {current_time}")
            if cached_data:
                cached_data.value = {'rankings': leaderboard_data}
                cached_data.last_updated = current_time
            else:
                new_cache = CacheDB(
                    key='leaderboard',
                    value={'rankings': leaderboard_data},
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
        raise HTTPException(
            status_code=503,
            detail="Leaderboard temporarily unavailable"
        )