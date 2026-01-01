from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(enum.Enum):
    ALLOCATE = "ALLOCATE"
    REDEEM = "REDEEM"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class CreditBalance(Base):
    """Separate table for credit balances to enable optimistic locking"""
    __tablename__ = "credit_balances"
    
    user_id = Column(String, primary_key=True, index=True)
    balance = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=0, nullable=False)  # For optimistic locking
    last_transaction_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint('balance >= 0', name='balance_non_negative'),
        Index('idx_balance_updated', 'updated_at'),
    )

class CreditTransaction(Base):
    """Immutable transaction log for audit trail"""
    __tablename__ = "credit_transactions"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(String, nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.COMPLETED, nullable=False)
    
    # extre_data
    initiated_by = Column(String, nullable=False)  # User ID who initiated
    reference_id = Column(String)  # External reference (order ID, event ID, etc.)
    description = Column(String)
    extre_data = Column(JSON)  # Additional flexible data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_type_created', 'transaction_type', 'created_at'),
        Index('idx_reference', 'reference_id'),
        Index('idx_status', 'status'),
    )

class LeaderboardCache(Base):
    """Specialized cache table for leaderboard with TTL"""
    __tablename__ = "leaderboard_cache"
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String, unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    ttl_seconds = Column(Integer, default=45, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_cache_expiry', 'cache_key', 'expires_at'),
    )