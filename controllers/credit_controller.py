from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.role_model import Role
from models.user_model import User
from models.database import UserDB, CacheDB
import time
from sqlalchemy import Column, String, JSON, Integer
from models.database import Base

class CacheDB(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True)
    value = Column(JSON)
    last_updated = Column(Integer)

async def allocate_points(points_data: dict, db: Session):
    try:
        current_user_id = points_data.get('current_user_id')
        target_user_id = points_data.get('target_user_id')
        points = points_data.get('points')

        if points is None:
            raise HTTPException(status_code=400, detail="Points not provided")
        
        try:
            points = int(points)  
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid points value")

        current_user = User.get_by_id(current_user_id, db)

        if not current_user:
            raise HTTPException(status_code=404, detail="Current user not found")

        if current_user.role not in [Role.SALES, Role.ADMIN]:
            raise HTTPException(status_code=403, detail="Unauthorized: Only SALES or ADMIN can allocate points")

        if current_user_id == target_user_id:
            raise HTTPException(status_code=400, detail="You cannot allocate points to yourself")

        target_user = User.get_by_id(target_user_id, db)

        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        
        if current_user.role == Role.SALES:
            if current_user.balance < points:
                raise HTTPException(status_code=400, detail="Insufficient balance to allocate points")
            current_user.balance -= points
            current_user.save(db)

        target_user.update_credits(points, "ALLOCATE", current_user_id, db)

        return {"message": f"Points successfully allocated to user {target_user_id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def redeem_points(redeem_data: dict, db: Session):
    try:
        current_user_id = redeem_data.get('current_user_id')
        points = int(redeem_data.get('points'))

        current_user = User.get_by_id(current_user_id, db)

        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        current_credits = current_user.get_current_credits()
        if current_credits < points:
            raise HTTPException(status_code=400, detail="Insufficient credits to redeem")

        current_user.update_credits(-points, "REDEEM", current_user_id, db)

        return {"message": "Points redeemed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def transaction_history(history_data: dict, db: Session):
    try:
        user_id = history_data.get('user_id')

        user = User.get_by_id(user_id, db)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"transaction_history": user.transaction_history}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def leaderboard(limit: int, db: Session):
    try:
        current_time = int(time.time())
        
        cached_data = db.query(CacheDB).filter(CacheDB.key == 'leaderboard').first()
        
        if cached_data:
            last_updated = cached_data.last_updated
            cache_age = current_time - last_updated
            print(f"Cache age: {cache_age} seconds")
            
            if cache_age < 45:
                leaderboard_data = cached_data.value.get('rankings', [])[:limit]
                print(f"Using cached data from {last_updated}")
                return {
                    "data": leaderboard_data,
                    "count": len(leaderboard_data),
                    "cached": True,
                    "cache_age": cache_age
                }
        
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