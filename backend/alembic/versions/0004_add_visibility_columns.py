"""add visibility/lock columns to audit_jobs

Revision ID: 0004_add_visibility_columns
Revises: 0003_add_indexes
Create Date: 2026-08-22 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_visibility_columns'
down_revision = '0003_add_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('audit_jobs', sa.Column('locked_by', sa.String(length=128), nullable=True))
    op.add_column('audit_jobs', sa.Column('locked_at', sa.DateTime(), nullable=True))
    op.add_column('audit_jobs', sa.Column('visibility_deadline', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('audit_jobs', 'visibility_deadline')
    op.drop_column('audit_jobs', 'locked_at')
    op.drop_column('audit_jobs', 'locked_by')
