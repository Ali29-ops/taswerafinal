"""Compatibility placeholder for existing system enhancement databases."""

from typing import Sequence, Union

revision: str = "005_system_enhancement"
down_revision: Union[str, None] = "004_branches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
