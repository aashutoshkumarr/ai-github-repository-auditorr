"use client";

import { useState, useEffect } from "react";
import { Finding, AutoFixProposal, AutoFixVerificationResult, AutoFixPRResult } from "@/types";
import { generateAutoFixProposal, verifyAutoFix, createAutoFixPR } from "@/lib/api";
import {
  Wrench,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  GitPullRequest,
  RefreshCw,
  Terminal,
  ArrowRight,
  Code2,
  FileCode,
  Layers,
  TrendingUp,
  X,
  ExternalLink,
  Copy,
  Check
} from "lucide-react";

interface AutoFixModalProps {
  reportId: string;
  finding: Finding | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function AutoFixModal({
  reportId,
  finding,
  isOpen,
  onClose,
  onSuccess,
}: AutoFixModalProps) {
  const [step, setStep] = useState<"diagnose" | "verifying" | "verified" | "pr_ready">("diagnose");
  const [proposal, setProposal] = useState<AutoFixProposal | null>(null);
  const [verification, setVerification] = useState<AutoFixVerificationResult | null>(null);
  const [prResult, setPrResult] = useState<AutoFixPRResult | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Form states for PR
  const [branchName, setBranchName] = useState("");
  const [prTitle, setPrTitle] = useState("");
  const [githubToken, setGithubToken] = useState("");

  useEffect(() => {
    if (isOpen && finding) {
      setStep("diagnose");
      setProposal(null);
      setVerification(null);
      setPrResult(null);
      setError(null);
      setBranchName(`autofix/${finding.category.toLowerCase()}-${finding.id.slice(0, 8)}`);
      setPrTitle(`fix(${finding.category.toLowerCase()}): remediate ${finding.title}`);
      
      // Auto-fetch proposal
      handleLoadProposal();
    }
  }, [isOpen, finding]);

  const handleLoadProposal = async () => {
    if (!finding) return;
    setIsLoading(true);
    setError(null);
    try {
      const prop = await generateAutoFixProposal(reportId, finding.id);
      setProposal(prop);
    } catch (err: any) {
      setError(err.message || "Failed to generate auto-fix proposal.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveAndVerify = async () => {
    if (!finding || !proposal) return;
    setStep("verifying");
    setIsLoading(true);
    setError(null);
    try {
      const ver = await verifyAutoFix({
        report_id: reportId,
        finding_id: finding.id,
        session_id: proposal.session_id,
        patched_code: proposal.patched_code,
        run_tests: true,
      });
      setVerification(ver);
      setStep("verified");
    } catch (err: any) {
      setError(err.message || "Verification execution failed.");
      setStep("diagnose");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePR = async () => {
    if (!finding || !proposal) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await createAutoFixPR({
        report_id: reportId,
        finding_id: finding.id,
        session_id: proposal.session_id,
        github_token: githubToken || undefined,
        branch_name: branchName,
        title: prTitle,
      });
      setPrResult(res);
      setStep("pr_ready");
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to create GitHub Pull Request.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !finding) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-blue-400 font-mono">
                  Autonomous Auto-Fix & Verify
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  {finding.severity}
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                {finding.title}
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

        {/* Stepper Progress Bar */}
        <div className="bg-slate-950/90 border-b border-slate-800 px-6 py-3">
          <div className="flex items-center justify-between max-w-2xl mx-auto text-xs font-semibold font-mono">
            <div className={`flex items-center gap-2 ${step === "diagnose" ? "text-blue-400" : "text-emerald-400"}`}>
              <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px]">1</span>
              <span>Diagnose & Patch</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
            <div className={`flex items-center gap-2 ${step === "verifying" ? "text-amber-400 animate-pulse" : step === "verified" || step === "pr_ready" ? "text-emerald-400" : "text-slate-500"}`}>
              <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px]">2</span>
              <span>Sandbox Test & Re-Audit</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
            <div className={`flex items-center gap-2 ${step === "pr_ready" ? "text-emerald-400" : "text-slate-500"}`}>
              <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px]">3</span>
              <span>Create GitHub PR</span>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800/80 p-4 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: DIAGNOSE & DIFF PREVIEW */}
          {step === "diagnose" && (
            <div className="space-y-4">
              {isLoading ? (
                <div className="py-16 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 mx-auto text-blue-400 animate-spin" />
                  <p className="text-xs text-slate-400 font-mono">
                    Diagnosing root-cause AST pattern & generating syntax-safe code patch...
                  </p>
                </div>
              ) : proposal ? (
                <>
                  {/* Diagnosis Box */}
                  <div className="bg-blue-950/20 border border-blue-500/30 rounded-xl p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
                      <Sparkles className="w-4 h-4" />
                      <span>Remediation Rationale</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {proposal.explanation}
                    </p>
                    <div className="flex items-center gap-3 pt-2 text-[11px] text-slate-400 font-mono">
                      <span>Target: <strong className="text-slate-200">{proposal.file_path}:{proposal.line_number}</strong></span>
                      <span>Category: <strong className="text-blue-300">{proposal.category}</strong></span>
                    </div>
                  </div>

                  {/* Code Diff Preview */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1.5 font-semibold">
                        <FileCode className="w-4 h-4 text-purple-400" />
                        <span>Unified Remediation Diff Preview</span>
                      </span>
                      <span className="text-[11px] font-mono text-slate-500">Standard Git Patch Format</span>
                    </div>

                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs overflow-x-auto max-h-60 leading-relaxed">
                      {proposal.diff_patch ? (
                        proposal.diff_patch.split("\n").map((line, idx) => {
                          const isAdd = line.startsWith("+") && !line.startsWith("+++");
                          const isDel = line.startsWith("-") && !line.startsWith("---");
                          const isHunk = line.startsWith("@@");

                          return (
                            <div
                              key={idx}
                              className={`py-0.5 px-1 rounded ${
                                isAdd
                                  ? "bg-emerald-950/60 text-emerald-300 font-bold"
                                  : isDel
                                  ? "bg-rose-950/60 text-rose-300 font-bold line-through"
                                  : isHunk
                                  ? "text-blue-400"
                                  : "text-slate-400"
                              }`}
                            >
                              {line}
                            </div>
                          );
                        })
                      ) : (
                        <div className="space-y-2">
                          <div className="text-rose-400 line-through">- {finding.evidence_code}</div>
                          <div className="text-emerald-400">+ {proposal.patched_code}</div>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          )}

          {/* STEP 2 & 3: VERIFYING / VERIFIED CONSOLE */}
          {(step === "verifying" || step === "verified") && (
            <div className="space-y-4">
              {isLoading ? (
                <div className="py-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 mx-auto text-amber-400 animate-spin" />
                  <h3 className="font-bold text-sm text-slate-100">Executing Sandbox Validation</h3>
                  <p className="text-xs text-slate-400 font-mono">
                    Applying patch to isolated sandbox, running test runner, executing security re-scan...
                  </p>
                </div>
              ) : verification ? (
                <>
                  {/* Verification Outcome Summary Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className={`p-4 rounded-xl border ${verification.status === "verified" ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-300" : "bg-rose-950/20 border-rose-500/40 text-rose-300"}`}>
                      <div className="flex items-center justify-between text-xs">
                        <span>Verification Status</span>
                        {verification.status === "verified" ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-rose-400" />}
                      </div>
                      <div className="text-lg font-bold mt-1 uppercase font-mono">
                        {verification.status}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1">{verification.verification_reason}</p>
                    </div>

                    <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span>Test Suite Execution</span>
                        <ShieldCheck className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="text-lg font-bold mt-1 text-slate-100 font-mono">
                        {verification.tests_passed ? "0 Regressions" : "Tests Failed"}
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1">Syntax & unit test suite</p>
                    </div>

                    <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 text-blue-300">
                      <div className="flex items-center justify-between text-xs">
                        <span>Score Delta (Δ)</span>
                        <TrendingUp className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="text-lg font-bold mt-1 text-emerald-400 font-mono">
                        +{verification.score_delta}% Gain
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1">
                        {verification.initial_score} → <strong className="text-slate-100">{verification.verified_score}/100</strong>
                      </p>
                    </div>
                  </div>

                  {/* Terminal Log Console */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1.5 font-semibold font-mono">
                        <Terminal className="w-4 h-4 text-amber-400" />
                        <span>Sandbox Test & Re-Audit Terminal Log</span>
                      </span>
                    </div>

                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-52 whitespace-pre-wrap leading-relaxed">
                      {verification.test_output}
                    </div>
                  </div>

                  {/* PR Inputs */}
                  {verification.status === "verified" && (
                    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3">
                      <h4 className="font-bold text-xs text-slate-200 flex items-center gap-2">
                        <GitPullRequest className="w-4 h-4 text-blue-400" />
                        <span>Pull Request Configuration</span>
                      </h4>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div>
                          <label className="text-slate-400 text-[11px] block mb-1">Target Branch</label>
                          <input
                            type="text"
                            value={branchName}
                            onChange={(e) => setBranchName(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="text-slate-400 text-[11px] block mb-1">PR Title</label>
                          <input
                            type="text"
                            value={prTitle}
                            onChange={(e) => setPrTitle(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : null}
            </div>
          )}

          {/* STEP 4: PR READY */}
          {step === "pr_ready" && prResult && (
            <div className="py-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Pull Request Created Successfully!</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                The patch was committed with verified test provenance and before/after score metrics.
              </p>

              <div className="pt-2">
                <a
                  href={prResult.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-600/25 transition-all"
                >
                  <span>Open Pull Request on GitHub</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            {step === "pr_ready" ? "Close" : "Cancel"}
          </button>

          <div className="flex items-center gap-3">
            {step === "diagnose" && (
              <button
                onClick={handleApproveAndVerify}
                disabled={isLoading || !proposal}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-600/20 transition-all flex items-center gap-2"
              >
                {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                <span>Approve & Verify in Sandbox</span>
              </button>
            )}

            {step === "verified" && verification?.status === "verified" && (
              <button
                onClick={handleCreatePR}
                disabled={isLoading}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2"
              >
                {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <GitPullRequest className="w-4 h-4" />}
                <span>Create GitHub Pull Request</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
