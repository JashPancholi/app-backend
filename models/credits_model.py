from __future__ import annotations
import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from models.database import Base


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_unique_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.unique_id"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "ALLOCATE" or "REDEEM"
    performed_by_unique_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.unique_id"), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relationships: use string names to avoid circular import issues
    user = relationship(
        "UserDB",
        foreign_keys=[user_unique_id],
        back_populates="transactions",
    )
    performed_by_user = relationship(
        "UserDB",
        foreign_keys=[performed_by_unique_id],
    )

    def __repr__(self) -> str:
        return (
            f"<CreditTransaction user={self.user_unique_id} "
            f"type={self.type} amount={self.amount}>"
        )
