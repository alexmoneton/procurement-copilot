"""Add user profiles table

Revision ID: 0004_add_user_profiles
Revises: 0003_add_outreach_system
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004_add_user_profiles'
down_revision = '0003_add_outreach_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_profiles table
    op.create_table('user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('target_value_range', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('preferred_countries', postgresql.ARRAY(sa.String(length=2)), nullable=True),
        sa.Column('cpv_expertise', postgresql.ARRAY(sa.String(length=10)), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=False)


def downgrade():
    # Drop user_profiles table
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
