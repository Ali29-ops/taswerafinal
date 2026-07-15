"""add sale payments and print packages

Revision ID: 010_payment_packages
Revises: 009_sale_invoice_tokens
Create Date: 2026-07-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010_payment_packages"
down_revision: Union[str, None] = "009_sale_invoice_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _tables() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    tables = _tables()
    if "print_packages" not in tables:
        op.create_table(
            "print_packages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("photo_count", sa.Integer(), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_print_packages_is_active"), "print_packages", ["is_active"], unique=False)

    sale_columns = _columns("sales")
    if "package_id" not in sale_columns:
        op.add_column("sales", sa.Column("package_id", sa.Integer(), nullable=True))
        op.create_index(op.f("ix_sales_package_id"), "sales", ["package_id"], unique=False)
        op.create_foreign_key("fk_sales_package_id_print_packages", "sales", "print_packages", ["package_id"], ["id"], ondelete="SET NULL")
    if "payment_status" not in sale_columns:
        op.add_column("sales", sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="paid"))
    if "payment_method" not in sale_columns:
        op.add_column("sales", sa.Column("payment_method", sa.String(length=20), nullable=True))


def downgrade() -> None:
    sale_columns = _columns("sales")
    if "payment_method" in sale_columns:
        op.drop_column("sales", "payment_method")
    if "payment_status" in sale_columns:
        op.drop_column("sales", "payment_status")
    if "package_id" in sale_columns:
        op.drop_constraint("fk_sales_package_id_print_packages", "sales", type_="foreignkey")
        op.drop_index(op.f("ix_sales_package_id"), table_name="sales")
        op.drop_column("sales", "package_id")
    if "print_packages" in _tables():
        op.drop_index(op.f("ix_print_packages_is_active"), table_name="print_packages")
        op.drop_table("print_packages")
