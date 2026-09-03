"""add indexes for job tables

Revision ID: 0003_add_indexes
Revises: 0002_add_job_tables
Create Date: 2026-08-22 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_indexes'
down_revision = '0002_add_job_tables'
branch_labels = None
depends_on = None


def upgrade():
    # index to speed up job listing by created_at
    op.create_index('ix_audit_jobs_created_at', 'audit_jobs', ['created_at'])
    # index for quick lookup on pending job_id
    op.create_index('ix_pending_jobs_job_id', 'pending_jobs', ['job_id'])


def downgrade():
    op.drop_index('ix_pending_jobs_job_id', table_name='pending_jobs')
    op.drop_index('ix_audit_jobs_created_at', table_name='audit_jobs')
