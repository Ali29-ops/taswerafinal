"""Branch locations with per-branch print pricing."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    price_per_photo: Mapped[float] = mapped_column(Float, nullable=False, default=120.0)
    commission_per_photo: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)
    commission_after_target_per_photo: Mapped[float] = mapped_column(Float, nullable=False, default=12.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    employee_links = relationship("EmployeeBranch", back_populates="branch", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="branch")
