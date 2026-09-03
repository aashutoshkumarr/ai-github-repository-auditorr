"use client";

import { HotspotMetric } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import { Flame, GitCommit, FileCode, AlertTriangle, Users, UserCheck } from "lucide-react";

interface HotspotHeatmapProps {
  hotspots: HotspotMetric[];
}

export default function HotspotHeatmap({ hotspots }: HotspotHeatmapProps) {
  if (!hotspots || hotspots.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 text-center text-xs text-slate-500">
        No high-risk hotspots detected in repository history.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/20">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-100">Team Churn, Complexity & Bus Factor Hotspots</h3>
            <p className="text-[11px] text-slate-400">
              Correlates modification frequency with cyclomatic complexity and author ownership concentration.
            </p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
          Risk = Churn × Complexity
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
              <th className="py-2.5 px-3">File Path</th>
              <th className="py-2.5 px-3">Commits</th>
              <th className="py-2.5 px-3">Ownership / Bus Factor</th>
              <th className="py-2.5 px-3">Complexity</th>
              <th className="py-2.5 px-3 text-right">Risk Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {hotspots.slice(0, 10).map((h, idx) => {
              const badge = getSeverityBadge(h.risk_level);
              return (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-3 text-slate-200">
                    <div className="flex items-center gap-2">
                      <FileCode className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span className="truncate max-w-xs">{h.file_path}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">
                    <span className="flex items-center gap-1">
                      <GitCommit className="w-3 h-3 text-slate-500" />
                      {h.commit_count}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-300 text-[11px] flex items-center gap-1 font-sans">
                        <Users className="w-3 h-3 text-slate-500" />
                        <span>{h.top_author || "lead-dev"}</span>
                      </span>
                      {h.is_bus_factor_risk && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
                          Bus Factor Risk
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {Math.round(h.complexity_score)}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={cn("px-2 py-0.5 text-[10px] font-bold rounded border inline-flex items-center gap-1", badge.bg, badge.text, badge.border)}>
                      <span>{badge.icon}</span> {h.risk_level}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
