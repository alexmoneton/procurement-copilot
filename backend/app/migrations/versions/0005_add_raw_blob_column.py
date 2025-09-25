"""Add raw_blob column to tenders table

Revision ID: 0005
Revises: 0004
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add raw_blob column to tenders table."""
    op.add_column("tenders", sa.Column("raw_blob", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove raw_blob column from tenders table."""
    op.drop_column("tenders", "raw_blob")
