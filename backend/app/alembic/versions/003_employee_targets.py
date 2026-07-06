"""Add employee monthly photo targets."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_employee_targets"
down_revision: Union[str, None] = "002_print_pricing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_monthly_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("target_photos", sa.Integer(), nullable=False),
        sa.Column("set_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["set_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "year", "month", name="uq_employee_month_target"),
    )
    op.create_index("ix_employee_monthly_targets_employee_id", "employee_monthly_targets", ["employee_id"])
    op.create_index("ix_employee_monthly_targets_year", "employee_monthly_targets", ["year"])
    op.create_index("ix_employee_monthly_targets_month", "employee_monthly_targets", ["month"])


def downgrade() -> None:
    op.drop_table("employee_monthly_targets")
