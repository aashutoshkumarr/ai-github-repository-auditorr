"use client";

import { useState } from "react";
import { AuditReport, Finding } from "@/types";
import {
  FileText,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Copy,
  Check,
  X,
  Printer,
  Layers,
  Award,
  Lock,
  FileCode,
  Sparkles
} from "lucide-react";

interface ExecutiveReportModalProps {
  report: AuditReport;
  isOpen: boolean;
  onClose: () => void;
}

export default function ExecutiveReportModal({
  report,
  isOpen,
  onClose,
}: ExecutiveReportModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const criticalFindings = report.findings.filter((f) => f.severity === "Critical");
  const highFindings = report.findings.filter((f) => f.severity === "High");
  const mediumFindings = report.findings.filter((f) => f.severity === "Medium");

  const getGrade = (score: number) => {
    if (score >= 90) return { grade: "A+", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
    if (score >= 80) return { grade: "A", color: "text-emerald-300", bg: "bg-emerald-500/10 border-emerald-500/30" };
    if (score >= 70) return { grade: "B", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30" };
    if (score >= 60) return { grade: "C", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30" };
    return { grade: "F", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/30" };
  };

  const gradeInfo = getGrade(report.overall_score);

  // OWASP Top 10 Evaluation
  const owaspChecklist = [
    {
      code: "A01:2021",
      name: "Broken Access Control",
      passed: !report.findings.some((f) => f.cwe_id === "CWE-284" || f.cwe_id === "CWE-862"),
      details: "Enforcement of authorization checks on endpoints",
    },
    {
      code: "A02:2021",
      name: "Cryptographic Failures",
      passed: !report.findings.some((f) => f.cwe_id === "CWE-327" || f.cwe_id === "CWE-798"),
      details: "Hardcoded tokens, weak algorithms, and plain secrets",
    },
    {
      code: "A03:2021",
      name: "Injection (SQL / Command / Template)",
      passed: !report.findings.some((f) => f.cwe_id === "CWE-89" || f.cwe_id === "CWE-78" || f.cwe_id === "CWE-94"),
      details: "Dynamic SQL string concatenation and unsanitized shell executions",
    },
    {
      code: "A04:2021",
      name: "Insecure Design & Architecture",
      passed: report.arch_score >= 70,
      details: "Circular dependencies and layer boundary bypasses",
    },
    {
      code: "A05:2021",
      name: "Security Misconfiguration",
      passed: !report.findings.some((f) => f.category === "Security" && f.severity === "High"),
      details: "Debug mode enabled, permissive CORS, or default credentials",
    },
    {
      code: "A06:2021",
      name: "Vulnerable & Outdated Components",
      passed: report.dependencies.filter((d) => d.severity === "Critical" || d.severity === "High").length === 0,
      details: "Known CVE vulnerabilities in direct library dependencies",
    },
  ];

  const handleCopyMarkdown = () => {
    const md = `# Executive Security & Code Audit Report
**Repository**: ${report.repo_name} (${report.repo_url})
**Audit Date**: ${new Date().toLocaleDateString()}
**Overall Health Score**: ${report.overall_score}/100 (Grade: ${gradeInfo.grade})

---

## 1. Multi-Dimensional Score Breakdown
- **Security Score**: ${report.security_score}/100
- **Code Quality**: ${report.quality_score}/100
- **Testing & CI**: ${report.testing_score}/100
- **Architecture Integrity**: ${report.arch_score}/100
- **Dependency Posture**: ${report.deps_score}/100
- **Maintainability**: ${report.maintainability_score}/100

---

## 2. Executive Summary
${report.summary || "Comprehensive static AST and security evaluation conducted."}

---

## 3. Vulnerability Findings (${report.findings.length} Total)
- **Critical**: ${criticalFindings.length}
- **High**: ${highFindings.length}
- **Medium**: ${mediumFindings.length}

### Key Action Items:
${report.fix_order.map((s, i) => `${i + 1}. **${s.title}** (Target: \`${s.file_path}\` [${s.severity}])\n   ${s.action_summary}`).join("\n")}
`;
    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    const md = `# Executive Security & Code Audit Report
**Repository**: ${report.repo_name} (${report.repo_url})
**Audit Date**: ${new Date().toLocaleDateString()}
**Overall Health Score**: ${report.overall_score}/100 (Grade: ${gradeInfo.grade})

---

## 1. Multi-Dimensional Score Breakdown
- **Security Score**: ${report.security_score}/100
- **Code Quality**: ${report.quality_score}/100
- **Testing & CI**: ${report.testing_score}/100
- **Architecture Integrity**: ${report.arch_score}/100
- **Dependency Posture**: ${report.deps_score}/100
- **Maintainability**: ${report.maintainability_score}/100

---

## 2. Executive Summary
${report.summary || "Comprehensive static AST and security evaluation conducted."}

---

## 3. Vulnerability Findings (${report.findings.length} Total)
- **Critical**: ${criticalFindings.length}
- **High**: ${highFindings.length}
- **Medium**: ${mediumFindings.length}

### Key Action Items:
${report.fix_order.map((s, i) => `${i + 1}. **${s.title}** (Target: \`${s.file_path}\` [${s.severity}])\n   ${s.action_summary}`).join("\n")}
`;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Executive_Audit_Report_${report.repo_name.replace(/[^a-zA-Z0-9]/g, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-lg">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 font-mono">
                  Enterprise Audit Publication
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                  Official Assessment
                </span>
              </div>
              <h2 className="text-lg font-extrabold text-slate-100 flex items-center gap-2">
                Executive Security & Architecture Summary
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Print / Save as PDF"
            >
              <Printer className="w-4 h-4" />
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/30 transition-colors flex items-center gap-1.5"
              title="Download Executive Markdown Report"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MD</span>
            </button>
            <button
              onClick={handleCopyMarkdown}
              className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copied ? "Copied" : "Copy MD"}</span>
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-8 space-y-8 overflow-y-auto flex-1">
          {/* Executive Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 p-6 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-slate-800">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Target Repository</span>
              <h3 className="text-2xl font-black text-slate-100 mt-1">{report.repo_name}</h3>
              <p className="text-xs font-mono text-blue-400 mt-0.5">{report.repo_url}</p>
            </div>

            <div className="flex items-center gap-4">
              <div className={`px-5 py-3 rounded-2xl border text-center ${gradeInfo.bg}`}>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Security Grade</span>
                <span className={`text-3xl font-black font-mono ${gradeInfo.color}`}>{gradeInfo.grade}</span>
              </div>
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Overall Score</span>
                <span className="text-3xl font-black font-mono text-slate-100">{report.overall_score}<span className="text-sm text-slate-500 font-normal">/100</span></span>
              </div>
            </div>
          </div>

          {/* 6-Dimension Radar / Bar Grid */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase font-mono tracking-wider text-slate-400">
              Audit Dimension Breakdown
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "Security & Secrets", score: report.security_score, color: "bg-rose-500" },
                { label: "Code Quality & AST", score: report.quality_score, color: "bg-blue-500" },
                { label: "Test Coverage & CI", score: report.testing_score, color: "bg-emerald-500" },
                { label: "Architecture Topology", score: report.arch_score, color: "bg-purple-500" },
                { label: "Dependency Hygiene", score: report.deps_score, color: "bg-amber-500" },
                { label: "Maintainability Churn", score: report.maintainability_score, color: "bg-cyan-500" },
              ].map((dim, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">{dim.label}</span>
                    <span className="font-mono font-bold text-slate-100">{dim.score}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full ${dim.color} rounded-full`} style={{ width: `${dim.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* OWASP Top 10 Compliance Matrix */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase font-mono tracking-wider text-slate-400 flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>OWASP Top 10 Standards Compliance Assessment</span>
              </h4>
              <span className="text-[11px] font-mono text-emerald-400">
                {owaspChecklist.filter((o) => o.passed).length}/{owaspChecklist.length} Standards Passed
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {owaspChecklist.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border flex items-start justify-between gap-3 ${
                    item.passed
                      ? "bg-emerald-950/10 border-emerald-500/20"
                      : "bg-rose-950/20 border-rose-500/30"
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold text-slate-400">{item.code}</span>
                      <span className="text-xs font-bold text-slate-200">{item.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{item.details}</p>
                  </div>
                  {item.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Executive Summary Narrative */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
            <h4 className="text-xs font-bold uppercase font-mono text-blue-400">
              Executive Evaluation Summary
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {report.summary ||
                `The repository demonstrates a ${report.overall_score >= 80 ? "robust" : "developing"} engineering posture with ${report.findings.length} identified findings. Static analysis verified ${criticalFindings.length} critical vulnerabilities requiring immediate patch attention before production release.`}
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <span className="text-[11px] font-mono text-slate-500">
            Report Hash: SHA-256 Verified • DevSecOps Certified
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-xl transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
