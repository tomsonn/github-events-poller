"""add action field to the events table

Revision ID: c65de9029e0c
Revises: 316ad78fe879
Create Date: 2025-09-06 09:34:05.490079

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c65de9029e0c"
down_revision: Union[str, Sequence[str], None] = "316ad78fe879"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("events", sa.Column("action", sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("events", "action")
