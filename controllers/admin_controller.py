from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.role_model import Role
from models.user_model import User
from models.database import UserDB
import base64
import os

def auth_middleware(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: Token key not provided")

    token = base64.b64decode(token).decode('utf-8')
    
    if token != os.getenv('ADMIN_PASSWORD'):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Credentials")

async def get_all_users(db: Session):
    try:
        users = db.query(UserDB).all()
        user_list = []
        for user in users:
            user_list.append({
                "unique_id": user.unique_id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "credits": user.credits or 0,
            })
        return user_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def update_user_points(user_id: str, points: int, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.credits += points
        db.commit()
        return {"message": "User points updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def add_user(user_data: dict, db: Session):
    try:
        user_id = user_data.get('user_id')
        user_name = user_data.get('user_name')
        user_points = user_data.get('user_points', 0)
        
        # Parse name into first and last
        name_parts = user_name.split(' ', 1) if user_name else ['', '']
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        new_user = User(
            unique_id=user_id,
            first_name=first_name,
            last_name=last_name,
            credits=user_points
        )
        new_user.save(db)
        return {"message": "User added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def remove_user(user_id: str, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        return {"message": "User removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def change_user_role(admin_id: str, target_user_id: str, new_role: str, db: Session):
    try:
        admin_user = User.get_by_id(admin_id, db)
        if not admin_user or admin_user.role != Role.ADMIN:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        target_user = User.get_by_id(target_user_id, db)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            new_role_enum = Role(new_role.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        db_user = db.query(UserDB).filter(UserDB.unique_id == target_user_id).first()
        db_user.role = new_role_enum.value
        db.commit()
        
        return {
            "message": f"User role updated to {new_role} successfully",
            "user": {
                "id": target_user_id,
                "role": new_role_enum.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
