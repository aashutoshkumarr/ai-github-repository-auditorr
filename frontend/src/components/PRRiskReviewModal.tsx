"use client";

import { useState } from "react";
import { PRRiskAnalysisResult, PRReviewComment } from "@/types";
import { analyzePRRisk } from "@/lib/api";
import {
  GitPullRequest,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Flame,
  Code2,
  FileCode,
  Copy,
  Check,
  RefreshCw,
  X,
  Layers,
  TrendingUp,
  Sparkles,
  ExternalLink
} from "lucide-react";

interface PRRiskReviewModalProps {
  repoUrl: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function PRRiskReviewModal({
  repoUrl,
  isOpen,
  onClose,
}: PRRiskReviewModalProps) {
  const [diffText, setDiffText] = useState<string>(`diff --git a/app/routes/auth.py b/app/routes/auth.py
--- a/app/routes/auth.py
+++ b/app/routes/auth.py
@@ -14,3 +14,6 @@
 def authenticate_user(user_input):
+    # Query database directly
+    cursor.execute("SELECT * FROM users WHERE username = '%s'" % user_input)
     return {"status": "authorized"}
`);
  const [prNumber, setPrNumber] = useState<number>(142);
  const [result, setResult] = useState<PRRiskAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleAnalyzePR = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyzePRRisk({
        repo_url: repoUrl,
        diff_content: diffText,
        pr_number: prNumber,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze PR risk.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyFix = (fix: string, idx: number) => {
    navigator.clipboard.writeText(fix);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30 shadow-lg">
              <GitPullRequest className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-purple-400 font-mono">
                  PR Risk Analyzer & AI Code Review
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                  PR #{prNumber}
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                Pull Request Blast Radius & Risk Classification
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800/80 p-4 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Diff Input Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold flex items-center gap-1.5">
                <Code2 className="w-4 h-4 text-blue-400" />
                <span>Pull Request Git Diff Content</span>
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    setDiffText(`diff --git a/app/routes/auth.py b/app/routes/auth.py
--- a/app/routes/auth.py
+++ b/app/routes/auth.py
@@ -14,3 +14,6 @@
 def authenticate_user(user_input):
+    # Query database directly
+    cursor.execute("SELECT * FROM users WHERE username = '%s'" % user_input)
     return {"status": "authorized"}
`)
                  }
                  className="text-[11px] text-blue-400 hover:underline"
                >
                  Load Vulnerable Diff
                </button>
                <span className="text-slate-600">•</span>
                <button
                  onClick={() =>
                    setDiffText(`diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,4 +1,6 @@
 def calculate_metrics(values):
+    if not values:
+        return 0
     return sum(values) / len(values)
diff --git a/tests/test_service.py b/tests/test_service.py
--- a/tests/test_service.py
+++ b/tests/test_service.py
@@ -1,3 +1,5 @@
+def test_calculate_metrics():
+    assert calculate_metrics([10, 20]) == 15
`)
                  }
                  className="text-[11px] text-emerald-400 hover:underline"
                >
                  Load Clean Diff
                </button>
              </div>
            </div>

            <textarea
              rows={5}
              value={diffText}
              onChange={(e) => setDiffText(e.target.value)}
              placeholder="Paste Git unified diff..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-purple-500 leading-relaxed"
            />
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleAnalyzePR}
              disabled={isLoading}
              className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-600/25 transition-all flex items-center gap-2"
            >
              {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>Execute PR Risk & AI Code Review</span>
            </button>
          </div>

          {/* Results Display */}
          {result && (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* Top Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                {/* Risk Level */}
                <div
                  className={`p-4 rounded-xl border ${
                    result.risk_level === "Critical"
                      ? "bg-rose-950/20 border-rose-500/40 text-rose-300"
                      : result.risk_level === "High"
                      ? "bg-amber-950/20 border-amber-500/40 text-amber-300"
                      : "bg-emerald-950/20 border-emerald-500/40 text-emerald-300"
                  }`}
                >
                  <span className="text-[11px] font-mono uppercase tracking-wider block">PR Risk Level</span>
                  <div className="text-xl font-bold font-mono mt-1">{result.risk_level}</div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {result.can_merge_safely ? "Merge Permitted" : "Merge Blocked"}
                  </p>
                </div>

                {/* Blast Radius Score */}
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                    Blast Radius
                  </span>
                  <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                    {result.blast_radius_score}/100
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">Downstream module impact</p>
                </div>

                {/* Security Delta */}
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                    Security Delta
                  </span>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      result.security_delta_findings.length > 0 ? "text-rose-400" : "text-emerald-400"
                    }`}
                  >
                    +{result.security_delta_findings.length} Issues
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">New vulnerabilities introduced</p>
                </div>

                {/* Test Coverage Delta */}
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                    Test Delta
                  </span>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      result.has_test_changes ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    {result.has_test_changes ? "+Tests Added" : "No Tests"}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">{result.files_changed_count} files changed</p>
                </div>
              </div>

              {/* Summary Banner */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                <strong className="text-slate-100 block mb-1">Executive Summary:</strong>
                {result.summary}
              </div>

              {/* AI Code Review Comments */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase font-mono text-purple-400 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  <span>Inline AI Code Review Comments ({result.review_comments.length})</span>
                </h4>

                {result.review_comments.length === 0 ? (
                  <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4 text-xs text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>0 code quality or security regressions found in this pull request.</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {result.review_comments.map((comment, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-950/90 border border-slate-800 rounded-xl p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
                              {comment.severity}
                            </span>
                            <span className="text-xs font-mono text-blue-400">
                              {comment.file_path}:{comment.line_number}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-slate-200">{comment.comment}</p>

                        {comment.suggested_fix && (
                          <div className="mt-2 bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs font-mono flex items-center justify-between text-emerald-300">
                            <code>{comment.suggested_fix}</code>
                            <button
                              onClick={() => handleCopyFix(comment.suggested_fix!, idx)}
                              className="text-slate-400 hover:text-white p-1"
                            >
                              {copiedIndex === idx ? (
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
