"""Add employee attendance records."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_attendance_records"
down_revision: Union[str, None] = "005_branch_commission_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "attendance_records" in inspector.get_table_names():
        return

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_day"),
    )
    op.create_index("ix_attendance_records_employee_id", "attendance_records", ["employee_id"])
    op.create_index("ix_attendance_records_branch_id", "attendance_records", ["branch_id"])
    op.create_index("ix_attendance_records_work_date", "attendance_records", ["work_date"])


def downgrade() -> None:
    op.drop_index("ix_attendance_records_work_date", table_name="attendance_records")
    op.drop_index("ix_attendance_records_branch_id", table_name="attendance_records")
    op.drop_index("ix_attendance_records_employee_id", table_name="attendance_records")
    op.drop_table("attendance_records")
