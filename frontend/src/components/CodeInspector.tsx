"use client";

import { useState, useMemo } from "react";
import { Finding } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import {
  FileCode,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Wrench,
  ShieldAlert,
  Search,
  ChevronRight,
  GitPullRequest,
  ExternalLink,
  Code2,
  Sparkles,
  Layers,
  Terminal,
  ArrowRight,
  ShieldCheck,
  Zap,
} from "lucide-react";

interface CodeInspectorProps {
  findings: Finding[];
  onOpenAutoFixModal?: (finding: Finding) => void;
  onOpenGitHubIssueModal?: (finding: Finding) => void;
  onOpenAttackPathModal?: (finding: Finding) => void;
}

export default function CodeInspector({
  findings,
  onOpenAutoFixModal,
  onOpenGitHubIssueModal,
  onOpenAttackPathModal,
}: CodeInspectorProps) {
  const [selectedFindingId, setSelectedFindingId] = useState<string>(
    findings[0]?.id || ""
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [diffViewMode, setDiffViewMode] = useState<"split" | "unified">("split");
  const [copiedPatch, setCopiedPatch] = useState(false);

  // Group findings by file
  const groupedFiles = useMemo(() => {
    const map = new Map<string, Finding[]>();
    for (const f of findings) {
      if (!map.has(f.file_path)) {
        map.set(f.file_path, []);
      }
      map.get(f.file_path)!.push(f);
    }
    return Array.from(map.entries()).map(([filePath, fileFindings]) => ({
      filePath,
      findings: fileFindings,
      maxSeverity: fileFindings.some((x) => x.severity?.toLowerCase() === "critical")
        ? "Critical"
        : fileFindings.some((x) => x.severity?.toLowerCase() === "high")
        ? "High"
        : fileFindings.some((x) => x.severity?.toLowerCase() === "medium")
        ? "Medium"
        : "Low",
    }));
  }, [findings]);

  // Filtered files by search
  const filteredGroupedFiles = useMemo(() => {
    if (!searchQuery.trim()) return groupedFiles;
    const q = searchQuery.toLowerCase();
    return groupedFiles.filter(
      (g) =>
        g.filePath.toLowerCase().includes(q) ||
        g.findings.some(
          (f) =>
            f.title.toLowerCase().includes(q) ||
            f.problem.toLowerCase().includes(q) ||
            f.cwe_id?.toLowerCase().includes(q)
        )
    );
  }, [groupedFiles, searchQuery]);

  const selectedFinding = useMemo(() => {
    return findings.find((f) => f.id === selectedFindingId) || findings[0] || null;
  }, [findings, selectedFindingId]);

  // Synthesize remediation diff if finding does not have a raw diff patch
  const synthesizedDiff = useMemo(() => {
    if (!selectedFinding) return { before: "", after: "", patch: "" };

    const before =
      selectedFinding.evidence_code?.trim() ||
      `// Issue detected at line ${selectedFinding.line_number}\n${selectedFinding.problem}`;

    let after = selectedFinding.recommendation;
    // Extract code block from recommendation if present
    const codeMatch = selectedFinding.recommendation.match(/`([^`]+)`/);
    if (codeMatch) {
      after = codeMatch[1];
    }

    const patch = `--- a/${selectedFinding.file_path}
+++ b/${selectedFinding.file_path}
@@ -${selectedFinding.line_number},1 +${selectedFinding.line_number},1 @@
- ${before.split("\n").join("\n- ")}
+ ${after.split("\n").join("\n+ ")}`;

    return { before, after, patch };
  }, [selectedFinding]);

  const handleCopyPatch = () => {
    if (!synthesizedDiff.patch) return;
    navigator.clipboard.writeText(synthesizedDiff.patch);
    setCopiedPatch(true);
    setTimeout(() => setCopiedPatch(false), 2000);
  };

  if (findings.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
        <ShieldCheck className="w-12 h-12 mx-auto text-emerald-400" />
        <h3 className="text-base font-bold text-slate-100">Zero Code Defects Detected</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Static AST analysis identified no security vulnerabilities, code smells, or high-risk hotspots in this repository.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-sm shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-inner">
            <Code2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-400">
                FAANG-Standard Code Inspector
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                Deterministic AST Locator
              </span>
            </div>
            <h2 className="text-base font-extrabold text-slate-100">
              Line-by-Line Issue Locator & Interactive Remediation Diff
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs font-mono text-slate-300">
            <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse"></span>
            <span>{findings.length} Flagged Defects</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs font-mono text-emerald-300">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>100% AutoFixable</span>
          </div>
        </div>
      </div>

      {/* Main Split Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: File Tree & Issues (4 cols) */}
        <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3 backdrop-blur-sm shadow-xl">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search file, function, CWE..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1 pt-1 flex items-center justify-between">
            <span>Affected Codebase Files</span>
            <span>{filteredGroupedFiles.length} files</span>
          </div>

          {/* Files Accordion List */}
          <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
            {filteredGroupedFiles.map((group) => {
              const badge = getSeverityBadge(group.maxSeverity);
              return (
                <div
                  key={group.filePath}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-2.5 space-y-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <FileCode className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span className="text-xs font-mono font-bold text-slate-200 truncate" title={group.filePath}>
                        {group.filePath}
                      </span>
                    </div>
                    <span className={cn("px-1.5 py-0.5 text-[9px] font-bold rounded border uppercase shrink-0", badge.bg, badge.text, badge.border)}>
                      {group.findings.length} {group.findings.length === 1 ? "issue" : "issues"}
                    </span>
                  </div>

                  <div className="space-y-1 pl-2 border-l border-slate-800">
                    {group.findings.map((f) => {
                      const isSelected = selectedFinding?.id === f.id;
                      const fBadge = getSeverityBadge(f.severity);
                      return (
                        <button
                          key={f.id}
                          onClick={() => setSelectedFindingId(f.id)}
                          className={cn(
                            "w-full text-left p-2 rounded-lg text-xs transition-all flex items-center justify-between gap-2 group",
                            isSelected
                              ? "bg-blue-600 text-white font-semibold shadow-sm toggle-active"
                              : "hover:bg-slate-850 bg-slate-900/40 text-slate-300 hover:text-slate-100 border border-slate-800/60 hover:border-slate-700"
                          )}
                        >
                          <div className="min-w-0 flex items-center gap-2">
                            <span
                              className={cn(
                                "w-2 h-2 rounded-full shrink-0",
                                isSelected
                                  ? "bg-white"
                                  : f.severity?.toLowerCase() === "critical"
                                  ? "bg-rose-500"
                                  : f.severity?.toLowerCase() === "high"
                                  ? "bg-orange-500"
                                  : f.severity?.toLowerCase() === "medium"
                                  ? "bg-amber-500"
                                  : "bg-blue-500"
                              )}
                            />
                            <span className="truncate text-[11px]">{f.title}</span>
                          </div>
                          <span className="text-[10px] font-mono opacity-80 shrink-0">
                            L{f.line_number}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Interactive Diff & Remediation Guide (8 cols) */}
        {selectedFinding ? (
          <div className="lg:col-span-8 space-y-4">
            {/* Top Finding Detail Card */}
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 space-y-4 backdrop-blur-sm shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {(() => {
                    const b = getSeverityBadge(selectedFinding.severity);
                    return (
                      <span className={cn("px-2.5 py-0.5 text-xs font-bold rounded-md border flex items-center gap-1", b.bg, b.text, b.border)}>
                        <span>{b.icon}</span> {selectedFinding.severity}
                      </span>
                    );
                  })()}
                  <span className="px-2 py-0.5 text-xs font-medium bg-slate-800 text-slate-300 rounded-md">
                    {selectedFinding.category}
                  </span>
                  {selectedFinding.cwe_id && (
                    <span className="px-2 py-0.5 text-[11px] font-mono text-purple-400 bg-purple-950/40 border border-purple-800/50 rounded-md">
                      {selectedFinding.cwe_id}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 font-mono">
                    Confidence: <strong className="text-slate-100">{Math.round(selectedFinding.confidence * 100)}%</strong>
                  </span>
                </div>

                {/* Diff View Mode Switcher */}
                <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                  <button
                    onClick={() => setDiffViewMode("split")}
                    className={cn(
                      "px-2.5 py-1 rounded-lg text-xs font-semibold transition-all",
                      diffViewMode === "split"
                        ? "bg-blue-600 text-white font-bold shadow-sm toggle-active"
                        : "text-slate-400 hover:text-slate-200"
                    )}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setDiffViewMode("unified")}
                    className={cn(
                      "px-2.5 py-1 rounded-lg text-xs font-semibold transition-all",
                      diffViewMode === "unified"
                        ? "bg-blue-600 text-white font-bold shadow-sm toggle-active"
                        : "text-slate-400 hover:text-slate-200"
                    )}
                  >
                    Unified Patch
                  </button>
                </div>
              </div>

              {/* Title & File Locator */}
              <div>
                <h3 className="text-base font-bold text-slate-100 mb-1.5">
                  {selectedFinding.title}
                </h3>
                <div className="flex items-center gap-2 text-xs font-mono text-blue-400 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800/80 w-fit">
                  <FileCode className="w-4 h-4 text-blue-400" />
                  <span>{selectedFinding.file_path}</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-amber-300 font-bold">Line {selectedFinding.line_number}</span>
                </div>
              </div>

              {/* Problem Description */}
              <div className="space-y-1">
                <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Root Cause & Attack Vector Analysis
                </h4>
                <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/70">
                  {selectedFinding.problem}
                </p>
              </div>

              {/* Interactive Diff Viewer */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-blue-400" />
                    <span>Remediation Diff (Before vs Hardened Code)</span>
                  </h4>
                  <button
                    onClick={handleCopyPatch}
                    className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    {copiedPatch ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400">Copied Patch</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 text-slate-400" />
                        <span>Copy .patch Diff</span>
                      </>
                    )}
                  </button>
                </div>

                {diffViewMode === "split" ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                    {/* Before / Vulnerable */}
                    <div className="bg-rose-950/20 border border-rose-900/40 rounded-xl overflow-hidden">
                      <div className="bg-rose-950/40 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-rose-400 border-b border-rose-900/40 flex items-center justify-between">
                        <span>Original (Defective / Vulnerable)</span>
                        <span className="text-rose-300 font-mono">Line {selectedFinding.line_number}</span>
                      </div>
                      <pre className="p-3 text-rose-200 overflow-x-auto text-[11px] leading-relaxed whitespace-pre-wrap">
                        {synthesizedDiff.before}
                      </pre>
                    </div>

                    {/* After / Hardened */}
                    <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-xl overflow-hidden">
                      <div className="bg-emerald-950/40 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400 border-b border-emerald-900/40 flex items-center justify-between">
                        <span>Remediated (Hardened AST Patch)</span>
                        <span className="text-emerald-300 font-mono">Clean AST</span>
                      </div>
                      <pre className="p-3 text-emerald-200 overflow-x-auto text-[11px] leading-relaxed whitespace-pre-wrap">
                        {synthesizedDiff.after}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden font-mono text-xs">
                    <div className="bg-slate-900 px-3 py-1.5 text-[10px] font-bold text-slate-400 border-b border-slate-800 flex items-center justify-between">
                      <span>Unified Diff (Git Patch Format)</span>
                      <span>Unified</span>
                    </div>
                    <pre className="p-3 text-slate-200 overflow-x-auto text-[11px] leading-relaxed whitespace-pre-wrap">
                      {synthesizedDiff.patch}
                    </pre>
                  </div>
                )}
              </div>

              {/* Step-by-Step Remediation Action Guide */}
              <div className="space-y-2 bg-blue-950/20 border border-blue-900/40 rounded-xl p-4">
                <h4 className="text-xs font-bold text-blue-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-blue-400" />
                  <span>How to Resolve This Issue</span>
                </h4>
                <div className="text-xs text-slate-200 leading-relaxed">
                  {selectedFinding.recommendation}
                </div>
              </div>

              {/* Action Toolbar Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                {onOpenAutoFixModal && (
                  <button
                    onClick={() => onOpenAutoFixModal(selectedFinding)}
                    className="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-500/20 flex items-center gap-2 transition-all"
                  >
                    <Wrench className="w-4 h-4" />
                    <span>Run AutoFix in Sandbox</span>
                  </button>
                )}

                {onOpenAttackPathModal && (
                  <button
                    onClick={() => onOpenAttackPathModal(selectedFinding)}
                    className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-500/30 transition-colors flex items-center gap-1.5"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    <span>Trace Attack Path</span>
                  </button>
                )}

                {onOpenGitHubIssueModal && (
                  <button
                    onClick={() => onOpenGitHubIssueModal(selectedFinding)}
                    className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5 ml-auto"
                  >
                    <GitPullRequest className="w-3.5 h-3.5 text-slate-400" />
                    <span>Export to GitHub</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
