from typing import List, Dict, Any, Optional
import re


class ConversationContext:
    def __init__(
        self,
        query: str,
        history: List[Dict[str, str]],
        repo_name: str,
        primary_language: str,
        file_count: int,
        health_score: float,
        previous_topic: Optional[str] = None,
        active_issue_num: Optional[int] = None,
        active_file: Optional[str] = None,
        has_baseline: bool = False
    ):
        self.query = query.strip()
        self.history = history or []
        self.repo_name = repo_name
        self.primary_language = primary_language
        self.file_count = file_count
        self.health_score = health_score
        self.previous_topic = previous_topic
        self.active_issue_num = active_issue_num
        self.active_file = active_file
        self.has_baseline = has_baseline


class ContextManager:
    """
    Maintains session history, sliding window conversation memory,
    topic tracking, and entity / pronoun reference resolution.
    """

    @classmethod
    def build_context(
        cls,
        query: str,
        history: Optional[List[Dict[str, str]]],
        ctx: Any,
        report: Any
    ) -> ConversationContext:
        history = history or []
        repo_name = ctx.repo_name if hasattr(ctx, "repo_name") else "repository"
        primary_language = ctx.primary_language if hasattr(ctx, "primary_language") else "Python"
        file_count = len(ctx.files) if hasattr(ctx, "files") else 0
        health_score = getattr(report, "overall_score", 45.0) if report else 45.0
        has_baseline = bool(getattr(report, "baseline_report_id", None))

        active_issue_num = None
        active_file = None
        previous_topic = None

        # Inspect history for context
        for turn in reversed(history[-8:]):
            content = turn.get("content", "").lower()

            if not previous_topic:
                if any(k in content for k in ["security", "sql", "secret", "vulnerability", "cwe", "cve"]):
                    previous_topic = "security"
                elif any(k in content for k in ["issue", "defect", "bug", "finding"]):
                    previous_topic = "issues"
                elif any(k in content for k in ["test", "pytest", "coverage"]):
                    previous_topic = "testing"
                elif any(k in content for k in ["file", "directory", "structure"]):
                    previous_topic = "files"

            if not active_issue_num:
                m = re.search(r"issue\s+#?([0-9]+)", content)
                if m:
                    active_issue_num = int(m.group(1))

            if not active_file:
                f_match = re.search(r"(?:app/[a-zA-Z0-9_\-]+\.py|requirements\.txt|models/[a-zA-Z0-9_\-]+\.py|README\.md)", content)
                if f_match:
                    active_file = f_match.group(0)

        return ConversationContext(
            query=query,
            history=history[-10:],
            repo_name=repo_name,
            primary_language=primary_language,
            file_count=file_count,
            health_score=health_score,
            previous_topic=previous_topic,
            active_issue_num=active_issue_num,
            active_file=active_file,
            has_baseline=has_baseline
        )
