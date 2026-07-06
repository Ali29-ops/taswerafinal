from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ManagerEmployee(Base):
    __tablename__ = "managers_employees"
    __table_args__ = (UniqueConstraint("manager_id", "employee_id", name="uq_manager_employee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_employees")
    employee = relationship("User", foreign_keys=[employee_id], back_populates="manager_assignments")
