from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    small_photo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    large_photo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price_per_photo: Mapped[float] = mapped_column(Float, nullable=False, default=120.0)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    invoice_token: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    customer = relationship("Customer", back_populates="sales")
    employee = relationship("User", back_populates="sales")
    branch = relationship("Branch", back_populates="sales")
