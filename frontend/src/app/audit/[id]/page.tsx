"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { AuditReport, Finding } from "@/types";
import { getReport } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import CategoryBreakdown from "@/components/CategoryBreakdown";
import SelfHealingPanel from "@/components/SelfHealingPanel";
import FindingsExplorer from "@/components/FindingsExplorer";
import FindingDetailModal from "@/components/FindingDetailModal";
import ArchitectureDiagram from "@/components/ArchitectureDiagram";
import HotspotHeatmap from "@/components/HotspotHeatmap";
import DependencyTable from "@/components/DependencyTable";
import FixRoadmap from "@/components/FixRoadmap";
import AgentChatDrawer from "@/components/AgentChatDrawer";
import GitHubExportModal from "@/components/GitHubExportModal";
import CodebaseRAGView from "@/components/CodebaseRAGView";
import ScoreLedgerModal from "@/components/ScoreLedgerModal";
import AutoFixModal from "@/components/AutoFixModal";
import HealthTimelineChart from "@/components/HealthTimelineChart";
import QualityGateCard from "@/components/QualityGateCard";
import PRRiskReviewModal from "@/components/PRRiskReviewModal";
import AttackPathModal from "@/components/AttackPathModal";
import ExecutiveReportModal from "@/components/ExecutiveReportModal";
import CommandPalette from "@/components/CommandPalette";
import CodeInspector from "@/components/CodeInspector";
import {
  Github,
  Bot,
  FileDown,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  Code,
  Code2,
  GitPullRequest,
  Layers,
  Flame,
  Package,
  ListOrdered,
  Sparkles,
  Calculator,
  Braces,
  Award,
  Command,
  Check
} from "lucide-react";

export default function AuditReportPage() {
  const params = useParams();
  const reportId = params.id as string;

  const [report, setReport] = useState<AuditReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [gitHubExportFinding, setGitHubExportFinding] = useState<Finding | null>(null);
  const [autoFixFinding, setAutoFixFinding] = useState<Finding | null>(null);
  const [attackPathFinding, setAttackPathFinding] = useState<Finding | null>(null);
  const [isPRModalOpen, setIsPRModalOpen] = useState(false);
  const [isExecutiveReportOpen, setIsExecutiveReportOpen] = useState(false);
  const [isAgentDrawerOpen, setIsAgentDrawerOpen] = useState(false);
  const [isScoreLedgerOpen, setIsScoreLedgerOpen] = useState(false);
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"findings" | "inspector" | "roadmap" | "rag" | "arch" | "hotspots" | "deps">("findings");
  const [isShareCopied, setIsShareCopied] = useState(false);

  useEffect(() => {
    if (!reportId) return;

    setIsLoading(true);
    getReport(reportId)
      .then((data) => {
        setReport(data);
        setIsLoading(false);
      })
      .catch((err) => {
        setErrorMessage(err.message || "Failed to load audit report");
        setIsLoading(false);
      });
  }, [reportId]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-sm font-medium text-slate-300">Loading comprehensive audit report...</p>
      </div>
    );
  }

  if (errorMessage || !report) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center max-w-lg mx-auto space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-slate-100">Audit Report Not Found</h2>
        <p className="text-xs text-slate-400">{errorMessage || "Could not retrieve the requested report."}</p>
        <a
          href="/"
          className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition-colors"
        >
          Return to Home
        </a>
      </div>
    );
  }

  const criticalCount = report.findings.filter((f) => f.severity === "Critical").length;
  const highCount = report.findings.filter((f) => f.severity === "High").length;
  const mediumCount = report.findings.filter((f) => f.severity === "Medium").length;
  const lowCount = report.findings.filter((f) => f.severity === "Low").length;

  const handleExportMarkdown = () => {
    const md = [
      `# Repository Health Audit Report: ${report.repo_owner}/${report.repo_name}`,
      `**URL**: ${report.repo_url}`,
      `**Overall Health Score**: ${report.overall_score}/100`,
      `**Audit Date**: ${new Date(report.created_at).toLocaleString()}`,
      "",
      "## Category Breakdown",
      `- Security: ${report.security_score}/100`,
      `- Code Quality: ${report.quality_score}/100`,
      `- Testing: ${report.testing_score}/100`,
      `- Documentation: ${report.docs_score}/100`,
      `- Dependencies: ${report.deps_score}/100`,
      `- Architecture: ${report.arch_score}/100`,
      `- Maintainability: ${report.maintainability_score}/100`,
      "",
      "## Executive Summary",
      report.summary || "N/A",
      "",
      "## Findings Summary",
      ...report.findings.map(
        (f) => `### [${f.severity}] ${f.title}\n- **File**: \`${f.file_path}:${f.line_number}\`\n- **Problem**: ${f.problem}\n- **Recommendation**: ${f.recommendation}\n`
      )
    ].join("\n");

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-report-${report.repo_owner}-${report.repo_name}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-report-${report.repo_owner}-${report.repo_name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportSARIF = () => {
    const sarif = {
      $schema: "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
      version: "2.1.0",
      runs: [
        {
          tool: {
            driver: {
              name: "AI GitHub Repository Auditor",
              version: "2.0.0",
              informationUri: "https://github.com/repository-auditor",
              rules: report.findings.map((f) => ({
                id: f.rule_id || `RULE-${f.category.toUpperCase()}`,
                name: f.title,
                shortDescription: { text: f.title },
                fullDescription: { text: f.problem },
                help: { text: f.recommendation },
                defaultConfiguration: {
                  level:
                    f.severity.toLowerCase() === "critical" || f.severity.toLowerCase() === "high"
                      ? "error"
                      : f.severity.toLowerCase() === "medium"
                      ? "warning"
                      : "note",
                },
              })),
            },
          },
          results: report.findings.map((f) => ({
            ruleId: f.rule_id || `RULE-${f.category.toUpperCase()}`,
            level:
              f.severity.toLowerCase() === "critical" || f.severity.toLowerCase() === "high"
                ? "error"
                : f.severity.toLowerCase() === "medium"
                ? "warning"
                : "note",
            message: { text: `${f.problem} Recommendation: ${f.recommendation}` },
            locations: [
              {
                physicalLocation: {
                  artifactLocation: { uri: f.file_path },
                  region: {
                    startLine: f.line_number || 1,
                    startColumn: 1,
                  },
                },
              },
            ],
          })),
        },
      ],
    };

    const blob = new Blob([JSON.stringify(sarif, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-${report.repo_owner}-${report.repo_name}.sarif.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShareReport = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      setIsShareCopied(true);
      setTimeout(() => setIsShareCopied(false), 2500);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Top Repo Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight">
              {report.repo_owner} / <span className="text-blue-400">{report.repo_name}</span>
            </h1>
            {report.repo_url && !report.repo_url.includes("sample/") ? (
              <a
                href={report.repo_url}
                target="_blank"
                rel="noopener noreferrer"
                title="Open GitHub Repository"
                className="text-slate-400 hover:text-slate-200 transition-colors p-1 rounded hover:bg-slate-800"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 border border-slate-700 font-mono font-medium">
                Sample Benchmark Repo
              </span>
            )}
          </div>

          <p className="text-xs text-slate-400 font-mono">
            Audited on {new Date(report.created_at).toLocaleDateString()} at {new Date(report.created_at).toLocaleTimeString()}
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleShareReport}
            title="Copy Shareable Audit Report Link"
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            {isShareCopied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Link Copied!</span>
              </>
            ) : (
              <>
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                <span>Share Report</span>
              </>
            )}
          </button>
          <button
            onClick={handleExportMarkdown}
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <FileDown className="w-3.5 h-3.5 text-slate-400" />
            <span>Export MD</span>
          </button>

          <button
            onClick={handleExportJSON}
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <Braces className="w-3.5 h-3.5 text-slate-400" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={handleExportSARIF}
            title="Export GitHub Advanced Security / OASIS SARIF 2.1.0 JSON"
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-blue-950/40 hover:bg-blue-900/50 text-blue-300 border border-blue-500/30 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span>Export SARIF 2.1.0</span>
          </button>

          <button
            onClick={() => setIsPRModalOpen(true)}
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-purple-950/40 hover:bg-purple-900/50 text-purple-300 border border-purple-500/30 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <GitPullRequest className="w-3.5 h-3.5 text-purple-400" />
            <span>PR Review</span>
          </button>

          <button
            onClick={() => setIsExecutiveReportOpen(true)}
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/30 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Award className="w-3.5 h-3.5 text-emerald-400" />
            <span>Executive Report</span>
          </button>

          <button
            onClick={() => setIsAgentDrawerOpen(true)}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2"
          >
            <Bot className="w-4 h-4" />
            <span>Ask AI Agent</span>
          </button>
        </div>
      </div>

      {/* Main Score Gauge */}
      <ScoreGauge
        score={report.overall_score}
        criticalCount={criticalCount}
        highCount={highCount}
        mediumCount={mediumCount}
        lowCount={lowCount}
        onOpenScoreLedger={() => setIsScoreLedgerOpen(true)}
      />

      <SelfHealingPanel selfHealing={report.self_healing} />

      {/* Historical Repository Health Timeline */}
      <HealthTimelineChart reportId={report.id} report={report} />

      {/* CI/CD DevSecOps Quality Gate */}
      <QualityGateCard reportId={report.id} />

      {/* 7 Dimension Category Breakdown */}
      <CategoryBreakdown
        scores={{
          security: report.security_score,
          quality: report.quality_score,
          testing: report.testing_score,
          docs: report.docs_score,
          deps: report.deps_score,
          arch: report.arch_score,
          maintainability: report.maintainability_score,
        }}
        activeCategory={activeCategoryFilter}
        onSelectCategory={(cat) => {
          setActiveCategoryFilter(cat);
          setActiveTab("findings");
        }}
      />

      {/* Executive Summary */}
      {report.summary && (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-3">
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span>Executive Engineering Summary</span>
          </h3>
          <div className="text-xs text-slate-300 leading-relaxed space-y-2 whitespace-pre-wrap">
            {report.summary}
          </div>
        </div>
      )}

      {/* Section Tabs */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("findings")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "findings"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Code className="w-4 h-4" />
            <span>Evidence Findings ({report.findings.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("inspector")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "inspector"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span>Code Inspector (Diffs)</span>
          </button>

          <button
            onClick={() => setActiveTab("roadmap")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "roadmap"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <ListOrdered className="w-4 h-4" />
            <span>Fix Roadmap ({report.fix_order.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("rag")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "rag"
                ? "bg-purple-600 text-white shadow-md border border-purple-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Codebase RAG QA</span>
          </button>

          <button
            onClick={() => setActiveTab("arch")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "arch"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Architecture Diagram</span>
          </button>

          <button
            onClick={() => setActiveTab("hotspots")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "hotspots"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Flame className="w-4 h-4" />
            <span>Git Hotspots ({report.hotspots.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("deps")}
            className={`px-3.5 py-2 text-xs font-semibold rounded-xl flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === "deps"
                ? "bg-blue-600 text-white shadow-md border border-blue-500 toggle-active font-bold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent"
            }`}
          >
            <Package className="w-4 h-4" />
            <span>Dependencies ({report.dependencies.length})</span>
          </button>
        </div>

        {/* Tab Contents */}
        {activeTab === "findings" && (
          <FindingsExplorer
            findings={report.findings}
            onSelectFinding={setSelectedFinding}
            onOpenGitHubIssueModal={setGitHubExportFinding}
            onOpenAutoFixModal={setAutoFixFinding}
            onOpenAttackPathModal={setAttackPathFinding}
            selectedCategory={activeCategoryFilter}
            onClearCategoryFilter={() => setActiveCategoryFilter("")}
          />
        )}

        {activeTab === "inspector" && (
          <CodeInspector
            findings={report.findings}
            onOpenAutoFixModal={setAutoFixFinding}
            onOpenGitHubIssueModal={setGitHubExportFinding}
            onOpenAttackPathModal={setAttackPathFinding}
          />
        )}

        {activeTab === "roadmap" && (
          <FixRoadmap steps={report.fix_order} />
        )}

        {activeTab === "rag" && (
          <CodebaseRAGView reportId={report.id} />
        )}

        {activeTab === "arch" && (
          <ArchitectureDiagram
            reportId={report.id}
            mermaidCode={report.architecture_mermaid || report.metrics?.mermaid_diagram}
            archetype={report.metrics?.architecture_pattern || report.metrics?.archetype}
            confidence={report.metrics?.pattern_confidence}
            explanation={report.metrics?.architecture_explanation || report.self_healing?.architecture_summary}
            risks={report.metrics?.architecture_risks}
            strengths={report.metrics?.architecture_strengths}
            techStackChecklist={report.metrics?.tech_stack_checklist}
            layerFlow={report.metrics?.layer_flow}
            dependencyGraph={report.metrics?.dependency_graph}
            blastRadius={report.metrics?.blast_radius}
            layerViolations={report.metrics?.layer_violations}
            metrics={report.metrics}
          />
        )}

        {activeTab === "hotspots" && (
          <HotspotHeatmap hotspots={report.hotspots} />
        )}

        {activeTab === "deps" && (
          <DependencyTable dependencies={report.dependencies} />
        )}
      </div>

      {/* Score Ledger Modal */}
      <ScoreLedgerModal
        scoreLedger={report.score_ledger}
        overallScore={report.overall_score}
        isOpen={isScoreLedgerOpen}
        onClose={() => setIsScoreLedgerOpen(false)}
      />

      {/* Finding Detail Modal */}
      <FindingDetailModal
        finding={selectedFinding}
        onClose={() => setSelectedFinding(null)}
        onOpenGitHubIssueModal={setGitHubExportFinding}
      />

      {/* Autonomous Auto-Fix & Verification Modal */}
      <AutoFixModal
        reportId={report.id}
        finding={autoFixFinding}
        isOpen={!!autoFixFinding}
        onClose={() => setAutoFixFinding(null)}
        onSuccess={() => {
          getReport(reportId).then(setReport).catch(() => {});
        }}
      />

      {/* PR Risk & AI Code Review Modal */}
      <PRRiskReviewModal
        repoUrl={report.repo_url}
        isOpen={isPRModalOpen}
        onClose={() => setIsPRModalOpen(false)}
      />

      {/* Security Attack Path Modal */}
      <AttackPathModal
        finding={attackPathFinding}
        isOpen={!!attackPathFinding}
        onClose={() => setAttackPathFinding(null)}
        onOpenAutoFix={(f) => setAutoFixFinding(f)}
      />

      {/* GitHub Export Modal */}
      <GitHubExportModal
        finding={gitHubExportFinding}
        onClose={() => setGitHubExportFinding(null)}
      />

      {/* Executive Security & OWASP Compliance Modal */}
      <ExecutiveReportModal
        report={report}
        isOpen={isExecutiveReportOpen}
        onClose={() => setIsExecutiveReportOpen(false)}
      />

      {/* Interactive AI Agent Drawer */}
      <AgentChatDrawer
        reportId={report.id}
        isOpen={isAgentDrawerOpen}
        onClose={() => setIsAgentDrawerOpen(false)}
      />

      {/* Global Command Palette (Cmd+K / Ctrl+K) */}
      <CommandPalette
        onOpenPRModal={() => setIsPRModalOpen(true)}
        onOpenExecutiveModal={() => setIsExecutiveReportOpen(true)}
        onOpenAgentDrawer={() => setIsAgentDrawerOpen(true)}
        onSelectTab={(tab) => setActiveTab(tab as any)}
      />
    </div>
  );
}
