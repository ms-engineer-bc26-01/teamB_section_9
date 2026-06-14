"""make clothes image_url nullable

Revision ID: b7d3a1c9e2f4
Revises: da09de1d5720
Create Date: 2026-06-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d3a1c9e2f4"
down_revision: Union[str, Sequence[str], None] = "da09de1d5720"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "clothes",
        "image_url",
        existing_type=sa.String(length=512),
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "clothes",
        "image_url",
        existing_type=sa.String(length=512),
        nullable=False,
        existing_nullable=True,
    )
