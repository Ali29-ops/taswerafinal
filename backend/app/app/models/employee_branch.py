"""Which branches an employee is allowed to work at."""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmployeeBranch(Base):
    __tablename__ = "employee_branches"
    __table_args__ = (UniqueConstraint("employee_id", "branch_id", name="uq_employee_branch"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    employee = relationship("User", foreign_keys=[employee_id])
    branch = relationship("Branch", back_populates="employee_links")


class EmployeeBranchSession(Base):
    """Daily branch selection when employee signs in."""

    __tablename__ = "employee_branch_sessions"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_employee_branch_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    employee = relationship("User", foreign_keys=[employee_id])
    branch = relationship("Branch")
