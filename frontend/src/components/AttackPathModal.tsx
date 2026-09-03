"use client";

import { useState, useEffect } from "react";
import { Finding, AttackPathResult } from "@/types";
import { fetchFindingAttackPath } from "@/lib/api";
import {
  ShieldAlert,
  ArrowRight,
  Terminal,
  RefreshCw,
  X,
  Wrench,
  AlertTriangle,
  Code2,
  Lock,
  Layers,
  Sparkles
} from "lucide-react";

interface AttackPathModalProps {
  finding: Finding | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenAutoFix?: (finding: Finding) => void;
}

export default function AttackPathModal({
  finding,
  isOpen,
  onClose,
  onOpenAutoFix,
}: AttackPathModalProps) {
  const [attackPath, setAttackPath] = useState<AttackPathResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && finding) {
      loadAttackPath();
    }
  }, [isOpen, finding]);

  const loadAttackPath = async () => {
    if (!finding) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchFindingAttackPath(finding.id);
      setAttackPath(data);
    } catch (err: any) {
      setError(err.message || "Failed to trace attack path.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !finding) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-rose-600/20 text-rose-400 border border-rose-500/30 shadow-lg">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400 font-mono">
                  Attack-Path & Risk Flow Tracing
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  {finding.severity}
                </span>
                {finding.cwe_id && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono">
                    {finding.cwe_id}
                  </span>
                )}
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

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800/80 p-4 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <RefreshCw className="w-8 h-8 mx-auto text-rose-400 animate-spin" />
              <p className="text-xs text-slate-400 font-mono">
                Tracing tainted data flow from entry points to sensitive execution sink...
              </p>
            </div>
          ) : attackPath ? (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Entry to Sink Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold block">
                    1. Entry Point (Untrusted Source)
                  </span>
                  <div className="text-xs font-semibold text-slate-200 font-mono">{attackPath.entry_point}</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-rose-500/30 space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold block">
                    2. Execution Sink (Vulnerable Target)
                  </span>
                  <div className="text-xs font-semibold text-rose-300 font-mono">{attackPath.sink_point}</div>
                </div>
              </div>

              {/* Tainted Data Progression Steps */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-rose-400" />
                  <span>Attack Path Node Progression</span>
                </h4>

                <div className="space-y-3 relative pl-6 border-l-2 border-slate-800 ml-3">
                  {attackPath.nodes.map((node, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border relative transition-all ${
                        node.is_source
                          ? "bg-rose-950/20 border-rose-500/40"
                          : node.is_sink
                          ? "bg-red-950/30 border-red-500/60"
                          : "bg-slate-950/60 border-slate-800"
                      }`}
                    >
                      <div className="absolute -left-[31px] top-4 w-4 h-4 rounded-full bg-slate-900 border-2 border-rose-500 flex items-center justify-center text-[9px] font-bold font-mono text-rose-300">
                        {node.step_number}
                      </div>

                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-xs font-bold text-slate-100 font-mono">
                          {node.layer} • <strong className="text-rose-300">{node.component_or_file}</strong>
                        </span>
                        {node.is_source && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 font-mono uppercase">
                            Untrusted Source
                          </span>
                        )}
                        {node.is_sink && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/30 text-red-300 font-mono uppercase animate-pulse">
                            Vulnerable Sink
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-300 font-mono bg-slate-900/60 p-2 rounded-lg border border-slate-800 mb-1.5">
                        {node.action_or_call}
                      </p>

                      <p className="text-[11px] text-slate-400">{node.risk_description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Remediation Advice */}
              <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/30 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
                  <Sparkles className="w-4 h-4" />
                  <span>Architectural Remediation Strategy</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{attackPath.remediation_summary}</p>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            Close
          </button>

          {onOpenAutoFix && finding && (
            <button
              onClick={() => {
                onClose();
                onOpenAutoFix(finding);
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-600/25 transition-all flex items-center gap-2"
            >
              <Wrench className="w-4 h-4" />
              <span>Launch Auto-Fix & Verify</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
