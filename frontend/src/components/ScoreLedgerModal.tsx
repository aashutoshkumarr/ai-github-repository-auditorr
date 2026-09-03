"use client";

import { X, Calculator, ShieldAlert, AlertTriangle, CheckCircle2, TrendingDown } from "lucide-react";
import { getSeverityBadge, cn } from "@/lib/utils";

interface ScoreLedgerModalProps {
  scoreLedger?: Record<string, any>;
  overallScore: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function ScoreLedgerModal({
  scoreLedger,
  overallScore,
  isOpen,
  onClose
}: ScoreLedgerModalProps) {
  if (!isOpen || !scoreLedger) return null;

  const categories = scoreLedger.categories || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <span>Score Transparency & Deduction Ledger</span>
              <span className="text-xs font-mono font-bold bg-blue-600 text-white px-2 py-0.5 rounded-md">
                {overallScore} / 100
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic, itemized mathematical breakdown explaining every point deduction.
            </p>
          </div>
        </div>

        {/* Formula Bar */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 mb-6 text-xs font-mono text-slate-300 overflow-x-auto">
          <div className="text-[10px] uppercase font-bold text-slate-500 font-sans mb-1">Scoring Formula</div>
          <code>Overall = 20%(Sec) + 20%(Qual) + 15%(Test) + 15%(Docs) + 10%(Deps) + 10%(Arch) + 10%(Maint)</code>
        </div>

        {/* Categories Itemized Deductions */}
        <div className="space-y-4">
          {Object.entries(categories).map(([catKey, catData]: [string, any]) => {
            const deductions = catData.itemized_deductions || [];

            return (
              <div
                key={catKey}
                className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-100 capitalize">{catKey}</span>
                    <span className="text-xs font-mono text-slate-400">(Weight: {catData.weight})</span>
                  </div>
                  <div className="text-xs font-bold text-slate-200">
                    Category Score: <span className={catData.score >= 80 ? "text-emerald-400" : (catData.score >= 60 ? "text-amber-400" : "text-rose-400")}>{catData.score}/100</span>
                  </div>
                </div>

                {deductions.length === 0 ? (
                  <div className="text-xs text-emerald-400/90 flex items-center gap-1.5 py-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Zero penalty deductions. Full 100 points awarded.</span>
                  </div>
                ) : (
                  <div className="space-y-1.5 font-mono text-xs">
                    {deductions.map((d: any, idx: number) => {
                      const badge = getSeverityBadge(d.severity);
                      return (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-900/80 border border-slate-800/60 hover:bg-slate-900 transition-colors"
                        >
                          <div className="flex items-center gap-2 max-w-[75%]">
                            <span className="text-rose-400 font-bold">{d.penalty} pts</span>
                            <span className={cn("px-1.5 py-0.2 text-[10px] font-bold rounded", badge.bg, badge.text)}>
                              {d.severity}
                            </span>
                            <span className="text-slate-200 truncate font-sans text-xs">{d.title}</span>
                          </div>

                          <div className="text-[11px] text-slate-500 truncate max-w-[20%] text-right font-sans">
                            {d.file_path ? `${d.file_path}:${d.line_number}` : d.rule_id}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex justify-end mt-6 pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Close Ledger
          </button>
        </div>
      </div>
    </div>
  );
}
