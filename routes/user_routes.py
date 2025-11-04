from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.user_controller import (
    add_user, 
    update_profile, 
    delete_profile, 
    get_profile
)
from db import get_db

user_router = APIRouter()

@user_router.post('/add')
async def add_user_route(user_data: dict, db: Session = Depends(get_db)):
    return await add_user(user_data, db)

@user_router.put('/update')
async def update_profile_route(user_data: dict, db: Session = Depends(get_db)):
    return await update_profile(user_data, db)

@user_router.delete('/delete')
async def delete_profile_route(user_data: dict, db: Session = Depends(get_db)):
    return await delete_profile(user_data, db)

@user_router.get('/profile/{unique_id}')
async def get_profile_route(unique_id: str, db: Session = Depends(get_db)):
    return await get_profile(unique_id, db)