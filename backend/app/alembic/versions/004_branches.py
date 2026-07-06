"""Add branches, per-branch pricing, and employee branch selection."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_branches"
down_revision: Union[str, None] = "003_employee_targets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("price_per_photo", sa.Float(), nullable=False, server_default="120"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "employee_branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "branch_id", name="uq_employee_branch"),
    )
    op.create_index("ix_employee_branches_employee_id", "employee_branches", ["employee_id"])
    op.create_index("ix_employee_branches_branch_id", "employee_branches", ["branch_id"])

    op.create_table(
        "employee_branch_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_employee_branch_day"),
    )
    op.create_index("ix_employee_branch_sessions_employee_id", "employee_branch_sessions", ["employee_id"])
    op.create_index("ix_employee_branch_sessions_branch_id", "employee_branch_sessions", ["branch_id"])
    op.create_index("ix_employee_branch_sessions_work_date", "employee_branch_sessions", ["work_date"])

    op.add_column("sales", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_sales_branch_id", "sales", "branches", ["branch_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_sales_branch_id", "sales", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_branch_id", table_name="sales")
    op.drop_constraint("fk_sales_branch_id", "sales", type_="foreignkey")
    op.drop_column("sales", "branch_id")
    op.drop_table("employee_branch_sessions")
    op.drop_table("employee_branches")
    op.drop_table("branches")
