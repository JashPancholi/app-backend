from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.auth_controller import (
    send_verification_code, 
    verify_code, 
    create_user_by_token, 
    search_user_by_email, 
    search_user_by_phone
)
from db import get_db

auth_router = APIRouter()

@auth_router.post('/phone/auth')
async def send_verification_code_route(phone_data: dict, db: Session = Depends(get_db)):
    return await send_verification_code(phone_data, db)

@auth_router.post('/phone/verify_code')
async def verify_code_route(verify_data: dict, db: Session = Depends(get_db)):
    return await verify_code(verify_data, db)

@auth_router.post('/phone/add_user')
async def add_user_route(user_data: dict, db: Session = Depends(get_db)):
    return await create_user_by_token(user_data, db)

@auth_router.post('/user/by_email')
async def search_user_by_email_route(email_data: dict, db: Session = Depends(get_db)):
    return await search_user_by_email(email_data, db)

@auth_router.post('/user/by_phone')
async def search_user_by_phone_route(phone_data: dict, db: Session = Depends(get_db)):
    return await search_user_by_phone(phone_data, db)