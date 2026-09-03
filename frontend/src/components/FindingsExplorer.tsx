"use client";

import { useState } from "react";
import { Finding } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import { Search, Filter, AlertCircle, ArrowUpRight, Code, ShieldCheck, Wrench, ShieldAlert } from "lucide-react";

interface FindingsExplorerProps {
  findings: Finding[];
  onSelectFinding: (finding: Finding) => void;
  onOpenGitHubIssueModal: (finding: Finding) => void;
  onOpenAutoFixModal?: (finding: Finding) => void;
  onOpenAttackPathModal?: (finding: Finding) => void;
  selectedCategory?: string;
  onClearCategoryFilter?: () => void;
}

export default function FindingsExplorer({
  findings,
  onSelectFinding,
  onOpenGitHubIssueModal,
  onOpenAutoFixModal,
  onOpenAttackPathModal,
  selectedCategory,
  onClearCategoryFilter
}: FindingsExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  const filteredFindings = findings.filter((f) => {
    // Severity filter
    if (severityFilter !== "ALL" && f.severity?.toUpperCase() !== severityFilter) {
      return false;
    }
    // Category filter from top cards
    if (selectedCategory && f.category !== selectedCategory) {
      return false;
    }
    // Text search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        f.title.toLowerCase().includes(q) ||
        f.file_path.toLowerCase().includes(q) ||
        f.problem.toLowerCase().includes(q) ||
        f.category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/50 p-3 rounded-xl border border-slate-800/80">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search findings, files, CWEs..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => {
            const isActive = severityFilter === sev;
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={cn(
                  "px-3 py-1 text-xs font-semibold rounded-lg transition-all whitespace-nowrap",
                  isActive
                    ? "bg-blue-600 text-white font-bold border border-blue-500 shadow-sm toggle-active"
                    : "bg-slate-950/70 text-slate-400 border border-slate-800 hover:text-slate-100 hover:border-slate-700 hover:bg-slate-900"
                )}
              >
                {sev}
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Category Filter Tag */}
      {selectedCategory && (
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 w-fit">
          <span>Filtering by category: <strong className="text-blue-400">{selectedCategory}</strong></span>
          <button
            onClick={onClearCategoryFilter}
            className="text-slate-500 hover:text-slate-200 ml-2"
          >
            × Clear
          </button>
        </div>
      )}

      {/* Findings List */}
      <div className="space-y-3">
        {filteredFindings.length === 0 ? (
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-emerald-400/60" />
            No findings matching the selected filters.
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const badge = getSeverityBadge(finding.severity);

            return (
              <div
                key={finding.id}
                className="bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 rounded-xl p-4 transition-all duration-200 backdrop-blur-sm"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
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
                  </div>

                  <span className="text-xs text-slate-400 font-mono">
                    Confidence: <strong className="text-slate-200">{Math.round(finding.confidence * 100)}%</strong>
                  </span>
                </div>

                <h3 className="font-semibold text-slate-100 text-sm mb-1">{finding.title}</h3>
                
                <div className="flex items-center gap-2 text-xs font-mono text-blue-400 mb-2">
                  <Code className="w-3.5 h-3.5" />
                  <span>{finding.file_path}:{finding.line_number}</span>
                </div>

                <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                  {finding.problem}
                </p>

                {finding.evidence_code && (
                  <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-2.5 font-mono text-xs text-amber-300/90 mb-3 overflow-x-auto">
                    <code>{finding.evidence_code}</code>
                  </div>
                )}

                <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-800/60 flex-wrap">
                  <button
                    onClick={() => onSelectFinding(finding)}
                    className="text-xs font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                  >
                    <span>View Evidence & Remediation</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>

                  <div className="flex items-center gap-2 flex-wrap">
                    {onOpenAttackPathModal && (finding.category?.toLowerCase() === "security" || finding.cwe_id) && (
                      <button
                        onClick={() => onOpenAttackPathModal(finding)}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/30 flex items-center gap-1.5 transition-all shadow-sm"
                      >
                        <ShieldAlert className="w-3 h-3" />
                        <span>Attack Path</span>
                      </button>
                    )}

                    {onOpenAutoFixModal && (
                      <button
                        onClick={() => onOpenAutoFixModal(finding)}
                        className="px-2.5 py-1 text-xs font-bold rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 flex items-center gap-1.5 transition-all shadow-sm"
                      >
                        <Wrench className="w-3 h-3" />
                        <span>Auto-Fix</span>
                      </button>
                    )}

                    <button
                      onClick={() => onOpenGitHubIssueModal(finding)}
                      className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
                    >
                      <span>Create GitHub Issue</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
