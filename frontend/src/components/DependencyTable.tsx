"use client";

import { useState } from "react";
import { DependencyVulnerability } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import { PackageCheck, AlertTriangle, ArrowRight, ShieldCheck, Copy, Check, Terminal, Flame } from "lucide-react";

interface DependencyTableProps {
  dependencies: DependencyVulnerability[];
}

export default function DependencyTable({ dependencies }: DependencyTableProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCmd = (cmd: string, idx: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (!dependencies || dependencies.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 text-center text-xs text-slate-400">
        <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-emerald-400/80" />
        <p className="font-semibold text-slate-200">No vulnerable dependencies detected</p>
        <p className="text-slate-500 mt-1">All scanned packages meet minimum secure baseline versions.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
            <PackageCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-100">Dependency Intelligence & CVE Upgrades</h3>
            <p className="text-[11px] text-slate-400">
              Automated CVE matching, breaking change prediction, and remediation command generation.
            </p>
          </div>
        </div>

        <span className="text-xs text-rose-400 font-semibold bg-rose-950/40 border border-rose-900/50 px-2.5 py-1 rounded-lg">
          {dependencies.length} Packages At Risk
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
              <th className="py-2.5 px-3">Package</th>
              <th className="py-2.5 px-3">Version Upgrade</th>
              <th className="py-2.5 px-3">Vulnerability Advisory</th>
              <th className="py-2.5 px-3">Remediation Command</th>
              <th className="py-2.5 px-3 text-right">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {dependencies.map((dep, idx) => {
              const badge = getSeverityBadge(dep.severity);
              const upgradeCmd = dep.upgrade_command || `pip install ${dep.package_name}>=${dep.recommended_version}`;
              return (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-3">
                    <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                      <span>{dep.package_name}</span>
                      {dep.is_breaking_risk && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                          <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                          <span>Major Bump</span>
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-1.5 text-xs">
                      <span className="text-rose-400 font-bold">{dep.current_version}</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                      <span className="text-emerald-400 font-bold">{dep.recommended_version}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-300 max-w-xs">
                    <p className="line-clamp-2">{dep.advisory_title}</p>
                    {dep.cve_id && (
                      <span className="inline-block mt-1 px-1.5 py-0.5 text-[10px] font-mono text-purple-400 bg-purple-950/50 border border-purple-800/50 rounded">
                        {dep.cve_id}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800 px-2 py-1 rounded-lg">
                      <code className="text-[11px] text-blue-300 font-mono truncate max-w-[200px]">
                        {upgradeCmd}
                      </code>
                      <button
                        onClick={() => handleCopyCmd(upgradeCmd, idx)}
                        className="text-slate-400 hover:text-white p-0.5"
                        title="Copy command"
                      >
                        {copiedIndex === idx ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className={cn("px-2 py-0.5 text-[10px] font-bold rounded border inline-flex items-center gap-1", badge.bg, badge.text, badge.border)}>
                      <span>{badge.icon}</span> {dep.severity}
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
