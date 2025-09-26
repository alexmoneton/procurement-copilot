"""Add outbound pipeline models

Revision ID: 0006
Revises: 0005_add_raw_blob_column
Create Date: 2024-09-26 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005_add_raw_blob_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create prospects table
    op.create_table('prospects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.Text(), nullable=False),
        sa.Column('normalized_company', sa.Text(), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('cpv_family', sa.Text(), nullable=False),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('new', 'enriched', 'queued', 'sent', 'bounced', 'unsub', 'suppressed', 'invalid', name='prospectstatus'), nullable=False),
        sa.Column('last_award_ref', sa.Text(), nullable=True),
        sa.Column('score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prospects_status', 'prospects', ['status'], unique=False)
    op.create_index('idx_prospects_score', 'prospects', ['score'], unique=False)
    op.create_index('idx_prospects_created_at', 'prospects', ['created_at'], unique=False)
    op.create_index('idx_prospects_normalized_company', 'prospects', ['normalized_company'], unique=False)
    op.create_index('uq_prospects_company_country_cpv_award', 'prospects', ['normalized_company', 'country', 'cpv_family', 'last_award_ref'], unique=True)

    # Create contact_cache table
    op.create_table('contact_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('normalized_company', sa.Text(), nullable=False),
        sa.Column('domain', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('source', sa.Enum('hunter', 'guess', 'manual', name='contactsource'), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('discovered_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_contact_cache_normalized_company', 'contact_cache', ['normalized_company'], unique=False)
    op.create_index('idx_contact_cache_expires_at', 'contact_cache', ['expires_at'], unique=False)
    op.create_index('idx_contact_cache_confidence', 'contact_cache', ['confidence'], unique=False)

    # Create suppressions table
    op.create_table('suppressions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('suppressed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_suppressions_email', 'suppressions', ['email'], unique=False)
    op.create_index('idx_suppressions_suppressed_at', 'suppressions', ['suppressed_at'], unique=False)

    # Create outbound_logs table
    op.create_table('outbound_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prospect_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('campaign', sa.Text(), nullable=False),
        sa.Column('event', sa.Enum('queued', 'sent', 'open', 'click', 'reply', 'bounce', 'complaint', 'unsubscribe', 'error', name='outboundevent'), nullable=False),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prospect_id'], ['prospects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_outbound_logs_campaign', 'outbound_logs', ['campaign'], unique=False)
    op.create_index('idx_outbound_logs_event', 'outbound_logs', ['event'], unique=False)
    op.create_index('idx_outbound_logs_created_at', 'outbound_logs', ['created_at'], unique=False)
    op.create_index('idx_outbound_logs_prospect_id', 'outbound_logs', ['prospect_id'], unique=False)

    # Create outbound_metrics table
    op.create_table('outbound_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('prospects_discovered', sa.Integer(), nullable=False),
        sa.Column('contacts_enriched', sa.Integer(), nullable=False),
        sa.Column('emails_sent', sa.Integer(), nullable=False),
        sa.Column('emails_opened', sa.Integer(), nullable=False),
        sa.Column('emails_clicked', sa.Integer(), nullable=False),
        sa.Column('emails_replied', sa.Integer(), nullable=False),
        sa.Column('emails_bounced', sa.Integer(), nullable=False),
        sa.Column('emails_complained', sa.Integer(), nullable=False),
        sa.Column('emails_unsubscribed', sa.Integer(), nullable=False),
        sa.Column('hunter_api_calls', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index('idx_outbound_metrics_date', 'outbound_metrics', ['date'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_outbound_metrics_date', table_name='outbound_metrics')
    op.drop_table('outbound_metrics')
    
    op.drop_index('idx_outbound_logs_prospect_id', table_name='outbound_logs')
    op.drop_index('idx_outbound_logs_created_at', table_name='outbound_logs')
    op.drop_index('idx_outbound_logs_event', table_name='outbound_logs')
    op.drop_index('idx_outbound_logs_campaign', table_name='outbound_logs')
    op.drop_table('outbound_logs')
    
    op.drop_index('idx_suppressions_suppressed_at', table_name='suppressions')
    op.drop_index('idx_suppressions_email', table_name='suppressions')
    op.drop_table('suppressions')
    
    op.drop_index('idx_contact_cache_confidence', table_name='contact_cache')
    op.drop_index('idx_contact_cache_expires_at', table_name='contact_cache')
    op.drop_index('idx_contact_cache_normalized_company', table_name='contact_cache')
    op.drop_table('contact_cache')
    
    op.drop_index('uq_prospects_company_country_cpv_award', table_name='prospects')
    op.drop_index('idx_prospects_normalized_company', table_name='prospects')
    op.drop_index('idx_prospects_created_at', table_name='prospects')
    op.drop_index('idx_prospects_score', table_name='prospects')
    op.drop_index('idx_prospects_status', table_name='prospects')
    op.drop_table('prospects')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS outboundevent')
    op.execute('DROP TYPE IF EXISTS contactsource')
    op.execute('DROP TYPE IF EXISTS prospectstatus')
