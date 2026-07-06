"""Add per-branch commission rates."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_branch_commission_rates"
down_revision: Union[str, None] = "005_system_enhancement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    branch_columns = {column["name"] for column in inspector.get_columns("branches")}
    if "commission_per_photo" not in branch_columns:
        op.add_column(
            "branches",
            sa.Column("commission_per_photo", sa.Float(), nullable=False, server_default="6"),
        )
        op.alter_column("branches", "commission_per_photo", server_default=None)
    if "commission_after_target_per_photo" not in branch_columns:
        op.add_column(
            "branches",
            sa.Column("commission_after_target_per_photo", sa.Float(), nullable=False, server_default="12"),
        )
        op.alter_column("branches", "commission_after_target_per_photo", server_default=None)


def downgrade() -> None:
    op.drop_column("branches", "commission_after_target_per_photo")
    op.drop_column("branches", "commission_per_photo")
