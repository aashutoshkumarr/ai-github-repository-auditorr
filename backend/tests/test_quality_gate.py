import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from backend.app.main import app
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.models.database_models import Repository, AuditReport, Finding
from backend.app.services.quality_gate import QualityGateEngine
from backend.app.models.schemas import QualityGatePolicy


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest_asyncio.fixture
async def sample_audit_reports():
    async with AsyncSessionLocal() as db:
        # 1. Clean repo
        stmt_clean = select(Repository).where(Repository.url == "repo_clean_test")
        res_clean = await db.execute(stmt_clean)
        clean_repo = res_clean.scalars().first()

        if not clean_repo:
            clean_repo = Repository(
                url="repo_clean_test",
                owner="sample",
                name="clean-repo",
                default_branch="main",
                language="TypeScript",
                is_sample=True,
            )
            db.add(clean_repo)
            await db.commit()
            await db.refresh(clean_repo)

        clean_report = AuditReport(
            repo_id=clean_repo.id,
            status="completed",
            overall_score=92.0,
            security_score=95.0,
            quality_score=90.0,
            testing_score=88.0,
            docs_score=90.0,
            deps_score=94.0,
            arch_score=92.0,
            maintainability_score=90.0,
        )
        db.add(clean_report)
        await db.commit()
        await db.refresh(clean_report)

        # 2. Vulnerable repo
        stmt_vuln = select(Repository).where(Repository.url == "repo_vuln_gate_test")
        res_vuln = await db.execute(stmt_vuln)
        vuln_repo = res_vuln.scalars().first()

        if not vuln_repo:
            vuln_repo = Repository(
                url="repo_vuln_gate_test",
                owner="sample",
                name="vuln-repo",
                default_branch="main",
                language="Python",
                is_sample=True,
            )
            db.add(vuln_repo)
            await db.commit()
            await db.refresh(vuln_repo)

        vuln_report = AuditReport(
            repo_id=vuln_repo.id,
            status="completed",
            overall_score=55.0,
            security_score=35.0,
            quality_score=60.0,
            testing_score=40.0,
            docs_score=65.0,
            deps_score=50.0,
            arch_score=60.0,
            maintainability_score=55.0,
        )
        db.add(vuln_report)
        await db.commit()
        await db.refresh(vuln_report)

        # Add critical finding
        f_crit = Finding(
            report_id=vuln_report.id,
            category="Security",
            severity="Critical",
            title="Remote Code Execution",
            file_path="app/server.py",
            line_number=12,
            problem="eval() allows arbitrary code execution",
            recommendation="Remove eval()",
            confidence=0.99,
        )
        db.add(f_crit)
        await db.commit()

        return {
            "clean_report_id": clean_report.id,
            "vuln_report_id": vuln_report.id,
        }


@pytest.mark.asyncio
async def test_quality_gate_clean_repo_passes(sample_audit_reports):
    report_id = sample_audit_reports["clean_report_id"]

    res = await QualityGateEngine.evaluate(report_id)

    assert res is not None
    assert res.status == "PASSED"
    assert res.can_merge is True
    assert res.failed_rules_count == 0
    assert res.overall_score == 92.0
    assert "MERGE PERMITTED" in res.markdown_report


@pytest.mark.asyncio
async def test_quality_gate_vulnerable_repo_blocks_merge(sample_audit_reports):
    report_id = sample_audit_reports["vuln_report_id"]

    res = await QualityGateEngine.evaluate(report_id)

    assert res is not None
    assert res.status == "FAILED"
    assert res.can_merge is False
    assert res.failed_rules_count >= 1
    assert "MERGE BLOCKED" in res.markdown_report
    assert any("Critical" in r.rule_name and not r.passed for r in res.rules)


@pytest.mark.asyncio
async def test_quality_gate_custom_policy(sample_audit_reports):
    report_id = sample_audit_reports["vuln_report_id"]

    # Highly lenient policy
    lenient_policy = QualityGatePolicy(
        min_overall_score=40.0,
        min_security_score=30.0,
        min_quality_score=30.0,
        min_testing_score=30.0,
        min_deps_score=30.0,
        min_arch_score=30.0,
        allow_critical_vulnerabilities=True,
        max_critical_findings=5,
        max_high_findings=10,
    )

    res = await QualityGateEngine.evaluate(report_id, policy=lenient_policy)

    assert res.status == "PASSED"
    assert res.can_merge is True


@pytest.mark.asyncio
async def test_quality_gate_api_endpoints(sample_audit_reports):
    clean_id = sample_audit_reports["clean_report_id"]
    vuln_id = sample_audit_reports["vuln_report_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET Quality Gate for clean repo
        res_clean = await client.get(f"/api/audit/{clean_id}/quality-gate")
        assert res_clean.status_code == 200
        data_clean = res_clean.json()
        assert data_clean["status"] == "PASSED"
        assert data_clean["can_merge"] is True

        # 2. POST Quality Gate evaluation for vulnerable repo
        res_vuln = await client.post(
            f"/api/audit/{vuln_id}/quality-gate/evaluate",
            json={"policy": {"min_overall_score": 80.0}},
        )
        assert res_vuln.status_code == 200
        data_vuln = res_vuln.json()
        assert data_vuln["status"] == "FAILED"
        assert data_vuln["can_merge"] is False
