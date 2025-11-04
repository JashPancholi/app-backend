from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user_model import User
from models.database import PhoneAuthDB, UserDB
from datetime import datetime, timedelta, timezone
from utils import send_otp
import base64
from dotenv import load_dotenv
import os

load_dotenv()

TEST_PHONE = os.getenv('TEST_PHONE_NUMBER') or '7777777777'
TEST_OTP = os.getenv('TEST_OTP') or '123456'

async def send_verification_code(phone_data: dict, db: Session):
    try:
        phone_number = phone_data.get('phone_number')
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")

        # TEST PHONE HANDLING START
        if phone_number == TEST_PHONE:
            verification_id = 'test_verification_id'
            test_otp = TEST_OTP
            
            # Delete existing verification if any
            db.query(PhoneAuthDB).filter(PhoneAuthDB.verification_id == verification_id).delete()
            
            phone_auth = PhoneAuthDB(
                phone_number=phone_number,
                verification_id=verification_id,
                otp=test_otp,
                verified=False,
                attempts=0,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            db.add(phone_auth)
            db.commit()
            
            return {
                "message": f"Test verification code sent to {phone_number}",
                "verification_id": verification_id
            }
        # TEST PHONE HANDLING END

        verification_id, otp = send_otp(phone_number)
        
        # Delete existing verification if any
        db.query(PhoneAuthDB).filter(PhoneAuthDB.verification_id == verification_id).delete()
        
        phone_auth = PhoneAuthDB(
            phone_number=phone_number,
            verification_id=verification_id,
            otp=str(otp),
            verified=False,
            attempts=0,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        db.add(phone_auth)
        db.commit()

        return {
            "message": f"Verification code sent to {phone_number}",
            "verification_id": verification_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def verify_code(verify_data: dict, db: Session):
    try:
        verification_id = verify_data.get('verification_id')
        verification_code = verify_data.get('verification_code')
        phone_number = verify_data.get('phone_number')

        # TEST VERIFICATION START
        if phone_number == TEST_PHONE:
            if verification_code == TEST_OTP:
                token = base64.b64encode(f"{phone_number}::test_verification_id".encode('utf-8')).decode('utf-8')
                return {
                    "message": "User not found",
                    "token": token
                }
        # TEST VERIFICATION END

        # Validate required fields
        if not all([verification_id, verification_code, phone_number]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: verification_id, verification_code, phone_number"
            )

        # Get verification attempt from database
        phone_auth = db.query(PhoneAuthDB).filter(
            PhoneAuthDB.verification_id == verification_id
        ).first()

        # Check if document exists
        if not phone_auth:
            raise HTTPException(status_code=404, detail="Invalid verification ID")

        # Check if already verified
        if phone_auth.verified:
            raise HTTPException(status_code=400, detail="Code already verified")

        # Check if the code has expired 
        if phone_auth.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Verification code has expired")
        
        # Verify phone number matches
        if phone_auth.phone_number != phone_number:
            raise HTTPException(status_code=400, detail="Phone number does not match verification record")

        # Verify code
        if phone_auth.otp != verification_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        token = base64.b64encode((phone_number+"::"+verification_id).encode('utf-8')).decode('utf-8')

        # Mark as verified
        phone_auth.verified = True
        phone_auth.verified_at = datetime.now(timezone.utc)
        phone_auth.token = token
        db.commit()

        # Check if user exists
        user = db.query(UserDB).filter(UserDB.phone_number == phone_number).first()

        if user:
            user_data = {
                "unique_id": user.unique_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "credits": user.credits,
                "balance": user.balance,
                "referral_code": user.referral_code
            }
            return {
                "message": "User found",
                "user": user_data
            }

        return {
            "message": "User not found",
            "token": token
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
async def create_user_by_token(user_data: dict, db: Session):
    try:
        token = user_data.get('token')
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        email = user_data.get('email') or None
        user_points = 0
        referral_code = user_data.get('referral_code', None)

        # TEST USER CREATION START
        if token and base64.b64decode(token).decode('utf-8').startswith(TEST_PHONE):
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=TEST_PHONE,
                credits=user_points
            )
            user.save(db)
            return {"message": "Test user added successfully", "user": user.to_dict()}
        # TEST USER CREATION END

        token_decoded = base64.b64decode(token).decode('utf-8')
        phone_number, verification_id = token_decoded.split("::")
        
        phone_auth = db.query(PhoneAuthDB).filter(
            PhoneAuthDB.verification_id == verification_id
        ).first()

        if not phone_auth:
            raise HTTPException(status_code=404, detail="Token invalid")

        if referral_code:
            # Get user by referral code
            referrer = db.query(UserDB).filter(UserDB.referral_code == referral_code).first()
            
            if not referrer:
                raise HTTPException(status_code=400, detail="Invalid referral code")
                
            # Check if referrer has reached the limit
            current_referrals = referrer.referrals or []
            if len(current_referrals) >= 5:
                raise HTTPException(status_code=400, detail="Referral limit reached for this code")
                
            user_points += 20
            
            # Create new user with referrer's ID
            newUser = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                credits=user_points,
                referred_by=[referrer.unique_id]
            )
            newUser.save(db)
            
            # Update referrer's credits and referrals
            referrer_user = User.get_by_id(referrer.unique_id, db)
            referrer_user.update_credits(20, "Referral bonus", first_name + " " + last_name, db)
            
            # Update referral count
            referrer.referrals = current_referrals + [newUser.unique_id]
            db.commit()
            
            return {"message": "User added successfully with referral", "user": newUser.to_dict()}
        
        else:
            newUser = User(
                first_name=first_name,
                last_name=last_name or None,
                email=email or None,
                phone_number=phone_number or None,
                credits=0
            )
            newUser.save(db)

            return {"message": "User added successfully without referral", "user": newUser.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def search_user_by_email(email_data: dict, db: Session):
    try:
        email = email_data.get('email')

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        user = db.query(UserDB).filter(UserDB.email == email).first()

        if user:
            user_data = {
                "unique_id": user.unique_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "credits": user.credits
            }
            return {
                "message": "Email already in use",
                "user_exists": True,
                "user": user_data
            }

        return {"message": "Email is available", "user_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching email: {str(e)}")

async def search_user_by_phone(phone_data: dict, db: Session):
    try:
        phone = phone_data.get('phone')

        if not phone:
            raise HTTPException(status_code=400, detail="Phone is required")

        user = db.query(UserDB).filter(UserDB.phone_number == phone).first()

        if user:
            user_data = {
                "unique_id": user.unique_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "credits": user.credits
            }
            return {
                "message": "Phone already in use",
                "user_exists": True,
                "user": user_data
            }

        return {"message": "Phone is available", "user_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching phone: {str(e)}")