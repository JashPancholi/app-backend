from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from controllers.admin_controller import (
    auth_middleware,
    get_all_users, 
    update_user_points, 
    add_user, 
    remove_user,
    change_user_role
)
from db import get_db

admin_router = APIRouter()

async def verify_admin_token(token: str = Header(None, alias="TOKEN")):
    return auth_middleware(token)

@admin_router.get('/users', dependencies=[Depends(verify_admin_token)])
async def get_all_users_route(sort: str = Query(default="ascending"), db: Session = Depends(get_db)):
    users = await get_all_users(db)
    if sort == "descending":
        users.sort(key=lambda x: x["credits"], reverse=True)
    else:
        users.sort(key=lambda x: x["credits"])
    return users

@admin_router.put('/points/update', dependencies=[Depends(verify_admin_token)])
async def update_user_points_route(points_data: dict, db: Session = Depends(get_db)):
    user_id = points_data.get('user_id')
    points = points_data.get('points')
    return await update_user_points(user_id, points, db)

@admin_router.post('/users/add', dependencies=[Depends(verify_admin_token)])
async def add_user_route(user_data: dict, db: Session = Depends(get_db)):
    return await add_user(user_data, db)

@admin_router.delete('/users/{user_id}', dependencies=[Depends(verify_admin_token)])
async def remove_user_route(user_id: str, db: Session = Depends(get_db)):
    return await remove_user(user_id, db)

@admin_router.put('/users/role', dependencies=[Depends(verify_admin_token)])
async def change_role_route(role_data: dict, db: Session = Depends(get_db)):
    admin_id = role_data.get('admin_id')
    target_user_id = role_data.get('user_id')
    new_role = role_data.get('role')
    return await change_user_role(admin_id, target_user_id, new_role, db)