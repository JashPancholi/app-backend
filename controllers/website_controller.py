from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models.database import UserDB
from controllers.admin_controller import add_user
from models.user_model import User
from dotenv import load_dotenv
import os

load_dotenv()

templates = Jinja2Templates(directory="templates")

async def home(request: Request, db: Session):
    sort_by = "default"
    
    users = db.query(UserDB).all()
    user_list = []
    for user in users:
        user_data = {
            'id': user.unique_id,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'credits': user.credits or 0,
            'role': user.role or 'User'
        }
        user_list.append(user_data)

    if sort_by != "default":
        user_list = [user for user in user_list if user["role"] == sort_by]
    
    return templates.TemplateResponse("HomePage.html", {"request": request, "users": user_list})

async def add_user_logic(user_data: dict, db: Session):
    try:
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        email = user_data.get('email')
        phone_number = user_data.get('phone_number')
        user_points = int(user_data.get('user_points', 0))
        
        if not email and not phone_number:
            raise HTTPException(status_code=400, detail="At least one of email or phone_number is required")
        
        user = User(
            unique_id=None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            credits=user_points
        )

        user.save(db)
        return {"message": "User added successfully", "user": user.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def user_details(request: Request, user_id: str, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        
        if user:
            user_data = {
                'unique_id': user.unique_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'role': user.role,
                'credits': user.credits,
                'balance': user.balance,
                'referral_code': user.referral_code
            }
            return templates.TemplateResponse("UserDetails.html", {"request": request, "user": user_data})
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_user_points_logic(user_id: str, points: int, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.credits = points
        db.commit()
        return RedirectResponse(url=f"{os.getenv('ADMIN_PORTAL')}/user/{user_id}", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_user_role_logic(user_id: str, new_role: str, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.role = new_role
        db.commit()
        return RedirectResponse(url=f"{os.getenv('ADMIN_PORTAL')}/user/{user_id}", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_user_logic(user_id: str, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_transactions_logic(user_id: str, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        
        if not user:
            return {'transactions': []}
            
        transactions = user.transaction_history or []
        
        # Sort transactions by timestamp in descending order
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"Found {len(transactions)} transactions for user {user_id}")
        return {'transactions': transactions}
        
    except Exception as e:
        print(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_user_balance_logic(user_id: str, balance: int, db: Session):
    try:
        user = db.query(UserDB).filter(UserDB.unique_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.balance = balance
        db.commit()
        return RedirectResponse(url=f"{os.getenv('ADMIN_PORTAL')}/user/{user_id}", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def search_users(request: Request, query: str, db: Session):
    print(f"Search query received: '{query}'")

    if not query or query.strip() == '':
        print("Empty query, returning all users")
        return await home(request, db)

    query = query.lower().strip()
    user_list = []

    try:
        print(f"Processing search for: '{query}'")
        all_users = db.query(UserDB).all()
        print(f"Total users in database: {len(all_users)}")

        for user in all_users:
            # Get the searchable fields
            first_name = (user.first_name or '').lower()
            last_name = (user.last_name or '').lower()
            full_name = f"{first_name} {last_name}".strip()
            email = (user.email or '').lower()
            phone = (user.phone_number or '').lower()
            user_id = user.unique_id.lower()

            print(f"Checking user - ID: {user_id}, Name: '{full_name}', Email: '{email}', Phone: '{phone}'")

            # Use exact substring matching
            found_match = False
            if query in full_name:
                print(f"Match found in name: '{full_name}'")
                found_match = True
            elif query in email:
                print(f"Match found in email: '{email}'")
                found_match = True  
            elif query in phone:
                print(f"Match found in phone: '{phone}'")
                found_match = True
            elif query in user_id:
                print(f"Match found in ID: '{user_id}'")
                found_match = True

            if found_match:
                user_data = {
                    'id': user.unique_id,
                    'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    'credits': user.credits or 0,
                    'role': user.role or 'User'
                }
                user_list.append(user_data)

        print(f"Search results: {len(user_list)} users found")
        return templates.TemplateResponse("HomePage.html", {"request": request, "users": user_list, "query": query})
    except Exception as e:
        print(f"Search error: {str(e)}")
        return templates.TemplateResponse("HomePage.html", {"request": request, "users": [], "query": query, "error": str(e)})