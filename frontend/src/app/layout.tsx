import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "AI GitHub Repository Auditor | Enterprise Code Health & Security Platform",
  description: "Evidence-backed AI code reviewer, security scanner, and repository health analyzer combining static AST analysis, RAG, and agentic tool-calling.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-[var(--page-bg)] text-[var(--page-fg)] antialiased flex flex-col selection:bg-blue-500/30 selection:text-blue-200">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-[var(--border)] py-6 text-center text-xs text-[var(--muted-fg)]">
          <p>© 2026 AI GitHub Repository Auditor • Powered by Static AST Analysis + RAG + Multi-Provider LLMs</p>
        </footer>
      </body>
    </html>
  );
}
