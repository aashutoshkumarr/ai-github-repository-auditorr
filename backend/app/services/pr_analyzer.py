import re
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.app.models.schemas import (
    PRAnalysisRequest,
    PRReviewComment,
    PRRiskAnalysisResult,
    FindingResponse,
)
from backend.app.services.repo_fetcher import RepoFetcher, RepositoryContext
from backend.app.services.analyzers.security_scanner import SecurityScanner


class PRAnalyzer:
    """
    Evaluates Pull Requests / Git Diffs:
    - Blast radius of modified components
    - Security delta (vulnerabilities introduced in the PR)
    - Complexity delta
    - Test coverage delta
    - Risk classification (Low / Medium / High / Critical)
    - Automated line-by-line AI code review comments with suggested fixes
    """

    @classmethod
    async def analyze_pr_diff(
        cls,
        repo_url: str,
        diff_content: str,
        pr_number: Optional[int] = None,
        llm_provider: str = "offline",
        api_key: Optional[str] = None,
    ) -> PRRiskAnalysisResult:
        files_modified = cls._parse_diff_files(diff_content)
        lines_added = sum(f["lines_added"] for f in files_modified)
        lines_deleted = sum(f["lines_deleted"] for f in files_modified)

        # 1. Security Delta: Scan added lines for vulnerabilities
        sec_findings, review_comments = cls._scan_diff_security(files_modified)

        # 2. Test Delta: Check if test files were modified
        has_tests = any(
            "test" in f["file_path"].lower() or "spec" in f["file_path"].lower()
            for f in files_modified
        )
        test_coverage_delta = 10.0 if has_tests else (-15.0 if lines_added > 50 else 0.0)

        # 3. Complexity Delta
        complexity_delta = cls._calculate_complexity_delta(files_modified)

        # 4. Blast Radius Score
        # Core modules (auth, db, core, services, models) have higher impact
        blast_score = 0.0
        for f in files_modified:
            p = f["file_path"].lower()
            if any(k in p for k in ("db", "database", "auth", "security", "core", "models", "schema")):
                blast_score += 25.0
            elif any(k in p for k in ("service", "api", "routes", "controller")):
                blast_score += 15.0
            elif any(k in p for k in ("util", "helpers", "lib")):
                blast_score += 10.0
            else:
                blast_score += 5.0

        blast_radius_score = min(100.0, round(blast_score, 1))

        # 5. Risk Level Classification
        crit_count = sum(1 for f in sec_findings if f.severity.lower() == "critical")
        high_count = sum(1 for f in sec_findings if f.severity.lower() == "high")

        if crit_count > 0 or blast_radius_score > 70.0:
            risk_level = "Critical"
        elif high_count > 0 or blast_radius_score > 45.0 or (lines_added > 200 and not has_tests):
            risk_level = "High"
        elif lines_added > 50 or complexity_delta > 10.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        can_merge = risk_level in ("Low", "Medium") and crit_count == 0

        # Summary
        if can_merge:
            summary = (
                f"PR Risk: {risk_level}. {len(files_modified)} files changed (+{lines_added}/-{lines_deleted}). "
                f"Blast radius is contained ({blast_radius_score}/100) with no blocking security vulnerabilities."
            )
        else:
            summary = (
                f"PR Risk: {risk_level} (MERGE BLOCKED). Detected {len(sec_findings)} security issues and "
                f"a high blast radius ({blast_radius_score}/100). Remediation required before merging."
            )

        return PRRiskAnalysisResult(
            pr_number=pr_number,
            repo_url=repo_url,
            risk_level=risk_level,
            blast_radius_score=blast_radius_score,
            files_changed_count=len(files_modified),
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            security_delta_findings=sec_findings,
            complexity_delta=round(complexity_delta, 1),
            test_coverage_delta=round(test_coverage_delta, 1),
            has_test_changes=has_tests,
            summary=summary,
            review_comments=review_comments,
            can_merge_safely=can_merge,
        )

    @classmethod
    def _parse_diff_files(cls, diff_content: str) -> List[Dict[str, Any]]:
        files = []
        current_file = None
        added_lines = []
        lines_add_cnt = 0
        lines_del_cnt = 0

        for line in diff_content.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    files.append({
                        "file_path": current_file,
                        "added_lines": added_lines,
                        "lines_added": lines_add_cnt,
                        "lines_deleted": lines_del_cnt,
                    })
                parts = line.split(" ")
                current_file = parts[-1].lstrip("b/") if len(parts) >= 4 else "unknown"
                added_lines = []
                lines_add_cnt = 0
                lines_del_cnt = 0
            elif line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("+") and not line.startswith("+++"):
                lines_add_cnt += 1
                added_lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                lines_del_cnt += 1

        if current_file:
            files.append({
                "file_path": current_file,
                "added_lines": added_lines,
                "lines_added": lines_add_cnt,
                "lines_deleted": lines_del_cnt,
            })

        if not files and diff_content:
            # Single snippet fallback
            add_lines = [l[1:] for l in diff_content.splitlines() if l.startswith("+") and not l.startswith("+++")]
            files.append({
                "file_path": "app/diff_patch.py",
                "added_lines": add_lines,
                "lines_added": len(add_lines),
                "lines_deleted": sum(1 for l in diff_content.splitlines() if l.startswith("-") and not l.startswith("---")),
            })

        return files

    @classmethod
    def _scan_diff_security(cls, files: List[Dict[str, Any]]) -> (List[FindingResponse], List[PRReviewComment]):
        findings: List[FindingResponse] = []
        comments: List[PRReviewComment] = []

        for f in files:
            file_path = f["file_path"]
            added = f["added_lines"]

            for line_idx, line in enumerate(added, 1):
                # 1. SQL injection
                if re.search(r"(SELECT|INSERT|UPDATE|DELETE|FROM)\b.*(%s|%d|\s*%\s*\w+|\s*\+\s*\w+|\{.*\}).*", line, re.I) or re.search(r"execute\s*\(\s*([f\"'].*SELECT.*%|.*SELECT.*\+\s*\w+)", line, re.I):
                    findings.append(
                        FindingResponse(
                            id=f"pr-sec-{len(findings)+1}",
                            report_id="pr",
                            category="Security",
                            severity="Critical",
                            title="SQL Injection Introduced in PR",
                            file_path=file_path,
                            line_number=line_idx,
                            problem="PR introduces dynamic string concatenation in a SQL query.",
                            recommendation="Use parameterized SQL placeholders (:param or %s) to sanitize input.",
                            evidence_code=line.strip(),
                            confidence=0.95,
                            cwe_id="CWE-89",
                            rule_id="PR-VULN-SQLI",
                            status="open",
                        )
                    )
                    comments.append(
                        PRReviewComment(
                            file_path=file_path,
                            line_number=line_idx,
                            severity="Critical",
                            category="Security",
                            comment="⚠️ Potential SQL Injection (CWE-89): Avoid concatenating unvalidated variables directly into SQL queries.",
                            suggested_fix="cursor.execute('SELECT * FROM table WHERE id = %s', (user_id,))",
                        )
                    )

                # 2. Hardcoded secret / API key
                elif re.search(r"(api_key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", line, re.I):
                    findings.append(
                        FindingResponse(
                            id=f"pr-sec-{len(findings)+1}",
                            report_id="pr",
                            category="Security",
                            severity="Critical",
                            title="Hardcoded Credential in PR",
                            file_path=file_path,
                            line_number=line_idx,
                            problem="PR commits hardcoded secret or API key.",
                            recommendation="Extract secret into environment variable (os.getenv).",
                            evidence_code=line.strip()[:40] + "...",
                            confidence=0.98,
                            cwe_id="CWE-798",
                            rule_id="PR-VULN-SECRET",
                            status="open",
                        )
                    )
                    comments.append(
                        PRReviewComment(
                            file_path=file_path,
                            line_number=line_idx,
                            severity="Critical",
                            category="Security",
                            comment="🚨 Hardcoded Secret (CWE-798): Plaintext credential committed. Move this token to environment secrets.",
                            suggested_fix="api_key = os.getenv('API_KEY')",
                        )
                    )

                # 3. Arbitrary eval
                elif "eval(" in line and "literal_eval" not in line:
                    comments.append(
                        PRReviewComment(
                            file_path=file_path,
                            line_number=line_idx,
                            severity="High",
                            category="Security",
                            comment="⚠️ Insecure eval() execution (CWE-95): eval() can execute arbitrary remote code.",
                            suggested_fix="import ast; ast.literal_eval(payload)",
                        )
                    )

                # 4. Bare except clause
                elif re.match(r"^\s*except\s*:\s*$", line):
                    comments.append(
                        PRReviewComment(
                            file_path=file_path,
                            line_number=line_idx,
                            severity="Medium",
                            category="Quality",
                            comment="💡 Broad except clause suppresses system exit and unexpected exceptions.",
                            suggested_fix="except Exception as e:",
                        )
                    )

        return findings, comments

    @classmethod
    def _calculate_complexity_delta(cls, files: List[Dict[str, Any]]) -> float:
        complexity = 0.0
        for f in files:
            for line in f["added_lines"]:
                # Count branch keywords
                tokens = re.findall(r"\b(if|elif|else|for|while|try|except|switch|case|catch)\b", line)
                complexity += len(tokens) * 1.5
        return complexity
