"""Initial migration

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    tendersource = postgresql.ENUM("TED", "BOAMP_FR", name="tendersource")
    tendersource.create(op.get_bind())

    notifyfrequency = postgresql.ENUM("daily", "weekly", name="notifyfrequency")
    notifyfrequency.create(op.get_bind())

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    # Create tenders table
    op.create_table(
        "tenders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tender_ref", sa.String(length=255), nullable=False),
        sa.Column("source", tendersource, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("cpv_codes", postgresql.ARRAY(sa.String(length=10)), nullable=False),
        sa.Column("buyer_name", sa.String(length=500), nullable=True),
        sa.Column("buyer_country", sa.String(length=2), nullable=False),
        sa.Column("value_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tender_ref"),
    )
    op.create_index(op.f("ix_tenders_id"), "tenders", ["id"], unique=False)
    op.create_index(
        op.f("ix_tenders_tender_ref"), "tenders", ["tender_ref"], unique=False
    )
    op.create_index(op.f("ix_tenders_source"), "tenders", ["source"], unique=False)
    op.create_index(
        op.f("ix_tenders_publication_date"),
        "tenders",
        ["publication_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tenders_deadline_date"), "tenders", ["deadline_date"], unique=False
    )
    op.create_index(
        op.f("ix_tenders_buyer_country"), "tenders", ["buyer_country"], unique=False
    )
    op.create_index(
        "ix_tenders_cpv_codes",
        "tenders",
        ["cpv_codes"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_tenders_publication_date_desc",
        "tenders",
        ["publication_date"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "ix_tenders_deadline_date_desc",
        "tenders",
        ["deadline_date"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "ix_tenders_buyer_country",
        "tenders",
        ["buyer_country"],
        unique=False,
        postgresql_using="btree",
    )

    # Create saved_filters table
    op.create_table(
        "saved_filters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String(length=100)), nullable=False),
        sa.Column("cpv_codes", postgresql.ARRAY(sa.String(length=10)), nullable=False),
        sa.Column("countries", postgresql.ARRAY(sa.String(length=2)), nullable=False),
        sa.Column("min_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("max_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("notify_frequency", notifyfrequency, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_filters_id"), "saved_filters", ["id"], unique=False)
    op.create_index(
        op.f("ix_saved_filters_user_id"), "saved_filters", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table("saved_filters")
    op.drop_table("tenders")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS notifyfrequency")
    op.execute("DROP TYPE IF EXISTS tendersource")
