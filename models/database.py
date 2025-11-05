from sqlalchemy import Column, Integer, String, Enum, JSON, Float, Boolean, DateTime 
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from datetime import datetime
from db import Base 
from models.role_model import Role
from sqlalchemy.orm import relationship


class UserDB(Base):
    __tablename__ = "users_sql"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    role = Column(Enum(Role), default=Role.USER) 
    credits = Column(Integer, default=0)
    transaction_history = Column(JSON, default=[])
    balance = Column(Float, default=0.0)
    referral_code = Column(String, unique=True)
    referred_by = Column(ARRAY(String)) 
    referrals = Column(ARRAY(String)) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transactions = relationship(
        "CreditTransaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
class PhoneAuthDB(Base):
    __tablename__ = "phone_auth"

    verification_id = Column(String, primary_key=True, index=True)
    phone_number = Column(String, nullable=False, index=True)
    otp = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    token = Column(String)

class CacheDB(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    last_updated = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())