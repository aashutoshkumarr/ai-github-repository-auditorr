import os
import re
from typing import Dict, Any, List, Optional
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.services.analyzers.code_quality import CodeQualityAnalyzer
from backend.app.services.analyzers.security_scanner import SecurityScanner
from backend.app.services.analyzers.dependency_scanner import DependencyScanner
from backend.app.services.analyzers.testing_analyzer import TestingAnalyzer

class AgentTools:
    @staticmethod
    def list_files(ctx: RepositoryContext, directory: str = "") -> str:
        """Lists files in the repository under an optional directory."""
        dir_clean = directory.strip("/").replace("\\", "/")
        matches = []
        for p in ctx.files.keys():
            if not dir_clean or p.startswith(dir_clean + "/") or p == dir_clean:
                matches.append(p)
        
        if not matches:
            return f"No files found under directory '{directory}'."
        return f"Files found ({len(matches)}):\n" + "\n".join(sorted(matches)[:40])

    @staticmethod
    def read_file(ctx: RepositoryContext, file_path: str, start_line: int = 1, end_line: int = 100) -> str:
        """Reads a section of a file with line numbers."""
        norm_path = file_path.strip().replace("\\", "/")
        file = ctx.files.get(norm_path)
        if not file:
            # Try fuzzy match
            for p, f in ctx.files.items():
                if norm_path in p:
                    file = f
                    norm_path = p
                    break
        
        if not file:
            return f"Error: File '{file_path}' not found in repository."

        lines = file.content.splitlines()
        start = max(1, start_line)
        end = min(len(lines), end_line)
        
        output = [f"--- File: {norm_path} (Lines {start}-{end}/{len(lines)}) ---"]
        for idx in range(start - 1, end):
            output.append(f"{idx + 1:4d} | {lines[idx]}")
        return "\n".join(output)

    @staticmethod
    def search_code(ctx: RepositoryContext, query: str) -> str:
        """Searches across all repository files for a keyword or regex pattern."""
        results = []
        for p, f in ctx.files.items():
            for idx, line in enumerate(f.content.splitlines(), start=1):
                if re.search(re.escape(query), line, re.IGNORECASE):
                    results.append(f"{p}:{idx} -> {line.strip()[:100]}")
                    if len(results) >= 15:
                        break
            if len(results) >= 15:
                break

        if not results:
            return f"No matches found for query: '{query}'"
        return f"Found {len(results)} matches for '{query}':\n" + "\n".join(results)

    @staticmethod
    def get_git_history(ctx: RepositoryContext, file_path: str = "") -> str:
        """Retrieves commit history and churn stats for the repository or a specific file."""
        if not ctx.git_commits:
            return "No Git commit history available (analyzed from direct source archive)."
        
        norm_path = file_path.strip().replace("\\", "/") if file_path else ""
        relevant_commits = []
        for c in ctx.git_commits:
            if not norm_path or norm_path in str(c.get("stats", {})):
                relevant_commits.append(f"[{c['hexsha']}] {c['date'][:10]} - {c['author']}: {c['message']}")
        
        if not relevant_commits:
            return f"No specific commits found touching '{file_path}'. Total repo commits: {len(ctx.git_commits)}."
        return "\n".join(relevant_commits[:10])

    @staticmethod
    def run_static_analysis(ctx: RepositoryContext, file_path: str = "") -> str:
        """Runs targeted AST and security inspection on a file or all files."""
        _, q_findings, _ = CodeQualityAnalyzer.analyze(ctx)
        _, s_findings, _ = SecurityScanner.analyze(ctx)
        
        all_findings = q_findings + s_findings
        if file_path:
            norm_path = file_path.strip().replace("\\", "/")
            all_findings = [f for f in all_findings if norm_path in f.get("file_path", "")]

        if not all_findings:
            return f"No static analysis issues detected for '{file_path or 'all files'}'."

        res = [f"Found {len(all_findings)} static analysis findings:"]
        for f in all_findings[:8]:
            res.append(f"[{f['severity']}] {f['category']} - {f['title']} in {f['file_path']}:{f['line_number']}")
        return "\n".join(res)

    @staticmethod
    def check_dependencies(ctx: RepositoryContext) -> str:
        """Checks dependency manifests and known CVE advisories."""
        _, _, vulns, metrics = DependencyScanner.analyze(ctx)
        if not vulns:
            return f"No vulnerable dependencies detected. Total dependencies scanned: {metrics.get('total_dependencies_detected', 0)}."
        
        res = [f"Found {len(vulns)} vulnerable dependencies:"]
        for v in vulns:
            res.append(f"• {v['package_name']} ({v['current_version']} -> recommend {v['recommended_version']}) - {v['advisory_title']} [{v['severity']}]")
        return "\n".join(res)

    @staticmethod
    def calculate_test_metrics(ctx: RepositoryContext) -> str:
        """Returns test suite volume, test-to-code ratio, and CI workflow status."""
        score, findings, metrics = TestingAnalyzer.analyze(ctx)
        return (
            f"Testing Score: {score}/100\n"
            f"Test Files: {metrics.get('test_files_count', 0)}\n"
            f"Test LOC: {metrics.get('test_loc', 0)} / Source LOC: {metrics.get('source_loc', 0)} (Ratio: {metrics.get('test_to_code_ratio_pct', 0)}%)\n"
            f"Frameworks Detected: {', '.join(metrics.get('detected_frameworks', [])) or 'None'}\n"
            f"CI Test Pipeline: {'Configured' if metrics.get('has_ci_test_workflow') else 'Missing'}"
        )

    @staticmethod
    def create_or_write_file(ctx: RepositoryContext, file_path: str, content: str) -> str:
        """Creates or writes a new file in the repository context."""
        import tempfile
        norm_path = file_path.strip().replace("\\", "/").lstrip("/")
        base_dir = ctx.local_path if ctx.local_path and os.path.exists(ctx.local_path) else os.path.join(tempfile.gettempdir(), "repo_sandbox")
        abs_path = os.path.join(base_dir, norm_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            # Update index
            from backend.app.services.repo_fetcher import RepoFile
            ext = os.path.splitext(norm_path)[1]
            ctx.files[norm_path] = RepoFile(norm_path, abs_path, len(content), ext, content=content)
            return f"Successfully created/updated '{norm_path}' ({len(content.splitlines())} lines)."
        except Exception as e:
            return f"Error writing file '{norm_path}': {str(e)}"

    @staticmethod
    def modify_file_snippet(ctx: RepositoryContext, file_path: str, old_snippet: str, new_snippet: str) -> str:
        """Modifies a file by replacing a specific snippet."""
        norm_path = file_path.strip().replace("\\", "/").lstrip("/")
        file = ctx.files.get(norm_path)
        if not file:
            for p, f in ctx.files.items():
                if norm_path in p:
                    file = f
                    norm_path = p
                    break
        if not file:
            return f"Error: Target file '{file_path}' not found in repository."

        content = file.content
        if old_snippet not in content:
            return f"Error: Target snippet not found in '{norm_path}'."

        new_content = content.replace(old_snippet, new_snippet, 1)
        return AgentTools.create_or_write_file(ctx, norm_path, new_content)
