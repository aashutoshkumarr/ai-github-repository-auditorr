export interface Finding {
  id: string;
  report_id: string;
  category: string;
  severity:
    | "Critical"
    | "High"
    | "Medium"
    | "Low"
    | "Informational";
  title: string;
  file_path: string;
  line_number: number;
  problem: string;
  recommendation: string;
  evidence_code?: string;
  confidence: number;
  cwe_id?: string;
  rule_id?: string;
  status: string;
}

export interface DependencyVulnerability {
  id: string;
  package_name: string;
  current_version: string;
  recommended_version: string;
  severity: string;
  advisory_title: string;
  cve_id?: string;
  is_breaking_risk?: boolean;
  upgrade_command?: string;
}

export interface HotspotMetric {
  id: string;
  file_path: string;
  commit_count: number;
  churn_score: number;
  complexity_score: number;
  risk_level:
    | "Critical"
    | "High"
    | "Medium"
    | "Low";
  top_author?: string;
  author_count?: number;
  is_bus_factor_risk?: boolean;
}

export interface FixRoadmapStep {
  order: number;
  severity: string;
  category: string;
  title: string;
  file_path: string;
  action_summary: string;
}

export interface SelfHealingProfile {
  status: string;
  operating_mode: string;

  confidence: number;

  /**
   * Number of remediation targets generated
   * by the audit.
   *
   * IMPORTANT:
   * This does NOT mean fixes were actually applied.
   */
  fixes_generated: number;

  /**
   * Number of validation/test targets generated
   * by the audit.
   *
   * IMPORTANT:
   * This does NOT mean tests were actually executed.
   */
  tests_created: number;

  /**
   * Legacy verification flag.
   *
   * null  = verification has not run
   * true  = verification passed
   * false = verification failed OR legacy response
   *
   * IMPORTANT:
   * When verification_status exists, the frontend
   * should use verification_status as the source
   * of truth.
   */
  verification_passed: boolean | null;

  /**
   * Authoritative verification state.
   *
   * pending  = verification has not been executed
   * passed   = verification executed and passed
   * verified = verification executed and passed
   * failed   = verification executed and failed
   *
   * Optional for backwards compatibility with
   * older API responses.
   */
  verification_status?:
    | "pending"
    | "passed"
    | "verified"
    | "failed"
    | null;

  architecture_summary: string;

  automated_steps: string[];

  predictive_risk: Array<{
    component: string;
    risk_score: number;
    trigger: string;
    explanation: string;
  }>;

  risk_graph: Array<{
    source: string;
    target: string;
    severity: string;
    propagation: string;
  }>;

  pr_agent_review: {
    summary: string;
    recommended_commit: string;
    branch_ready: boolean;
    review_score: number;
  };

  /**
   * Repository health history.
   *
   * Values are expected to be between 0 and 100.
   */
  health_trend: number[];
}

export interface TechStackChecklistItem {
  category: string;
  detected: boolean;
  name: string;
}

export interface LayerFlowStep {
  layer: string;
  icon: string;
  description: string;
}

export interface ArchitectureRiskItem {
  severity: string;
  type: string;
  title: string;
  description: string;
  mitigation: string;
  file_path?: string;
}

export interface ArchitectureStrengthItem {
  title: string;
  description: string;
  badge: string;
}

export interface DependencyGraphNode {
  id: string;
  label: string;
  layer: string;
  in_degree: number;
  out_degree: number;
  instability: number;
  loc: number;
  is_god_module?: boolean;
  is_isolated?: boolean;
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
}

export interface CircularCycleItem {
  signature: string;
  length: number;
  path: string[];
  full_path: string[];
  display: string;
}

export interface DependencyGraphDetail {
  total_modules: number;
  total_dependencies: number;
  circular_cycles_count: number;
  circular_cycles: CircularCycleItem[];
  tightly_coupled_modules: Array<Record<string, any>>;
  isolated_modules: string[];
  god_modules: string[];
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
}

export interface TechnologyEvidenceItem {
  technology: string;
  category: string;
  evidence: string[];
  confidence: number;
  version?: string;
}

export interface ComponentItem {
  name: string;
  type: string;
  layer: string;
  files: string[];
  file_count: number;
  loc: number;
  description: string;
  technology?: string;
}

export interface LayerViolationItem {
  source_layer: string;
  target_layer: string;
  source_file: string;
  target_file: string;
  description: string;
  severity: string;
}

export interface BlastRadiusItem {
  target_module: string;
  affected_modules: string[];
  affected_endpoints: string[];
  affected_services: string[];
  affected_tests: string[];
  risk_level: string;
  total_impact_score: number;
}

export interface AuditReport {
  id: string;

  repo_id: string;
  repo_name: string;
  repo_owner: string;
  repo_url: string;

  status: string;

  overall_score: number;
  security_score: number;
  quality_score: number;
  testing_score: number;
  docs_score: number;
  deps_score: number;
  arch_score: number;
  maintainability_score: number;

  summary?: string;
  architecture_mermaid?: string;

  fix_order: FixRoadmapStep[];

  metrics: Record<string, any>;

  score_ledger?: Record<string, any>;

  self_healing?: SelfHealingProfile;

  findings: Finding[];

  dependencies: DependencyVulnerability[];

  hotspots: HotspotMetric[];

  created_at: string;
}

export interface SampleRepo {
  id: string;
  name: string;
  owner: string;
  url: string;
  alias: string;
  language: string;
  description: string;
  badge: string;
  tags: string[];
}

export interface RepoPreview {
  owner: string;
  name: string;
  url: string;
  description: string;
  default_branch: string;
  language: string;
  stars: number;
  forks: number;
  topics: string[];
  tech_stack: string[];
  summary: string;
  readme_excerpt: string;
}

export interface AuditJob {
  id: string;
  status: string;
  stage: string;
  percent_complete: number;
  created_at: string;
  updated_at: string;
  request: Record<string, any>;
  report_id?: string | null;
  error?: string | null;
}

export interface AgentToolStep {
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output: string;
}

export interface AgentChatResponse {
  reply: string;
  tool_steps: AgentToolStep[];
}

export interface BenchmarkResult {
  suite_name: string;

  overall_precision: number;
  overall_recall: number;
  overall_f1: number;

  total_cases: number;

  total_execution_time_s: number;

  test_results: Array<{
    case_name: string;
    description: string;

    true_positives: number;
    false_positives: number;
    false_negatives: number;

    precision: number;
    recall: number;
    f1_score: number;

    execution_time_s: number;

    detected_count: number;
    expected_count: number;
  }>;

  comparison_vs_naive_llm: {
    our_system: {
      name: string;
      precision: number;
      recall: number;
      f1_score: number;
      finding_groundedness: number;
      false_positive_rate: number;
    };

    naive_llm_baseline: {
      name: string;
      precision: number;
      recall: number;
      f1_score: number;
      finding_groundedness: number;
      false_positive_rate: number;
    };
  };
}

export interface AutoFixProposal {
  session_id: string;
  finding_id: string;
  file_path: string;
  line_number: number;
  title: string;
  severity: string;
  category: string;
  original_code: string;
  patched_code: string;
  diff_patch: string;
  explanation: string;
  status: string;
}

export interface AutoFixVerificationResult {
  session_id: string;
  status: "verified" | "failed" | "unverified";
  tests_passed: boolean;
  security_check_passed: boolean;
  test_output: string;
  initial_score: number;
  verified_score: number;
  score_delta: number;
  verification_reason: string;
  remaining_findings_count: number;
}

export interface AutoFixPRResult {
  pr_url: string;
  pr_number?: number;
  branch_name: string;
  status: string;
  message: string;
}

export interface TimelinePoint {
  audit_id: string;
  created_at: string;
  overall_score: number;
  security_score: number;
  quality_score: number;
  testing_score: number;
  docs_score: number;
  deps_score: number;
  arch_score: number;
  maintainability_score: number;
  findings_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  commit_sha?: string;
  commit_message?: string;
}

export interface TimelineData {
  repo_id: string;
  repo_name: string;
  repo_url: string;
  points: TimelinePoint[];
  trend: "Improving" | "Degrading" | "Stable";
  average_score: number;
  latest_score: number;
  score_delta: number;
  has_regression: boolean;
}

export interface QualityGatePolicy {
  min_overall_score: number;
  min_security_score: number;
  min_quality_score: number;
  min_testing_score: number;
  min_deps_score: number;
  min_arch_score: number;
  allow_critical_vulnerabilities: boolean;
  max_critical_findings: number;
  max_high_findings: number;
  allow_circular_dependencies: boolean;
  allow_architecture_violations: boolean;
}

export interface QualityGateRule {
  rule_name: string;
  category: string;
  status: "PASSED" | "FAILED";
  expected: string;
  actual: string;
  passed: boolean;
  reason: string;
}

export interface QualityGateResult {
  report_id: string;
  repo_name: string;
  status: "PASSED" | "FAILED";
  can_merge: boolean;
  overall_score: number;
  summary: string;
  passed_rules_count: number;
  failed_rules_count: number;
  rules: QualityGateRule[];
  markdown_report: string;
}

export interface PRReviewComment {
  file_path: string;
  line_number: number;
  severity: "Critical" | "High" | "Medium" | "Low" | "Suggestion";
  category: string;
  comment: string;
  suggested_fix?: string;
}

export interface PRRiskAnalysisResult {
  pr_number?: number;
  repo_url: string;
  risk_level: "Low" | "Medium" | "High" | "Critical";
  blast_radius_score: number;
  files_changed_count: number;
  lines_added: number;
  lines_deleted: number;
  security_delta_findings: Finding[];
  complexity_delta: number;
  test_coverage_delta: number;
  has_test_changes: boolean;
  summary: string;
  review_comments: PRReviewComment[];
  can_merge_safely: boolean;
}

export interface AttackPathNode {
  step_number: number;
  layer: string;
  component_or_file: string;
  action_or_call: string;
  risk_description: string;
  is_source?: boolean;
  is_sink?: boolean;
}

export interface AttackPathResult {
  finding_id: string;
  title: string;
  severity: string;
  cwe_id?: string;
  entry_point: string;
  sink_point: string;
  nodes: AttackPathNode[];
  mermaid_flow: string;
  remediation_summary: string;
}

export interface ArchitectureDriftResult {
  repo_id: string;
  base_report_id: string;
  current_report_id: string;
  drift_detected: boolean;
  drift_severity: "None" | "Low" | "Medium" | "High";
  added_components: string[];
  removed_components: string[];
  added_flows: string[];
  removed_flows: string[];
  new_violations: string[];
  drift_mermaid: string;
  explanation: string;
}