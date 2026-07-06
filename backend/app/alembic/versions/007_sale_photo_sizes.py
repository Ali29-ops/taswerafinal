"""Add small and large photo counts to sales."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_sale_photo_sizes"
down_revision: Union[str, None] = "006_attendance_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    sale_columns = {column["name"] for column in inspector.get_columns("sales")}
    if "small_photo_count" not in sale_columns:
        op.add_column("sales", sa.Column("small_photo_count", sa.Integer(), nullable=False, server_default="0"))
    if "large_photo_count" not in sale_columns:
        op.add_column("sales", sa.Column("large_photo_count", sa.Integer(), nullable=False, server_default="0"))
    op.execute(
        "UPDATE sales SET small_photo_count = COALESCE(NULLIF(small_photo_count, 0), photo_count, 0) "
        "WHERE large_photo_count = 0"
    )
    op.alter_column("sales", "small_photo_count", server_default=None)
    op.alter_column("sales", "large_photo_count", server_default=None)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    sale_columns = {column["name"] for column in inspector.get_columns("sales")}
    if "large_photo_count" in sale_columns:
        op.drop_column("sales", "large_photo_count")
    if "small_photo_count" in sale_columns:
        op.drop_column("sales", "small_photo_count")
