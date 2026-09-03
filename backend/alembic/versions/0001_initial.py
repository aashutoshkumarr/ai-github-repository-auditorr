"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('owner', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('default_branch', sa.String(length=64), nullable=True),
        sa.Column('language', sa.String(length=64), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=True),
        sa.Column('forks', sa.Integer(), nullable=True),
        sa.Column('is_sample', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create audit_reports table
    op.create_table(
        'audit_reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('repo_id', sa.String(length=36), sa.ForeignKey('repositories.id'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('security_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('testing_score', sa.Float(), nullable=True),
        sa.Column('docs_score', sa.Float(), nullable=True),
        sa.Column('deps_score', sa.Float(), nullable=True),
        sa.Column('arch_score', sa.Float(), nullable=True),
        sa.Column('maintainability_score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('architecture_mermaid', sa.Text(), nullable=True),
        sa.Column('fix_order_json', sa.Text(), nullable=True),
        sa.Column('metrics_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # Create findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('audit_reports.id'), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('problem', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('evidence_code', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('cwe_id', sa.String(length=32), nullable=True),
        sa.Column('rule_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
    )

    # Create dependency_vulnerabilities table
    op.create_table(
        'dependency_vulnerabilities',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('audit_reports.id'), nullable=False),
        sa.Column('package_name', sa.String(length=128), nullable=False),
        sa.Column('current_version', sa.String(length=64), nullable=False),
        sa.Column('recommended_version', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=True),
        sa.Column('advisory_title', sa.String(length=256), nullable=False),
        sa.Column('cve_id', sa.String(length=64), nullable=True),
    )

    # Create hotspot_metrics table
    op.create_table(
        'hotspot_metrics',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('audit_reports.id'), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('commit_count', sa.Integer(), nullable=True),
        sa.Column('churn_score', sa.Float(), nullable=True),
        sa.Column('complexity_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(length=32), nullable=True),
    )

    # Create benchmark_results table
    op.create_table(
        'benchmark_results',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('suite_name', sa.String(length=128), nullable=True),
        sa.Column('test_case_name', sa.String(length=128), nullable=False),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1', sa.Float(), nullable=True),
        sa.Column('true_positives', sa.Integer(), nullable=True),
        sa.Column('false_positives', sa.Integer(), nullable=True),
        sa.Column('false_negatives', sa.Integer(), nullable=True),
        sa.Column('execution_time_s', sa.Float(), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('benchmark_results')
    op.drop_table('hotspot_metrics')
    op.drop_table('dependency_vulnerabilities')
    op.drop_table('findings')
    op.drop_table('audit_reports')
    op.drop_table('repositories')
