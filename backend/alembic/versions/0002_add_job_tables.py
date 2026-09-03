"""add job tables

Revision ID: 0002_add_job_tables
Revises: 0001_initial
Create Date: 2026-08-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_job_tables'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_jobs',
        sa.Column('job_id', sa.String(length=36), primary_key=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'pending_jobs',
        sa.Column('seq', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', sa.String(length=36), unique=True, nullable=False),
    )


def downgrade():
    op.drop_table('pending_jobs')
    op.drop_table('audit_jobs')
