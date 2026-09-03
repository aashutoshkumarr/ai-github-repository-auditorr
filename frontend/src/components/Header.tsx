"use client";

import Link from "next/link";
import { ShieldCheck, BarChart3, Github } from "lucide-react";
import { useEffect, useState } from "react";
import ThemeToggle from "@/components/ThemeToggle";
import { checkApiHealth } from "@/lib/api";

export default function Header() {
  const [apiOnline, setApiOnline] = useState<boolean>(true);

  useEffect(() => {
    checkApiHealth().then((online) => setApiOnline(online));
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-[var(--header-bg)] backdrop-blur-md">
      <div className="container max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-lg shadow-blue-500/25 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-sm sm:text-base tracking-tight text-[var(--page-fg)] flex items-center gap-1.5">
              AI GitHub Auditor <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-blue-500/20 text-blue-400 font-mono font-bold">v2.0</span>
            </span>
            <span className="text-[10px] text-[var(--muted-fg)] font-mono hidden sm:inline">
              Evidence-Backed Engineering Health & Security Platform
            </span>
          </div>
        </Link>

        {/* Navigation Actions */}
        <div className="flex items-center gap-3 sm:gap-5">
          {/* Live API Health indicator */}
          <div className="flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--muted-fg)]">
            <span className={`w-2 h-2 rounded-full ${apiOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-500"}`} />
            <span>{apiOnline ? "Engine Online" : "Engine Offline"}</span>
          </div>

          <ThemeToggle />

          <Link
            href="/benchmark"
            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-fg)] hover:text-[var(--page-fg)] px-3 py-1.5 rounded-lg hover:bg-[var(--card)] border border-transparent hover:border-[var(--border)] transition-all"
          >
            <BarChart3 className="w-4 h-4 text-purple-400" />
            <span>Benchmark Suite</span>
          </Link>

          <a
            href="https://github.com/aashutoshkumarr/ai-github-repository-auditorr"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-fg)] hover:text-[var(--page-fg)] px-3 py-1.5 rounded-lg bg-[var(--card)] hover:bg-[var(--card-hover)] border border-[var(--border)] transition-all"
          >
            <Github className="w-4 h-4 text-[var(--muted-fg)]" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </div>
    </header>
  );
}
