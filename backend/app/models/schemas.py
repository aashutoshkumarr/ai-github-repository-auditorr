from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# =========================================================
# Finding Schema
# =========================================================

class FindingBase(BaseModel):
    category: str
    severity: str
    title: str
    file_path: str
    line_number: int = 1
    problem: str
    recommendation: str
    evidence_code: Optional[str] = None
    confidence: float = 0.9
    cwe_id: Optional[str] = None
    rule_id: Optional[str] = None


class FindingResponse(FindingBase):
    id: str
    report_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# Dependency Vulnerability Schema
# =========================================================

class DependencyVulnerabilityResponse(BaseModel):
    id: str
    package_name: str
    current_version: str
    recommended_version: str
    severity: str
    advisory_title: str
    cve_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# Hotspot Schema
# =========================================================

class HotspotMetricResponse(BaseModel):
    id: str
    file_path: str
    commit_count: int
    churn_score: float
    complexity_score: float
    risk_level: str

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# Prioritized Fix Step Schema
# =========================================================

class FixRoadmapStep(BaseModel):
    order: int
    severity: str
    category: str
    title: str
    file_path: str
    action_summary: str


# =========================================================
# Self-Healing Profile
# =========================================================

class SelfHealingProfile(BaseModel):
    status: str = "Autonomous"

    operating_mode: str = (
        "Audit -> Diagnose -> Fix -> Test -> Verify"
    )

    confidence: float = 0.0

    fixes_generated: int = 0

    tests_created: int = 0

    # -----------------------------------------------------
    # Verification state
    #
    # None  = verification has not run yet
    # False = verification actually ran and failed
    # True  = verification actually ran and passed
    # -----------------------------------------------------

    verification_passed: Optional[bool] = None

    verification_status: str = "pending"

    architecture_summary: str = ""

    automated_steps: List[str] = Field(
        default_factory=list
    )

    predictive_risk: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    risk_graph: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    pr_agent_review: Dict[str, Any] = Field(
        default_factory=dict
    )

    health_trend: List[int] = Field(
        default_factory=list,
        description=(
            "Five-point repository health trend "
            "ordered from oldest to newest."
        ),
    )


# =========================================================
# Audit Request
# =========================================================

class AuditRequest(BaseModel):
    github_url: str = Field(
        ...,
        description="GitHub repository URL to analyze",
    )

    branch: Optional[str] = None

    llm_provider: Optional[str] = "offline"

    api_key: Optional[str] = None

    webhook_url: Optional[str] = None


# =========================================================
# Architecture Analysis Schemas
# =========================================================

class TechStackChecklistItem(BaseModel):
    category: str
    detected: bool
    name: str


class LayerFlowStep(BaseModel):
    layer: str
    icon: str
    description: str


class ArchitectureRiskItem(BaseModel):
    severity: str
    type: str
    title: str
    description: str
    mitigation: str
    file_path: Optional[str] = None


class ArchitectureStrengthItem(BaseModel):
    title: str
    description: str
    badge: str


class DependencyGraphNode(BaseModel):
    id: str
    label: str
    layer: str
    in_degree: int
    out_degree: int
    instability: float
    loc: int
    is_god_module: bool = False
    is_isolated: bool = False


class DependencyGraphEdge(BaseModel):
    source: str
    target: str


class CircularCycleItem(BaseModel):
    signature: str
    length: int
    path: List[str]
    full_path: List[str]
    display: str


class DependencyGraphDetail(BaseModel):
    total_modules: int
    total_dependencies: int
    circular_cycles_count: int
    circular_cycles: List[CircularCycleItem] = Field(default_factory=list)
    tightly_coupled_modules: List[Dict[str, Any]] = Field(default_factory=list)
    isolated_modules: List[str] = Field(default_factory=list)
    god_modules: List[str] = Field(default_factory=list)
    nodes: List[DependencyGraphNode] = Field(default_factory=list)
    edges: List[DependencyGraphEdge] = Field(default_factory=list)


class ArchitectureDetailsResponse(BaseModel):
    pattern: str
    confidence: int
    description: str
    tech_stack: Dict[str, List[str]] = Field(default_factory=dict)
    tech_stack_checklist: List[TechStackChecklistItem] = Field(default_factory=list)
    layer_flow: List[LayerFlowStep] = Field(default_factory=list)
    mermaid_diagram: str = ""
    explanation: str = ""
    risks: List[ArchitectureRiskItem] = Field(default_factory=list)
    strengths: List[ArchitectureStrengthItem] = Field(default_factory=list)
    dependency_graph: Optional[DependencyGraphDetail] = None


# =========================================================
# Audit Report Summary
# =========================================================

class AuditReportSummaryResponse(BaseModel):
    id: str

    repo_id: str

    repo_name: str

    repo_owner: str

    repo_url: str

    status: str

    overall_score: float

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Audit Report Detail
# =========================================================

class AuditReportDetailResponse(BaseModel):
    id: str

    repo_id: str

    repo_name: str

    repo_owner: str

    repo_url: str

    status: str

    overall_score: float

    security_score: float

    quality_score: float

    testing_score: float

    docs_score: float

    deps_score: float

    arch_score: float

    maintainability_score: float

    summary: Optional[str] = None

    architecture_mermaid: Optional[str] = None

    fix_order: List[FixRoadmapStep] = Field(
        default_factory=list
    )

    metrics: Dict[str, Any] = Field(
        default_factory=dict
    )

    score_ledger: Optional[Dict[str, Any]] = None

    self_healing: Optional[SelfHealingProfile] = None

    findings: List[FindingResponse] = Field(
        default_factory=list
    )

    dependencies: List[
        DependencyVulnerabilityResponse
    ] = Field(
        default_factory=list
    )

    hotspots: List[HotspotMetricResponse] = Field(
        default_factory=list
    )

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Agent Chat Schemas
# =========================================================

class AgentChatRequest(BaseModel):
    report_id: str

    message: str

    history: Optional[
        List[Dict[str, str]]
    ] = Field(
        default_factory=list
    )

    llm_provider: Optional[str] = "offline"

    api_key: Optional[str] = None


class AgentToolCallStep(BaseModel):
    tool_name: str

    tool_input: Dict[str, Any]

    tool_output: str


class AgentChatResponse(BaseModel):
    reply: str

    tool_steps: List[
        AgentToolCallStep
    ] = Field(
        default_factory=list
    )


# =========================================================
# GitHub Integration Schemas
# =========================================================

class CreateIssueRequest(BaseModel):
    finding_id: str

    github_token: Optional[str] = None


class CreatePRRequest(BaseModel):
    finding_id: str

    github_token: Optional[str] = None

    branch_name: Optional[str] = None


class IssuePreviewResponse(BaseModel):
    title: str

    body_markdown: str

    labels: List[str]


class PRPreviewResponse(BaseModel):
    title: str

    branch_name: str

    diff_patch: str

    body_markdown: str


# =========================================================
# Benchmark Schemas
# =========================================================

class BenchmarkRunRequest(BaseModel):
    suite_name: Optional[str] = (
        "Default Ground-Truth Benchmark"
    )

    compare_baseline_llm: bool = True


class BenchmarkResponse(BaseModel):
    suite_name: str

    overall_precision: float

    overall_recall: float

    overall_f1: float

    total_cases: int

    test_results: List[
        Dict[str, Any]
    ]

    comparison_vs_naive_llm: Dict[
        str, Any
    ]


# =========================================================
# Auto-Fix Schemas (Human-in-the-Loop Workflow)
# =========================================================

class AutoFixGenerateRequest(BaseModel):
    finding_id: str
    llm_provider: Optional[str] = "offline"
    api_key: Optional[str] = None


class AutoFixProposalResponse(BaseModel):
    session_id: str
    finding_id: str
    file_path: str
    line_number: int
    title: str
    severity: str
    category: str
    original_code: str
    patched_code: str
    diff_patch: str
    explanation: str
    status: str = "proposed"


class AutoFixVerifyRequest(BaseModel):
    session_id: Optional[str] = None
    finding_id: str
    patched_code: Optional[str] = None
    run_tests: bool = True


class AutoFixVerifyResponse(BaseModel):
    session_id: str
    status: str  # verified, failed, unverified
    tests_passed: bool
    security_check_passed: bool
    test_output: str
    initial_score: float
    verified_score: float
    score_delta: float
    verification_reason: str
    remaining_findings_count: int = 0


class AutoFixCreatePRRequest(BaseModel):
    session_id: Optional[str] = None
    finding_id: str
    github_token: Optional[str] = None
    branch_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class AutoFixCreatePRResponse(BaseModel):
    pr_url: str
    pr_number: Optional[int] = None
    branch_name: str
    status: str = "success"
    message: str


# =========================================================
# Repository Health Timeline Schemas
# =========================================================

class TimelinePoint(BaseModel):
    audit_id: str
    created_at: datetime
    overall_score: float
    security_score: float
    quality_score: float
    testing_score: float
    docs_score: float
    deps_score: float
    arch_score: float
    maintainability_score: float
    findings_count: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None


class TimelineResponse(BaseModel):
    repo_id: str
    repo_name: str
    repo_url: str
    points: List[TimelinePoint] = Field(default_factory=list)
    trend: str = "Stable"  # Improving, Degrading, Stable
    average_score: float = 0.0
    latest_score: float = 0.0
    score_delta: float = 0.0
    has_regression: bool = False


# =========================================================
# CI/CD Quality Gate Schemas
# =========================================================

class QualityGatePolicy(BaseModel):
    min_overall_score: float = 80.0
    min_security_score: float = 80.0
    min_quality_score: float = 75.0
    min_testing_score: float = 70.0
    min_deps_score: float = 70.0
    min_arch_score: float = 75.0
    allow_critical_vulnerabilities: bool = False
    max_critical_findings: int = 0
    max_high_findings: int = 2
    allow_circular_dependencies: bool = False
    allow_architecture_violations: bool = False


class QualityGateRuleEvaluation(BaseModel):
    rule_name: str
    category: str
    status: str  # "PASSED" | "FAILED"
    expected: str
    actual: str
    passed: bool
    reason: str


class QualityGateEvaluateRequest(BaseModel):
    policy: Optional[QualityGatePolicy] = None


class QualityGateResult(BaseModel):
    report_id: str
    repo_name: str
    status: str  # "PASSED" | "FAILED"
    can_merge: bool
    overall_score: float
    summary: str
    passed_rules_count: int
    failed_rules_count: int
    rules: List[QualityGateRuleEvaluation] = Field(default_factory=list)
    markdown_report: str


# =========================================================
# PR Risk Analyzer & AI Code Review Schemas
# =========================================================

class PRAnalysisRequest(BaseModel):
    repo_url: str
    base_branch: Optional[str] = "main"
    head_branch: Optional[str] = None
    pr_number: Optional[int] = None
    diff_content: Optional[str] = None
    llm_provider: Optional[str] = "offline"
    api_key: Optional[str] = None


class PRReviewComment(BaseModel):
    file_path: str
    line_number: int
    severity: str  # "Critical" | "High" | "Medium" | "Low" | "Suggestion"
    category: str
    comment: str
    suggested_fix: Optional[str] = None


class PRRiskAnalysisResult(BaseModel):
    pr_number: Optional[int] = None
    repo_url: str
    risk_level: str  # "Low" | "Medium" | "High" | "Critical"
    blast_radius_score: float
    files_changed_count: int
    lines_added: int
    lines_deleted: int
    security_delta_findings: List[FindingResponse] = Field(default_factory=list)
    complexity_delta: float
    test_coverage_delta: float
    has_test_changes: bool
    summary: str
    review_comments: List[PRReviewComment] = Field(default_factory=list)
    can_merge_safely: bool


# =========================================================
# Architecture Drift Schemas
# =========================================================

class ArchitectureDriftResult(BaseModel):
    repo_id: str
    base_report_id: str
    current_report_id: str
    drift_detected: bool
    drift_severity: str  # "None" | "Low" | "Medium" | "High"
    added_components: List[str] = Field(default_factory=list)
    removed_components: List[str] = Field(default_factory=list)
    added_flows: List[str] = Field(default_factory=list)
    removed_flows: List[str] = Field(default_factory=list)
    new_violations: List[str] = Field(default_factory=list)
    drift_mermaid: str
    explanation: str


# =========================================================
# Attack Path Schemas
# =========================================================

class AttackPathNode(BaseModel):
    step_number: int
    layer: str
    component_or_file: str
    action_or_call: str
    risk_description: str
    is_source: bool = False
    is_sink: bool = False


class AttackPathResult(BaseModel):
    finding_id: str
    title: str
    severity: str
    cwe_id: Optional[str] = None
    entry_point: str
    sink_point: str
    nodes: List[AttackPathNode] = Field(default_factory=list)
    mermaid_flow: str
    remediation_summary: str