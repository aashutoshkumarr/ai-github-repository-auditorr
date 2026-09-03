"use client";

import { Finding } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import { runAutoFix } from "@/lib/api";
import { X, Copy, Check, ShieldAlert, Sparkles, Terminal, FileCode, CheckCircle2, Wrench, RefreshCw, AlertTriangle } from "lucide-react";
import { useState } from "react";

interface FindingDetailModalProps {
  finding: Finding | null;
  onClose: () => void;
  onOpenGitHubIssueModal: (finding: Finding) => void;
}

interface AutoFixState {
  status: string;
  diff_patch: string;
  tests_passed: boolean;
  security_check_passed: boolean;
  iterations: number;
  log: string[];
}

export default function FindingDetailModal({
  finding,
  onClose,
  onOpenGitHubIssueModal
}: FindingDetailModalProps) {
  const [copied, setCopied] = useState(false);
  const [isAutoFixing, setIsAutoFixing] = useState(false);
  const [autoFixResult, setAutoFixResult] = useState<AutoFixState | null>(null);

  if (!finding) return null;

  const badge = getSeverityBadge(finding.severity);

  const handleCopyFix = () => {
    navigator.clipboard.writeText(finding.recommendation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunAutoFix = async () => {
    setIsAutoFixing(true);
    setAutoFixResult(null);

    try {
      const data = await runAutoFix(finding.id);
      setAutoFixResult(data);
    } catch (err) {
      console.error("AutoFix failed:", err);
    } finally {
      setIsAutoFixing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Badges */}
        <div className="flex items-center gap-2 flex-wrap mb-3">
          <span className={cn("px-2.5 py-0.5 text-xs font-bold rounded-md border flex items-center gap-1", badge.bg, badge.text, badge.border)}>
            <span>{badge.icon}</span> {finding.severity}
          </span>
          <span className="px-2 py-0.5 text-xs font-medium bg-slate-800 text-slate-300 rounded-md">
            {finding.category}
          </span>
          {finding.cwe_id && (
            <span className="px-2 py-0.5 text-[11px] font-mono text-purple-400 bg-purple-950/40 border border-purple-800/50 rounded-md">
              {finding.cwe_id}
            </span>
          )}
          <span className="text-xs text-slate-400 font-mono ml-auto">
            Confidence: <strong className="text-slate-100">{Math.round(finding.confidence * 100)}%</strong>
          </span>
        </div>

        {/* Title */}
        <h2 className="text-lg font-bold text-slate-100 mb-2">{finding.title}</h2>

        {/* File location */}
        <div className="flex items-center gap-2 text-xs font-mono text-blue-400 bg-slate-950/70 px-3 py-2 rounded-lg border border-slate-800 mb-5">
          <FileCode className="w-4 h-4" />
          <span>{finding.file_path} (Line {finding.line_number})</span>
        </div>

        {/* Problem Section */}
        <div className="space-y-4 text-xs">
          <div>
            <h4 className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] mb-1">Problem & Impact</h4>
            <p className="text-slate-200 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
              {finding.problem}
            </p>
          </div>

          {/* Evidence Code */}
          {finding.evidence_code && (
            <div>
              <h4 className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] mb-1">Code Evidence</h4>
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-amber-300/90 overflow-x-auto text-[11px]">
                <div className="text-slate-500 text-[10px] mb-1 select-none">// Line {finding.line_number} in {finding.file_path}</div>
                <code>{finding.evidence_code}</code>
              </div>
            </div>
          )}

          {/* Recommended Fix */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Recommended Remediation</h4>
              <button
                onClick={handleCopyFix}
                className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy Fix"}</span>
              </button>
            </div>
            <div className="text-slate-200 leading-relaxed bg-blue-950/20 border border-blue-900/40 p-3 rounded-lg">
              {finding.recommendation}
            </div>
          </div>

          {/* AutoFix Loop Runner */}
          <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold text-slate-100">Automated Remediation Loop</span>
              </div>

              <button
                onClick={handleRunAutoFix}
                disabled={isAutoFixing}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-lg text-xs flex items-center gap-1.5 transition-colors"
              >
                {isAutoFixing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Validating Sandbox...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Run Auto-Fix Loop</span>
                  </>
                )}
              </button>
            </div>

            {autoFixResult && (
              <div className="space-y-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Pipeline Status:</span>
                  <span className="text-emerald-400 font-bold uppercase">{autoFixResult.status}</span>
                  <span className="text-slate-500 font-sans">({autoFixResult.iterations} iteration)</span>
                </div>

                <div className="bg-slate-900 p-2 rounded text-slate-300 space-y-1">
                  {autoFixResult.log.map((l, lIdx) => (
                    <div key={lIdx}>{l}</div>
                  ))}
                </div>

                {autoFixResult.diff_patch && (
                  <div>
                    <span className="text-slate-400 font-sans block mb-1">Generated Verified Unified Patch:</span>
                    <pre className="p-2 bg-slate-900 border border-slate-800 text-emerald-300 rounded overflow-x-auto">
                      {autoFixResult.diff_patch}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onOpenGitHubIssueModal(finding);
            }}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 transition-colors flex items-center gap-1.5"
          >
            <span>Create GitHub Issue</span>
          </button>
        </div>
      </div>
    </div>
  );
}
