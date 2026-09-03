"use client";

import { useState, useEffect } from "react";
import { QualityGateResult, QualityGatePolicy } from "@/types";
import { evaluateQualityGate, getQualityGate } from "@/lib/api";
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Sliders,
  Copy,
  Check,
  GitMerge,
  AlertTriangle,
  RefreshCw,
  FileCode,
  Layers,
  Sparkles,
  ExternalLink
} from "lucide-react";

interface QualityGateCardProps {
  reportId: string;
}

export default function QualityGateCard({ reportId }: QualityGateCardProps) {
  const [result, setResult] = useState<QualityGateResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [copiedAction, setCopiedAction] = useState<boolean>(false);

  // Policy configuration state
  const [policy, setPolicy] = useState<QualityGatePolicy>({
    min_overall_score: 80,
    min_security_score: 80,
    min_quality_score: 75,
    min_testing_score: 70,
    min_deps_score: 70,
    min_arch_score: 75,
    allow_critical_vulnerabilities: false,
    max_critical_findings: 0,
    max_high_findings: 2,
    allow_circular_dependencies: false,
    allow_architecture_violations: false,
  });

  useEffect(() => {
    loadQualityGate();
  }, [reportId]);

  const loadQualityGate = async (customPolicy?: QualityGatePolicy) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = customPolicy
        ? await evaluateQualityGate(reportId, customPolicy)
        : await getQualityGate(reportId);
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate quality gate.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyCustomPolicy = () => {
    loadQualityGate(policy);
    setIsConfigOpen(false);
  };

  const handleCopyGitHubAction = () => {
    const yaml = `# .github/workflows/repository-auditor-gate.yml
name: "DevSecOps CI/CD Quality Gate"
on: [push, pull_request]
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: "Run Repository Quality Gate"
        run: |
          curl -X POST "${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/audit/${reportId}/quality-gate/evaluate" \\
            -H "Content-Type: application/json"
`;
    navigator.clipboard.writeText(yaml);
    setCopiedAction(true);
    setTimeout(() => setCopiedAction(false), 2000);
  };

  if (isLoading && !result) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm animate-pulse space-y-4">
        <div className="h-6 w-44 bg-slate-800 rounded-lg" />
        <div className="h-32 bg-slate-950/60 rounded-xl" />
      </div>
    );
  }

  if (error || !result) {
    return null;
  }

  const isPassed = result.status === "PASSED" && result.can_merge;

  return (
    <div
      className={`border rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-6 transition-all ${
        isPassed
          ? "bg-gradient-to-b from-slate-900/80 to-emerald-950/20 border-emerald-500/30"
          : "bg-gradient-to-b from-slate-900/80 to-rose-950/20 border-rose-500/30"
      }`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-3">
          <div
            className={`p-3 rounded-xl border shadow-lg ${
              isPassed
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-emerald-500/10"
                : "bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-rose-500/10"
            }`}
          >
            {isPassed ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                CI/CD DevSecOps Quality Gate
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase font-mono flex items-center gap-1 border ${
                  isPassed
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse"
                }`}
              >
                {isPassed ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                <span>{isPassed ? "MERGE PERMITTED" : "MERGE BLOCKED"}</span>
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              {isPassed ? "All Quality Policies Passed" : `${result.failed_rules_count} Quality Gate Violations Detected`}
            </h3>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsConfigOpen(!isConfigOpen)}
            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span>Policy Rules</span>
          </button>

          <button
            onClick={handleCopyGitHubAction}
            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            {copiedAction ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-purple-400" />}
            <span>{copiedAction ? "Copied YAML" : "GitHub Action"}</span>
          </button>
        </div>
      </div>

      {/* Summary Banner */}
      <div
        className={`p-4 rounded-xl border text-xs leading-relaxed flex items-start gap-3 ${
          isPassed
            ? "bg-emerald-950/30 border-emerald-500/20 text-emerald-200"
            : "bg-rose-950/30 border-rose-500/20 text-rose-200"
        }`}
      >
        <GitMerge className={`w-4 h-4 mt-0.5 shrink-0 ${isPassed ? "text-emerald-400" : "text-rose-400"}`} />
        <div>
          <strong className="font-semibold block mb-0.5">
            {isPassed ? "Automated Merge Verification:" : "Blocking Issue Alert:"}
          </strong>
          <span>{result.summary}</span>
        </div>
      </div>

      {/* Policy Configuration Drawer (Expandable) */}
      {isConfigOpen && (
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-5 space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wider font-mono">
                Organizational Quality Gate Policy Thresholds
              </h4>
            </div>
            <button
              onClick={handleApplyCustomPolicy}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all"
            >
              Re-Evaluate Policies
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">Min Overall Score: {policy.min_overall_score}%</label>
              <input
                type="range"
                min="50"
                max="95"
                value={policy.min_overall_score}
                onChange={(e) => setPolicy({ ...policy, min_overall_score: Number(e.target.value) })}
                className="w-full accent-blue-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Min Security Score: {policy.min_security_score}%</label>
              <input
                type="range"
                min="50"
                max="95"
                value={policy.min_security_score}
                onChange={(e) => setPolicy({ ...policy, min_security_score: Number(e.target.value) })}
                className="w-full accent-blue-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Min Test Score: {policy.min_testing_score}%</label>
              <input
                type="range"
                min="40"
                max="90"
                value={policy.min_testing_score}
                onChange={(e) => setPolicy({ ...policy, min_testing_score: Number(e.target.value) })}
                className="w-full accent-blue-500"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-4 pt-2 text-xs text-slate-300">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!policy.allow_critical_vulnerabilities}
                onChange={(e) => setPolicy({ ...policy, allow_critical_vulnerabilities: !e.target.checked })}
                className="accent-rose-500 rounded"
              />
              <span>Block on any Critical Vulnerability</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!policy.allow_circular_dependencies}
                onChange={(e) => setPolicy({ ...policy, allow_circular_dependencies: !e.target.checked })}
                className="accent-blue-500 rounded"
              />
              <span>Block on Circular Architecture Cycles</span>
            </label>
          </div>
        </div>
      )}

      {/* Rules Breakdown Table */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-mono text-[11px] uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Policy Rule</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Required</th>
                <th className="py-3 px-4">Actual Measured</th>
                <th className="py-3 px-4">Policy Evaluation Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {result.rules.map((rule, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-100 flex items-center gap-2">
                    {rule.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    )}
                    <span>{rule.rule_name}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">{rule.category}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                        rule.passed
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {rule.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">{rule.expected}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-200">{rule.actual}</td>
                  <td className="py-3 px-4 text-slate-400 max-w-xs">{rule.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
