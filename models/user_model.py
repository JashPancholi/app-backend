from models.role_model import Role
from models.database import UserDB
from sqlalchemy.orm import Session
import datetime
import random
import string
import uuid

class User:
    def __init__(self, first_name: str, last_name: str, unique_id: str = None, email: str = "", phone_number: str = "", is_user: bool = False, is_admin: bool = False, is_sales: bool = False, credits: int = 0, transaction_history: list = None, balance=0, referral_code:str=None, referred_by:list[str]=None):
        self.unique_id = unique_id or str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone_number = phone_number
        self.role = Role.USER if is_user else (Role.ADMIN if is_admin else (Role.SALES if is_sales else Role.USER))
        self.credits = credits
        self.transaction_history = transaction_history if transaction_history is not None else []
        self.balance = balance
        self.referral_code = referral_code or generate_referral_code()
        self.referred_by = referred_by if referred_by is not None else []
        self.referrals = []

    def to_dict(self):
        return {
            'unique_id': self.unique_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'role': self.role.value,
            'credits': self.credits,
            'transaction_history': self.transaction_history,
            'balance': self.balance,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by
        }

    def save(self, db: Session):
        # Check if user exists
        db_user = db.query(UserDB).filter(UserDB.unique_id == self.unique_id).first()
        
        if db_user:
            # Update existing user
            db_user.first_name = self.first_name
            db_user.last_name = self.last_name
            db_user.email = self.email
            db_user.phone_number = self.phone_number
            db_user.role = self.role.value
            db_user.credits = self.credits
            db_user.transaction_history = self.transaction_history
            db_user.balance = self.balance
            db_user.referral_code = self.referral_code
            db_user.referred_by = self.referred_by
            db_user.referrals = self.referrals
            print(f"User {self.unique_id} updated.")
        else:
            # Create new user
            db_user = UserDB(
                unique_id=self.unique_id,
                first_name=self.first_name,
                last_name=self.last_name,
                email=self.email,
                phone_number=self.phone_number,
                role=self.role.value,
                credits=self.credits,
                transaction_history=self.transaction_history,
                balance=self.balance,
                referral_code=self.referral_code,
                referred_by=self.referred_by,
                referrals=self.referrals
            )
            db.add(db_user)
            print(f"User {self.unique_id} created.")
        
        db.commit()
        db.refresh(db_user)

    def update_credits(self, amount: int, transaction_type: str, action_user: str, db: Session):
        # Ensure that credits don't go below 0 for redemption
        if self.credits + amount < 0:
            raise ValueError("Insufficient credits to redeem")
        
        # Add or subtract the credits
        self.credits += amount

        # Add the transaction entry for the action (either allocated or redeemed)
        transaction_entry = {
            "type": transaction_type,
            "points": amount,
            "timestamp": datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            "balance": self.credits,
            "action_user": action_user
        }
        self.transaction_history.append(transaction_entry)

        # Save the updated user data
        self.save(db)

    def get_current_credits(self):
        return self.credits

    @classmethod
    def get_by_id(cls, unique_id: str, db: Session):
        db_user = db.query(UserDB).filter(UserDB.unique_id == unique_id).first()
        if db_user:
            user = cls(
                unique_id=db_user.unique_id,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                email=db_user.email,
                phone_number=db_user.phone_number,
                is_user=db_user.role == Role.USER.value,
                is_admin=db_user.role == Role.ADMIN.value,
                is_sales=db_user.role == Role.SALES.value,
                credits=db_user.credits,
                transaction_history=db_user.transaction_history or [],
                balance=db_user.balance or 0,
                referral_code=db_user.referral_code,
                referred_by=db_user.referred_by or []
            )
            user.referrals = db_user.referrals or []
            return user
        return None

    @classmethod
    def get_all(cls, db: Session):
        db_users = db.query(UserDB).all()
        users = []
        for db_user in db_users:
            user = cls(
                unique_id=db_user.unique_id,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                email=db_user.email,
                phone_number=db_user.phone_number,
                is_user=db_user.role == Role.USER.value,
                is_admin=db_user.role == Role.ADMIN.value,
                is_sales=db_user.role == Role.SALES.value,
                credits=db_user.credits,
                transaction_history=db_user.transaction_history or [],
                balance=db_user.balance or 0,
                referral_code=db_user.referral_code,
                referred_by=db_user.referred_by or []
            )
            user.referrals = db_user.referrals or []
            users.append(user)
        return users

def generate_referral_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # Note: This should be checked against the database in actual usage
    return code