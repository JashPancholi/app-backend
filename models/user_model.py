from __future__ import annotations
from typing import List, Optional, Any, Dict
from models.role_model import Role
from models.database import UserDB
from sqlalchemy.orm import Session
import datetime
import random
import string
import uuid


def generate_referral_code() -> str:
    """Generate a random 4-character referral code (alphanumeric)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


class User:
    def __init__(
        self,
        first_name: str,
        last_name: str,
        unique_id: Optional[str] = None,
        email: str = "",
        phone_number: str = "",
        is_user: bool = False,
        is_admin: bool = False,
        is_sales: bool = False,
        credits: float = 0,
        transaction_history: Optional[List[Dict[str, Any]]] = None,
        balance: float = 0,
        referral_code: Optional[str] = None,
        referred_by: Optional[List[str]] = None,
        referrals: Optional[List[str]] = None,
    ):
        self.unique_id = unique_id or str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone_number = phone_number
        self.role = (
            Role.USER
            if is_user
            else (Role.ADMIN if is_admin else (Role.SALES if is_sales else Role.USER))
        )
        self.credits = credits or 0
        self.transaction_history = transaction_history or []
        self.balance = balance or 0
        self.referral_code = referral_code or generate_referral_code()
        self.referred_by = referred_by or []
        self.referrals = referrals or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unique_id": self.unique_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "role": self.role.value,
            "credits": self.credits,
            "transaction_history": self.transaction_history,
            "balance": self.balance,
            "referral_code": self.referral_code,
            "referred_by": self.referred_by,
            "referrals": self.referrals,
        }

    def save(self, db: Session) -> None:
        """Create or update user in DB."""
        db_user: Optional[UserDB] = db.query(UserDB).filter(
            UserDB.unique_id == self.unique_id
        ).first()

        if db_user:
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
            print(f"[INFO] User {self.unique_id} updated.")
        else:
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
                referrals=self.referrals,
            )
            db.add(db_user)
            print(f"[INFO] User {self.unique_id} created.")

        db.commit()
        db.refresh(db_user)

    def update_credits(
        self, amount: float, transaction_type: str, action_user: str, db: Session
    ) -> None:
        """Add/redeem credits and append to transaction history."""
        if self.credits + amount < 0:
            raise ValueError("Insufficient credits to redeem")

        self.credits += amount

        transaction_entry = {
            "type": transaction_type,
            "points": amount,
            "timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "balance": self.credits,
            "action_user": action_user,
        }

        self.transaction_history.append(transaction_entry)
        self.save(db)

    def get_current_credits(self) -> float:
        """Return user’s current credits."""
        return self.credits or 0

    @classmethod
    def get_by_id(cls, unique_id: str, db: Session) -> Optional[User]:
        """Fetch a single user by unique_id."""
        db_user: Optional[UserDB] = db.query(UserDB).filter(
            UserDB.unique_id == unique_id
        ).first()

        if not db_user:
            return None

        return cls.from_db(db_user)

    @classmethod
    def get_all(cls, db: Session) -> List[User]:
        """Fetch all users."""
        db_users: List[UserDB] = db.query(UserDB).all()
        return [cls.from_db(u) for u in db_users]

    @classmethod
    def from_db(cls, db_user: UserDB) -> User:
        """Convert ORM UserDB object into User instance."""
        return cls(
            unique_id=db_user.unique_id,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            email=db_user.email,
            phone_number=db_user.phone_number,
            is_user=db_user.role == Role.USER.value,
            is_admin=db_user.role == Role.ADMIN.value,
            is_sales=db_user.role == Role.SALES.value,
            credits=db_user.credits or 0,
            transaction_history=list(db_user.transaction_history or []),
            balance=db_user.balance or 0,
            referral_code=db_user.referral_code,
            referred_by=list(db_user.referred_by or []),
            referrals=list(db_user.referrals or []),
        )
