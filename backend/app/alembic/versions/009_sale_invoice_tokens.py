"""Add invoice tokens to sales."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_sale_invoice_tokens"
down_revision: Union[str, None] = "008_attendance_shift_partner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("sales")}
    indexes = {index["name"] for index in inspector.get_indexes("sales")}
    if "invoice_token" not in columns:
        op.add_column("sales", sa.Column("invoice_token", sa.String(length=128), nullable=True))
    if "ix_sales_invoice_token" not in indexes:
        op.create_index("ix_sales_invoice_token", "sales", ["invoice_token"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("sales")}
    if "ix_sales_invoice_token" in indexes:
        op.drop_index("ix_sales_invoice_token", table_name="sales")
    columns = {column["name"] for column in inspector.get_columns("sales")}
    if "invoice_token" in columns:
        op.drop_column("sales", "invoice_token")
