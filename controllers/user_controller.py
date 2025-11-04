from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user_model import User
from models.database import UserDB

def validate_contact_info(email, phone_number):
    if not email and not phone_number:
        return False, "At least one of email or phone_number is required."
    return True, ""

async def add_user(user_data: dict, db: Session):
    try:
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        email = user_data.get('email')
        phone_number = user_data.get('phone_number')
        user_points = 0
        referral_code = user_data.get('referral_code', None)

        # validate that at least one of email or phone_number is provided
        is_valid, error_message = validate_contact_info(email, phone_number)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)

        if referral_code:
            referrer = db.query(UserDB).filter(UserDB.referral_code == referral_code).first()
            if not referrer:
                raise HTTPException(status_code=400, detail="Referral code invalid")
            
            referrer_id = referrer.unique_id
            user_points += 20
            
            # create new user with referrer's ID
            newUser = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                credits=user_points,
                referred_by=[referrer_id]
            )
        else:
            newUser = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                credits=user_points,
                referred_by=[]
            )
        newUser.save(db)

        return {"message": "User added successfully", "user": newUser.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def update_profile(user_data: dict, db: Session):
    try:
        unique_id = user_data.get('unique_id')

        # retrieve user from database
        user = User.get_by_id(unique_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # validate that at least one of email or phone_number is provided
        email = user_data.get('email', user.email)
        phone_number = user_data.get('phone_number', user.phone_number)
        is_valid, error_message = validate_contact_info(email, phone_number)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)

        # update fields
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.email = email
        user.phone_number = phone_number

        # save updated user
        user.save(db)

        return {"message": "User profile updated successfully", "user": user.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def delete_profile(user_data: dict, db: Session):
    try:
        unique_id = user_data.get('unique_id')
        user = User.get_by_id(unique_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user from database
        db.query(UserDB).filter(UserDB.unique_id == unique_id).delete()
        db.commit()

        return {"message": "User profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def get_profile(unique_id: str, db: Session):
    try:
        user = User.get_by_id(unique_id, db)
        if user:
            return {"user": user.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))