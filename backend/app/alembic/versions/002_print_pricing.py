"""Add print pricing and photo count on sales."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_print_pricing"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "print_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("price_per_photo", sa.Float(), nullable=False, server_default="120"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO print_settings (id, price_per_photo) VALUES (1, 120.0)")

    op.add_column("sales", sa.Column("photo_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("sales", sa.Column("price_per_photo", sa.Float(), nullable=False, server_default="120"))
    op.alter_column("sales", "photo_count", server_default=None)
    op.alter_column("sales", "price_per_photo", server_default=None)


def downgrade() -> None:
    op.drop_column("sales", "price_per_photo")
    op.drop_column("sales", "photo_count")
    op.drop_table("print_settings")
