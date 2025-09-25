"""Add alerts system

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add name column to saved_filters
    op.add_column(
        "saved_filters",
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            server_default="Unnamed Filter",
        ),
    )

    # Add last_notified_at column to saved_filters
    op.add_column(
        "saved_filters",
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create email_logs table
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_filter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body_preview", sa.String(length=500), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["saved_filter_id"], ["saved_filters.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for email_logs
    op.create_index(op.f("ix_email_logs_id"), "email_logs", ["id"], unique=False)
    op.create_index(
        op.f("ix_email_logs_user_id"), "email_logs", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_email_logs_saved_filter_id"),
        "email_logs",
        ["saved_filter_id"],
        unique=False,
    )

    # Remove the server default for name column after data migration
    op.alter_column("saved_filters", "name", server_default=None)


def downgrade() -> None:
    # Drop email_logs table
    op.drop_table("email_logs")

    # Remove columns from saved_filters
    op.drop_column("saved_filters", "last_notified_at")
    op.drop_column("saved_filters", "name")
