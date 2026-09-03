import { AuditReport, SampleRepo, RepoPreview, AgentChatResponse, BenchmarkResult, AuditJob } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function checkApiHealth(): Promise<boolean> {
  try {
    const healthUrl = API_BASE.replace(/\/api\/?$/, "") + "/health";
    const res = await fetch(healthUrl, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function submitAuditJob(data: {
  github_url: string;
  branch?: string;
  llm_provider?: string;
  api_key?: string;
}): Promise<{ message: string; job: AuditJob }> {
  const res = await fetch(`${API_BASE}/jobs/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "devkey",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Job submission failed" }));
    throw new Error(err.detail || "Failed to queue audit job");
  }
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<{ job: AuditJob }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit job status");
  return res.json();
}

export async function previewRepository(githubUrl: string): Promise<RepoPreview> {
  const res = await fetch(`${API_BASE}/repo/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_url: githubUrl }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Preview unavailable" }));
    throw new Error(err.detail || "Failed to preview repository");
  }
  return res.json();
}

export async function fetchSamples(): Promise<SampleRepo[]> {
  const res = await fetch(`${API_BASE}/samples`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch sample repositories");
  return res.json();
}

export async function analyzeRepository(data: {
  github_url: string;
  branch?: string;
  llm_provider?: string;
  api_key?: string;
}): Promise<AuditReport> {
  const res = await fetch(`${API_BASE}/audit/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error occurred" }));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

export async function getReport(reportId: string): Promise<AuditReport> {
  const res = await fetch(`${API_BASE}/audit/${reportId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit report");
  return res.json();
}

export async function sendAgentMessage(data: {
  report_id: string;
  message: string;
  history?: Array<{ role: string; content: string }>;
  llm_provider?: string;
  api_key?: string;
}): Promise<AgentChatResponse> {
  const res = await fetch(`${API_BASE}/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to communicate with AI agent");
  return res.json();
}

export async function streamAgentMessage(
  data: {
    report_id: string;
    message: string;
    history?: Array<{ role: string; content: string }>;
    llm_provider?: string;
    api_key?: string;
  },
  onToolStep: (step: any) => void,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: any) => void
) {
  try {
    const res = await fetch(`${API_BASE}/agent/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok || !res.body) {
      // Fallback to sync endpoint
      const fallback = await sendAgentMessage(data);
      if (fallback.tool_steps) {
        fallback.tool_steps.forEach((ts) => onToolStep(ts));
      }
      onToken(fallback.reply);
      onDone();
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          try {
            const parsed = JSON.parse(trimmed.replace("data: ", ""));
            if (parsed.type === "tool") {
              onToolStep(parsed.data);
            } else if (parsed.type === "token") {
              onToken(parsed.content);
            } else if (parsed.type === "done") {
              onDone();
            }
          } catch (e) {
            // Ignore parse errors on partial chunks
          }
        }
      }
    }
    onDone();
  } catch (err) {
    onError(err);
  }
}

export async function queryCodebaseRAG(reportId: string, query: string) {
  const res = await fetch(`${API_BASE}/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_id: reportId, query }),
  });
  if (!res.ok) throw new Error("Failed to query codebase RAG");
  return res.json();
}

export async function runAutoFix(findingId: string) {
  const res = await fetch(`${API_BASE}/github/autofix/${findingId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute auto-fix loop");
  return res.json();
}

export async function getIssuePreview(findingId: string) {
  const res = await fetch(`${API_BASE}/github/preview-issue/${findingId}`);
  if (!res.ok) throw new Error("Failed to generate issue preview");
  return res.json();
}

export async function getPRPreview(findingId: string) {
  const res = await fetch(`${API_BASE}/github/preview-pr/${findingId}`);
  if (!res.ok) throw new Error("Failed to generate PR preview");
  return res.json();
}

export async function createGitHubIssue(data: { finding_id: string; github_token: string }) {
  const res = await fetch(`${API_BASE}/github/create-issue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "GitHub issue creation failed" }));
    throw new Error(err.detail || "Failed to create issue on GitHub");
  }
  return res.json();
}

export async function runBenchmarkEvaluation(suiteName: string = "Default Ground-Truth Suite"): Promise<BenchmarkResult> {
  const res = await fetch(`${API_BASE}/benchmark/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suite_name: suiteName }),
  });
  if (!res.ok) throw new Error("Failed to run benchmark suite");
  return res.json();
}

// =========================================================
// Auto-Fix & Verification Endpoints
// =========================================================

export async function generateAutoFixProposal(reportId: string, findingId: string): Promise<import("@/types").AutoFixProposal> {
  const res = await fetch(`${API_BASE}/audit/${reportId}/autofix/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ finding_id: findingId, llm_provider: "offline" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Proposal generation failed" }));
    throw new Error(err.detail || "Failed to generate auto-fix proposal");
  }
  return res.json();
}

export async function verifyAutoFix(data: {
  report_id: string;
  finding_id: string;
  session_id?: string;
  patched_code?: string;
  run_tests?: boolean;
}): Promise<import("@/types").AutoFixVerificationResult> {
  const res = await fetch(`${API_BASE}/audit/${data.report_id}/autofix/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      finding_id: data.finding_id,
      session_id: data.session_id,
      patched_code: data.patched_code,
      run_tests: data.run_tests !== false,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Verification execution failed" }));
    throw new Error(err.detail || "Failed to verify auto-fix patch");
  }
  return res.json();
}

export async function createAutoFixPR(data: {
  report_id: string;
  finding_id: string;
  session_id?: string;
  github_token?: string;
  branch_name?: string;
  title?: string;
}): Promise<import("@/types").AutoFixPRResult> {
  const res = await fetch(`${API_BASE}/audit/${data.report_id}/autofix/create-pr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "PR creation failed" }));
    throw new Error(err.detail || "Failed to create PR for auto-fix");
  }
  return res.json();
}

// =========================================================
// Repository Health Timeline Endpoints
// =========================================================

export async function fetchRepositoryTimeline(reportIdOrRepoId: string): Promise<import("@/types").TimelineData> {
  const res = await fetch(`${API_BASE}/audit/${reportIdOrRepoId}/timeline`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Timeline fetch failed" }));
    throw new Error(err.detail || "Failed to fetch repository timeline");
  }
  return res.json();
}

// =========================================================
// CI/CD Quality Gate Endpoints
// =========================================================

export async function evaluateQualityGate(
  reportId: string,
  policy?: Partial<import("@/types").QualityGatePolicy>
): Promise<import("@/types").QualityGateResult> {
  const res = await fetch(`${API_BASE}/audit/${reportId}/quality-gate/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Quality gate evaluation failed" }));
    throw new Error(err.detail || "Failed to evaluate quality gate");
  }
  return res.json();
}

export async function getQualityGate(reportId: string): Promise<import("@/types").QualityGateResult> {
  const res = await fetch(`${API_BASE}/audit/${reportId}/quality-gate`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Quality gate fetch failed" }));
    throw new Error(err.detail || "Failed to fetch quality gate");
  }
  return res.json();
}

// =========================================================
// PR Risk Analyzer & AI Code Review Endpoints
// =========================================================

export async function analyzePRRisk(data: {
  repo_url: string;
  diff_content?: string;
  pr_number?: number;
  base_branch?: string;
  head_branch?: string;
}): Promise<import("@/types").PRRiskAnalysisResult> {
  const res = await fetch(`${API_BASE}/pr/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "PR analysis failed" }));
    throw new Error(err.detail || "Failed to analyze PR risk");
  }
  return res.json();
}

// =========================================================
// Security Attack Path & Architecture Drift Endpoints
// =========================================================

export async function fetchFindingAttackPath(findingId: string): Promise<import("@/types").AttackPathResult> {
  const res = await fetch(`${API_BASE}/audit/findings/${findingId}/attack-path`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Attack path fetch failed" }));
    throw new Error(err.detail || "Failed to trace attack path");
  }
  return res.json();
}

export async function fetchArchitectureDrift(reportId: string): Promise<import("@/types").ArchitectureDriftResult> {
  const res = await fetch(`${API_BASE}/architecture/${reportId}/drift`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Architecture drift fetch failed" }));
    throw new Error(err.detail || "Failed to fetch architecture drift");
  }
  return res.json();
}