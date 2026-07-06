"""User model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    managed_employees = relationship(
        "ManagerEmployee",
        foreign_keys="ManagerEmployee.manager_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )
    manager_assignments = relationship(
        "ManagerEmployee",
        foreign_keys="ManagerEmployee.employee_id",
        back_populates="employee",
    )
    created_customers = relationship("Customer", back_populates="created_by")
    uploaded_photos = relationship("Photo", back_populates="uploaded_by")
    sales = relationship("Sale", back_populates="employee")
    audit_logs = relationship("AuditLog", back_populates="user")
