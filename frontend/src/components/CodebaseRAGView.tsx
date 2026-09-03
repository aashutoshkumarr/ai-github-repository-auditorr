"use client";

import { useState } from "react";
import { Search, Sparkles, FileCode, CheckCircle2, RefreshCw, HelpCircle, Code } from "lucide-react";
import { queryCodebaseRAG } from "@/lib/api";

interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
  relevance_score: number;
  symbol: string;
}

interface RAGResponse {
  query: string;
  answer: string;
  citations: Citation[];
}

interface CodebaseRAGViewProps {
  reportId: string;
}

export default function CodebaseRAGView({ reportId }: CodebaseRAGViewProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [ragResult, setRagResult] = useState<RAGResponse | null>(null);

  const presetQueries = [
    "Where is authentication implemented?",
    "Why does this service use Redis?",
    "Which files handle payments?",
    "Where are SQL database queries executed?"
  ];

  const handleRunRAG = async (queryText?: string) => {
    const textToRun = queryText || query;
    if (!textToRun.trim() || isLoading) return;

    setQuery(textToRun);
    setIsLoading(true);

    try {
      const data = await queryCodebaseRAG(reportId, textToRun);
      setRagResult(data);
    } catch (err) {
      console.error("RAG Query Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-slate-100">Codebase Semantic RAG & Evidence QA</h3>
            <p className="text-[11px] text-slate-400">
              Ask architectural and code location questions with verified file/line citations.
            </p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-purple-400 bg-purple-950/40 border border-purple-800/40 px-2.5 py-1 rounded-lg">
          BM25 + Semantic Vector Retrieval
        </span>
      </div>

      {/* Query Search Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleRunRAG();
        }}
        className="flex gap-2"
      >
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Where is authentication implemented? Or which files handle payments?"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-600/20 transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Retrieving...</span>
            </>
          ) : (
            <>
              <span>Query RAG</span>
            </>
          )}
        </button>
      </form>

      {/* Preset Queries */}
      <div className="flex items-center gap-2 flex-wrap text-xs">
        <span className="text-slate-500 text-[11px]">Suggested:</span>
        {presetQueries.map((pq, idx) => (
          <button
            key={idx}
            onClick={() => handleRunRAG(pq)}
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition-colors"
          >
            {pq}
          </button>
        ))}
      </div>

      {/* RAG Results Display */}
      {ragResult && (
        <div className="space-y-4 pt-2 border-t border-slate-800/80">
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Grounded Explanation</span>
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed">
              {ragResult.answer}
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Evidence Citations ({ragResult.citations.length})
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {ragResult.citations.map((c, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-2 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-blue-400 font-bold">
                      <FileCode className="w-3.5 h-3.5" />
                      <span className="truncate max-w-[200px]">{c.file_path}</span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-sans bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      Lines {c.start_line}–{c.end_line}
                    </span>
                  </div>

                  <pre className="bg-slate-900/90 border border-slate-800/60 p-2 rounded text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-32">
                    {c.snippet}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
