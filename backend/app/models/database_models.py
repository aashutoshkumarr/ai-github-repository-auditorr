import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(512), unique=True, index=True, nullable=False)
    owner = Column(String(128), nullable=False)
    name = Column(String(128), nullable=False)
    default_branch = Column(String(64), default="main")
    language = Column(String(64), default="Unknown")
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    is_sample = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reports = relationship("AuditReport", back_populates="repository", cascade="all, delete-orphan")

class AuditReport(Base):
    __tablename__ = "audit_reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    repo_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    status = Column(String(32), default="pending")  # pending, analyzing, completed, failed
    
    # Category Scores (0 - 100)
    overall_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    testing_score = Column(Float, default=0.0)
    docs_score = Column(Float, default=0.0)
    deps_score = Column(Float, default=0.0)
    arch_score = Column(Float, default=0.0)
    maintainability_score = Column(Float, default=0.0)
    
    summary = Column(Text, nullable=True)
    architecture_mermaid = Column(Text, nullable=True)
    fix_order_json = Column(Text, nullable=True)  # JSON array of prioritized fixes
    metrics_json = Column(Text, nullable=True)    # JSON stats
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repository = relationship("Repository", back_populates="reports")
    findings = relationship("Finding", back_populates="report", cascade="all, delete-orphan")
    dependencies = relationship("DependencyVulnerability", back_populates="report", cascade="all, delete-orphan")
    hotspots = relationship("HotspotMetric", back_populates="report", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("audit_reports.id"), nullable=False)
    category = Column(String(64), nullable=False)  # Security, Code Quality, Testing, Documentation, Dependencies, Architecture, Maintainability
    severity = Column(String(32), nullable=False)  # Critical, High, Medium, Low, Informational
    title = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, default=1)
    problem = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    evidence_code = Column(Text, nullable=True)
    confidence = Column(Float, default=0.9)  # 0.0 - 1.0
    cwe_id = Column(String(32), nullable=True)
    rule_id = Column(String(64), nullable=True)
    status = Column(String(32), default="open")  # open, resolved, ignored
    
    report = relationship("AuditReport", back_populates="findings")

class DependencyVulnerability(Base):
    __tablename__ = "dependency_vulnerabilities"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("audit_reports.id"), nullable=False)
    package_name = Column(String(128), nullable=False)
    current_version = Column(String(64), nullable=False)
    recommended_version = Column(String(64), nullable=False)
    severity = Column(String(32), default="Medium")
    advisory_title = Column(String(256), nullable=False)
    cve_id = Column(String(64), nullable=True)
    
    report = relationship("AuditReport", back_populates="dependencies")

class HotspotMetric(Base):
    __tablename__ = "hotspot_metrics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("audit_reports.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    commit_count = Column(Integer, default=1)
    churn_score = Column(Float, default=0.0)
    complexity_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="Low")  # Critical, High, Medium, Low
    
    report = relationship("AuditReport", back_populates="hotspots")

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    suite_name = Column(String(128), default="Default Benchmark Suite")
    test_case_name = Column(String(128), nullable=False)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1 = Column(Float, default=0.0)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    execution_time_s = Column(Float, default=0.0)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Job queue models for durable storage (used by JobQueueManager)
class AuditJobModel(Base):
    __tablename__ = "audit_jobs"

    job_id = Column(String(36), primary_key=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Locking / visibility columns for durable queue
    locked_by = Column(String(128), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    visibility_deadline = Column(DateTime, nullable=True)


class PendingJobModel(Base):
    __tablename__ = "pending_jobs"

    seq = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False)


class AutoFixSession(Base):
    __tablename__ = "autofix_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=False)
    report_id = Column(String(36), ForeignKey("audit_reports.id"), nullable=False)
    status = Column(String(32), default="proposed")  # proposed, approved, testing, verified, failed, pr_created, rejected
    
    file_path = Column(String(512), nullable=False)
    original_code = Column(Text, nullable=True)
    patched_code = Column(Text, nullable=True)
    diff_patch = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    
    test_output = Column(Text, nullable=True)
    security_check_passed = Column(Boolean, default=False)
    tests_passed = Column(Boolean, default=False)
    
    initial_score = Column(Float, default=0.0)
    verified_score = Column(Float, default=0.0)
    score_delta = Column(Float, default=0.0)
    
    pr_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RepositoryHealthTimeline(Base):
    __tablename__ = "repository_health_timeline"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repo_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    report_id = Column(String(36), ForeignKey("audit_reports.id"), nullable=False)
    
    overall_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    testing_score = Column(Float, default=0.0)
    docs_score = Column(Float, default=0.0)
    deps_score = Column(Float, default=0.0)
    arch_score = Column(Float, default=0.0)
    maintainability_score = Column(Float, default=0.0)
    
    findings_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    
    commit_sha = Column(String(64), nullable=True)
    commit_message = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

