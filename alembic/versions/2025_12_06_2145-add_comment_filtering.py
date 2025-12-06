"""Add comment filtering tables

Revision ID: 9a1b2c3d4e5f
Revises: 8f7f9c9512ec
Create Date: 2025-12-06 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '8f7f9c9512ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create comment filtering tables."""
    
    # Create allowed_commenters table
    op.create_table(
        'allowed_commenters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_username', sa.String(length=255), nullable=False),
        sa.Column('github_user_id', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('added_by', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_comment_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_username')
    )
    op.create_index('idx_allowed_commenters_username', 'allowed_commenters', ['github_username'])
    op.create_index('idx_allowed_commenters_enabled', 'allowed_commenters', ['enabled'])
    op.create_index('idx_allowed_commenters_user_id', 'allowed_commenters', ['github_user_id'])
    
    # Create comment_filter_settings table
    op.create_table(
        'comment_filter_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_add_commenters', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_reply_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'auto_reply_message',
            sa.Text(),
            nullable=False,
            server_default='Thank you for your comment! User @{username} has been added to the allowed commenters list. '
            'Comments from this user will now be processed. You can manage this in your AutoPR dashboard.'
        ),
        sa.Column('whitelist_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_comment_filter_settings_enabled', 'comment_filter_settings', ['enabled'])
    
    # Insert default settings (singleton record)
    op.execute("""
        INSERT INTO comment_filter_settings (id, enabled, auto_add_commenters, auto_reply_enabled, whitelist_mode)
        VALUES (gen_random_uuid(), true, false, true, true)
    """)


def downgrade() -> None:
    """Downgrade schema - remove comment filtering tables."""
    op.drop_index('idx_comment_filter_settings_enabled', table_name='comment_filter_settings')
    op.drop_table('comment_filter_settings')
    
    op.drop_index('idx_allowed_commenters_user_id', table_name='allowed_commenters')
    op.drop_index('idx_allowed_commenters_enabled', table_name='allowed_commenters')
    op.drop_index('idx_allowed_commenters_username', table_name='allowed_commenters')
    op.drop_table('allowed_commenters')
