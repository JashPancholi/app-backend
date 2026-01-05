from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    
    unique_id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    role = Column(String, default="USER")
    credits = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    referral_code = Column(String, unique=True, index=True)
    referred_by = Column(ARRAY(String), default=[])
    referrals = Column(ARRAY(String), default=[])
    transaction_history = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

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
