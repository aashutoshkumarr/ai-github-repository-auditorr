"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  ShieldCheck,
  GitPullRequest,
  Layers,
  Sparkles,
  Award,
  BarChart3,
  Bot,
  Flame,
  FileCode,
  X,
  Command
} from "lucide-react";

interface CommandPaletteProps {
  onOpenPRModal?: () => void;
  onOpenExecutiveModal?: () => void;
  onOpenAgentDrawer?: () => void;
  onSelectTab?: (tab: string) => void;
}

export default function CommandPalette({
  onOpenPRModal,
  onOpenExecutiveModal,
  onOpenAgentDrawer,
  onSelectTab,
}: CommandPaletteProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const commands = [
    {
      id: "findings",
      title: "View Vulnerability Findings",
      description: "Inspect security CWEs, code quality issues, and recommendations",
      icon: ShieldCheck,
      category: "Navigation",
      action: () => {
        onSelectTab?.("findings");
        setIsOpen(false);
      },
    },
    {
      id: "inspector",
      title: "Open Code Inspector & Diff Resolver",
      description: "Line-by-line file locator with side-by-side remediation patches",
      icon: FileCode,
      category: "Code Quality",
      action: () => {
        onSelectTab?.("inspector");
        setIsOpen(false);
      },
    },
    {
      id: "pr-review",
      title: "Launch PR Risk Analyzer & AI Review",
      description: "Evaluate pull request blast radius, security delta & AI fixes",
      icon: GitPullRequest,
      category: "DevSecOps",
      action: () => {
        setIsOpen(false);
        onOpenPRModal?.();
      },
    },
    {
      id: "executive-report",
      title: "Export Executive & OWASP Compliance Report",
      description: "Generate executive summary and standards scorecard",
      icon: Award,
      category: "Reports",
      action: () => {
        setIsOpen(false);
        onOpenExecutiveModal?.();
      },
    },
    {
      id: "architecture",
      title: "Inspect Architecture Topology & Drift",
      description: "Render Mermaid dependency graphs, layer violations, and drift",
      icon: Layers,
      category: "Architecture",
      action: () => {
        onSelectTab?.("arch");
        setIsOpen(false);
      },
    },
    {
      id: "hotspots",
      title: "View Team Churn & Bus Factor Hotspots",
      description: "Analyze Git commit velocity and developer ownership hotspots",
      icon: Flame,
      category: "Maintenance",
      action: () => {
        onSelectTab?.("hotspots");
        setIsOpen(false);
      },
    },
    {
      id: "agent-chat",
      title: "Ask Repository-Aware AI Agent",
      description: "Start interactive debugging session with agent tools",
      icon: Bot,
      category: "AI",
      action: () => {
        setIsOpen(false);
        onOpenAgentDrawer?.();
      },
    },
    {
      id: "benchmark",
      title: "Open Benchmark & Ground-Truth Matrix",
      description: "View empirical Precision, Recall, and F1 evaluation metrics",
      icon: BarChart3,
      category: "Evaluation",
      action: () => {
        setIsOpen(false);
        router.push("/benchmark");
      },
    },
  ];

  const filteredCommands = commands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase()) ||
    c.description.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Search Bar */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3 bg-slate-950/60">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search action (or press Esc)..."
            autoFocus
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <kbd className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-400 border border-slate-700">
            ESC
          </kbd>
        </div>

        {/* Action List */}
        <div className="p-2 max-h-80 overflow-y-auto divide-y divide-slate-800/40">
          {filteredCommands.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 font-mono">
              No matching actions found.
            </div>
          ) : (
            filteredCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={cmd.action}
                  className="w-full text-left p-3 rounded-xl hover:bg-slate-800/70 transition-colors flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-800 text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-200 group-hover:text-white">
                        {cmd.title}
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-1">
                        {cmd.description}
                      </p>
                    </div>
                  </div>

                  <span className="px-2 py-0.5 rounded text-[9px] font-mono text-slate-500 bg-slate-950 border border-slate-800">
                    {cmd.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>Tip: Press <kbd className="text-slate-400 font-bold">⌘K</kbd> / <kbd className="text-slate-400 font-bold">Ctrl+K</kbd> anywhere</span>
          <span>Fast Navigation</span>
        </div>
      </div>
    </div>
  );
}
