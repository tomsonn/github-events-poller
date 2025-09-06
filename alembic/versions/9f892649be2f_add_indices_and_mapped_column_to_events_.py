"""add indices and mapped_column to events table

Revision ID: 9f892649be2f
Revises: c65de9029e0c
Create Date: 2025-09-06 10:07:38.870133

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9f892649be2f"
down_revision: Union[str, Sequence[str], None] = "c65de9029e0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f("ix_events_action"), "events", ["action"], unique=False)
    op.create_index(
        op.f("ix_events_event_type"), "events", ["event_type"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index(op.f("ix_events_action"), table_name="events")
