"""Add shift partner to attendance records."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_attendance_shift_partner"
down_revision: Union[str, None] = "007_sale_photo_sizes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("attendance_records")}
    if "partner_employee_id" not in columns:
        op.add_column("attendance_records", sa.Column("partner_employee_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_attendance_partner_employee_id",
            "attendance_records",
            "users",
            ["partner_employee_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_attendance_records_partner_employee_id", "attendance_records", ["partner_employee_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("attendance_records")}
    if "ix_attendance_records_partner_employee_id" in indexes:
        op.drop_index("ix_attendance_records_partner_employee_id", table_name="attendance_records")
    columns = {column["name"] for column in inspector.get_columns("attendance_records")}
    if "partner_employee_id" in columns:
        op.drop_constraint("fk_attendance_partner_employee_id", "attendance_records", type_="foreignkey")
        op.drop_column("attendance_records", "partner_employee_id")
