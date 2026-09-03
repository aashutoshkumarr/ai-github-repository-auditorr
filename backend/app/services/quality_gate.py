import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.database_models import AuditReport, Finding, Repository
from backend.app.models.schemas import (
    QualityGatePolicy,
    QualityGateRuleEvaluation,
    QualityGateResult,
)


class QualityGateEngine:
    """
    DevSecOps CI/CD Quality Gate Evaluation Engine.
    Evaluates repository audits against strict organizational standards before merge.
    """

    @classmethod
    async def evaluate(
        cls,
        report_id: str,
        policy: Optional[QualityGatePolicy] = None,
        db: Optional[AsyncSession] = None,
    ) -> QualityGateResult:
        if policy is None:
            policy = QualityGatePolicy()

        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            r_stmt = select(AuditReport).where(AuditReport.id == report_id)
            r_res = await db.execute(r_stmt)
            report = r_res.scalars().first()
            if not report:
                raise ValueError(f"Audit report '{report_id}' not found.")

            repo_stmt = select(Repository).where(Repository.id == report.repo_id)
            repo_res = await db.execute(repo_stmt)
            repo = repo_res.scalars().first()
            repo_name = repo.name if repo else "Repository"

            # Fetch findings for severity counts
            f_stmt = select(Finding).where(Finding.report_id == report_id)
            f_res = await db.execute(f_stmt)
            findings = f_res.scalars().all()

            crit_count = sum(1 for f in findings if f.severity.lower() == "critical")
            high_count = sum(1 for f in findings if f.severity.lower() == "high")

            # Parse metrics for architecture cycles / violations
            metrics: Dict[str, Any] = {}
            if report.metrics_json:
                try:
                    metrics = json.loads(report.metrics_json)
                except Exception:
                    metrics = {}

            cycles_count = len(metrics.get("circular_dependencies") or [])
            violations_count = len(metrics.get("layer_violations") or [])

            rules: List[QualityGateRuleEvaluation] = []

            # 1. Overall Score
            overall_pass = report.overall_score >= policy.min_overall_score
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Overall Repository Health",
                    category="Overall",
                    status="PASSED" if overall_pass else "FAILED",
                    expected=f"≥ {policy.min_overall_score}/100",
                    actual=f"{report.overall_score}/100",
                    passed=overall_pass,
                    reason=f"Overall score is {report.overall_score}/100." if overall_pass else f"Score {report.overall_score} fell below required {policy.min_overall_score}.",
                )
            )

            # 2. Security Score
            sec_pass = report.security_score >= policy.min_security_score
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Security Standard",
                    category="Security",
                    status="PASSED" if sec_pass else "FAILED",
                    expected=f"≥ {policy.min_security_score}/100",
                    actual=f"{report.security_score}/100",
                    passed=sec_pass,
                    reason=f"Security score is {report.security_score}/100." if sec_pass else f"Security score {report.security_score} fell below required {policy.min_security_score}.",
                )
            )

            # 3. Critical Vulnerabilities
            crit_pass = crit_count <= policy.max_critical_findings
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Critical Vulnerability Block",
                    category="Security",
                    status="PASSED" if crit_pass else "FAILED",
                    expected=f"≤ {policy.max_critical_findings} criticals",
                    actual=f"{crit_count} critical findings",
                    passed=crit_pass,
                    reason="No blocking critical vulnerabilities detected." if crit_pass else f"Detected {crit_count} critical vulnerabilities (Limit: {policy.max_critical_findings}).",
                )
            )

            # 4. High Vulnerabilities
            high_pass = high_count <= policy.max_high_findings
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="High Severity Vulnerabilities",
                    category="Security",
                    status="PASSED" if high_pass else "FAILED",
                    expected=f"≤ {policy.max_high_findings} high issues",
                    actual=f"{high_count} high findings",
                    passed=high_pass,
                    reason="High severity issue threshold met." if high_pass else f"Detected {high_count} high severity issues (Limit: {policy.max_high_findings}).",
                )
            )

            # 5. Code Quality
            qual_pass = report.quality_score >= policy.min_quality_score
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Code Quality & Maintainability",
                    category="Quality",
                    status="PASSED" if qual_pass else "FAILED",
                    expected=f"≥ {policy.min_quality_score}/100",
                    actual=f"{report.quality_score}/100",
                    passed=qual_pass,
                    reason=f"Code quality score is {report.quality_score}/100." if qual_pass else f"Code quality {report.quality_score} fell below {policy.min_quality_score}.",
                )
            )

            # 6. Testing Score
            test_pass = report.testing_score >= policy.min_testing_score
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Automated Test Suite Coverage",
                    category="Testing",
                    status="PASSED" if test_pass else "FAILED",
                    expected=f"≥ {policy.min_testing_score}/100",
                    actual=f"{report.testing_score}/100",
                    passed=test_pass,
                    reason=f"Testing score is {report.testing_score}/100." if test_pass else f"Testing score {report.testing_score} fell below {policy.min_testing_score}.",
                )
            )

            # 7. Dependency Risk
            deps_pass = report.deps_score >= policy.min_deps_score
            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Dependency Security & Freshness",
                    category="Dependencies",
                    status="PASSED" if deps_pass else "FAILED",
                    expected=f"≥ {policy.min_deps_score}/100",
                    actual=f"{report.deps_score}/100",
                    passed=deps_pass,
                    reason=f"Dependency health is {report.deps_score}/100." if deps_pass else f"Dependency health {report.deps_score} fell below {policy.min_deps_score}.",
                )
            )

            # 8. Architecture Integrity
            arch_pass = report.arch_score >= policy.min_arch_score
            if not policy.allow_circular_dependencies and cycles_count > 0:
                arch_pass = False
            if not policy.allow_architecture_violations and violations_count > 0:
                arch_pass = False

            rules.append(
                QualityGateRuleEvaluation(
                    rule_name="Architecture & Structural Integrity",
                    category="Architecture",
                    status="PASSED" if arch_pass else "FAILED",
                    expected=f"≥ {policy.min_arch_score}/100 & 0 cycles",
                    actual=f"{report.arch_score}/100 ({cycles_count} cycles, {violations_count} violations)",
                    passed=arch_pass,
                    reason="Architecture integrity passed without structural cycle violations." if arch_pass else f"Architecture failed: score {report.arch_score} / {cycles_count} cycles / {violations_count} layer violations.",
                )
            )

            passed_count = sum(1 for r in rules if r.passed)
            failed_count = len(rules) - passed_count
            can_merge = failed_count == 0
            gate_status = "PASSED" if can_merge else "FAILED"

            if can_merge:
                summary = f"Quality Gate PASSED. Repository '{repo_name}' satisfies all {len(rules)} organizational engineering standards. Merge permitted."
            else:
                failed_reasons = [r.reason for r in rules if not r.passed]
                summary = f"Quality Gate FAILED ({failed_count} violations). Merge blocked: {'; '.join(failed_reasons[:2])}"

            markdown_report = cls._generate_markdown_report(report, repo_name, gate_status, can_merge, rules)

            return QualityGateResult(
                report_id=report.id,
                repo_name=repo_name,
                status=gate_status,
                can_merge=can_merge,
                overall_score=report.overall_score,
                summary=summary,
                passed_rules_count=passed_count,
                failed_rules_count=failed_count,
                rules=rules,
                markdown_report=markdown_report,
            )
        finally:
            if should_close:
                await db.close()

    @classmethod
    def _generate_markdown_report(
        cls,
        report: AuditReport,
        repo_name: str,
        status: str,
        can_merge: bool,
        rules: List[QualityGateRuleEvaluation],
    ) -> str:
        icon = "✅" if can_merge else "❌"
        decision = "**MERGE PERMITTED**" if can_merge else "**MERGE BLOCKED**"

        md = f"""# {icon} DevSecOps Quality Gate: {status}

### Target: `{repo_name}` • Health Score: **{report.overall_score}/100** • Decision: {decision}

| Rule / Category | Status | Expected | Actual | Rationale |
|---|:---:|---|---|---|
"""
        for r in rules:
            s_badge = "✅ PASS" if r.passed else "❌ FAIL"
            md += f"| **{r.rule_name}** (`{r.category}`) | {s_badge} | `{r.expected}` | `{r.actual}` | {r.reason} |\n"

        md += "\n---\n*Enforced by AI GitHub Repository Auditor Quality Gate Engine • DevSecOps CI/CD Automation*"
        return md
