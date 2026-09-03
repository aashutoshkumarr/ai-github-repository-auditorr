import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from backend.app.main import app
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.models.database_models import Repository, AuditReport, Finding
from backend.app.services.autofix_orchestrator import AutoFixOrchestrator
from backend.app.services.timeline_service import TimelineService


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest_asyncio.fixture
async def mock_vulnerable_report():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Create or fetch test repo
        stmt = select(Repository).where(Repository.url == "repo_vulnerable_python")
        res = await db.execute(stmt)
        repo = res.scalars().first()

        if not repo:
            repo = Repository(
                url="repo_vulnerable_python",
                owner="mock",
                name="vulnerable_python",
                default_branch="main",
                language="Python",
                is_sample=True,
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)

        # Create audit report
        report = AuditReport(
            repo_id=repo.id,
            status="completed",
            overall_score=45.0,
            security_score=30.0,
            quality_score=50.0,
            testing_score=40.0,
            docs_score=60.0,
            deps_score=50.0,
            arch_score=55.0,
            maintainability_score=45.0,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        # Add SQL injection finding
        finding = Finding(
            report_id=report.id,
            category="Security",
            severity="Critical",
            title="SQL Injection in delete_user",
            file_path="app/db.py",
            line_number=16,
            problem="Dynamic SQL query concatenation exposes the database to SQL injection.",
            recommendation="Use parameterized query placeholders instead of string formatting.",
            evidence_code='cursor.execute("DELETE FROM users WHERE id = %s" % user_id)',
            rule_id="VULN-SQL-INJECTION",
            confidence=0.95,
            cwe_id="CWE-89",
        )
        db.add(finding)
        await db.commit()
        await db.refresh(finding)

        return {"repo_id": repo.id, "report_id": report.id, "finding_id": finding.id}


@pytest.mark.asyncio
async def test_autofix_proposal_generation(mock_vulnerable_report):
    report_id = mock_vulnerable_report["report_id"]
    finding_id = mock_vulnerable_report["finding_id"]

    proposal = await AutoFixOrchestrator.generate_proposal(
        report_id=report_id,
        finding_id=finding_id,
        llm_provider="offline",
    )

    assert proposal is not None
    assert proposal.finding_id == finding_id
    assert proposal.status == "proposed"
    assert proposal.severity == "Critical"
    assert "query" in proposal.patched_code or "execute" in proposal.patched_code
    assert "diff" in proposal.diff_patch or "---" in proposal.diff_patch
    assert "SQL" in proposal.explanation or "parameterized" in proposal.explanation


@pytest.mark.asyncio
async def test_autofix_apply_and_verify_sandbox(mock_vulnerable_report):
    report_id = mock_vulnerable_report["report_id"]
    finding_id = mock_vulnerable_report["finding_id"]

    # 1. Generate proposal first
    proposal = await AutoFixOrchestrator.generate_proposal(
        report_id=report_id,
        finding_id=finding_id,
        llm_provider="offline",
    )

    # 2. Apply and verify in sandbox
    verify_res = await AutoFixOrchestrator.apply_and_verify(
        report_id=report_id,
        finding_id=finding_id,
        session_id=proposal.session_id,
        patched_code=proposal.patched_code,
        run_tests=True,
    )

    assert verify_res is not None
    assert verify_res.session_id == proposal.session_id
    assert verify_res.status == "verified"
    assert verify_res.security_check_passed is True
    assert verify_res.tests_passed is True
    assert verify_res.score_delta > 0
    assert verify_res.verified_score >= verify_res.initial_score
    assert "Sandbox" in verify_res.test_output or "Syntax" in verify_res.test_output


@pytest.mark.asyncio
async def test_autofix_create_pr_payload(mock_vulnerable_report):
    report_id = mock_vulnerable_report["report_id"]
    finding_id = mock_vulnerable_report["finding_id"]

    pr_res = await AutoFixOrchestrator.create_pull_request(
        report_id=report_id,
        finding_id=finding_id,
        branch_name="autofix/security-sql-fix",
        title="fix(security): sanitize user query against SQL injection",
    )

    assert pr_res is not None
    assert pr_res.status == "success"
    assert "autofix/security-sql-fix" in pr_res.branch_name
    assert "github.com" in pr_res.pr_url


@pytest.mark.asyncio
async def test_timeline_service_recording_and_trend(mock_vulnerable_report):
    repo_id = mock_vulnerable_report["repo_id"]
    report_id = mock_vulnerable_report["report_id"]

    # Record 1st snapshot
    snap1 = await TimelineService.record_snapshot(report_id, commit_sha="abc111", commit_message="Initial vulnerable commit")
    assert snap1 is not None
    assert snap1.overall_score == 45.0

    # Record 2nd snapshot (e.g. after fix, score rises to 85)
    async with AsyncSessionLocal() as db:
        report2 = AuditReport(
            repo_id=repo_id,
            status="completed",
            overall_score=85.0,
            security_score=90.0,
            quality_score=80.0,
            testing_score=85.0,
            docs_score=85.0,
            deps_score=80.0,
            arch_score=85.0,
            maintainability_score=80.0,
        )
        db.add(report2)
        await db.commit()
        await db.refresh(report2)
        report2_id = report2.id

    snap2 = await TimelineService.record_snapshot(report2_id, commit_sha="abc222", commit_message="Remediated SQL injection")
    assert snap2 is not None
    assert snap2.overall_score == 85.0

    # Query Timeline
    timeline = await TimelineService.get_timeline(repo_id)
    assert timeline is not None
    assert len(timeline.points) >= 2
    assert timeline.trend == "Improving"
    assert timeline.latest_score == 85.0
    assert timeline.score_delta > 0
    assert timeline.has_regression is False


@pytest.mark.asyncio
async def test_autofix_and_timeline_api_endpoints(mock_vulnerable_report):
    report_id = mock_vulnerable_report["report_id"]
    finding_id = mock_vulnerable_report["finding_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test AutoFix Generate Endpoint
        gen_res = await client.post(
            f"/api/audit/{report_id}/autofix/generate",
            json={"finding_id": finding_id, "llm_provider": "offline"},
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert gen_data["finding_id"] == finding_id
        session_id = gen_data["session_id"]

        # 2. Test AutoFix Verify Endpoint
        ver_res = await client.post(
            f"/api/audit/{report_id}/autofix/verify",
            json={
                "session_id": session_id,
                "finding_id": finding_id,
                "patched_code": gen_data["patched_code"],
                "run_tests": True,
            },
        )
        assert ver_res.status_code == 200
        ver_data = ver_res.json()
        assert ver_data["status"] == "verified"
        assert ver_data["score_delta"] > 0

        # 3. Test AutoFix Create PR Endpoint
        pr_res = await client.post(
            f"/api/audit/{report_id}/autofix/create-pr",
            json={
                "session_id": session_id,
                "finding_id": finding_id,
                "title": "fix(security): resolve SQL injection vulnerability",
            },
        )
        assert pr_res.status_code == 200
        pr_data = pr_res.json()
        assert pr_data["status"] == "success"

        # 4. Test Timeline Endpoint
        timeline_res = await client.get(f"/api/audit/{report_id}/timeline")
        assert timeline_res.status_code == 200
        timeline_data = timeline_res.json()
        assert len(timeline_data["points"]) >= 1
        assert "points" in timeline_data
