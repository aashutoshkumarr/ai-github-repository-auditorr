import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db
from backend.app.services.pr_analyzer import PRAnalyzer
from backend.app.architecture.drift import ArchitectureDriftDetector
from backend.app.architecture.model import (
    ArchitectureModel,
    ArchitecturePattern,
    Component,
    Dependency,
    ArchitectureRisk,
    LayerViolation,
)
from backend.app.services.attack_path_tracer import AttackPathTracer


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_pr_analyzer_vulnerable_diff():
    diff_with_sqli = """diff --git a/app/user_routes.py b/app/user_routes.py
--- a/app/user_routes.py
+++ b/app/user_routes.py
@@ -10,3 +10,6 @@
 def get_profile(user_input):
+    # Query DB dynamically
+    query = "SELECT * FROM profiles WHERE username = '%s'" % user_input
+    cursor.execute(query)
     return {"status": "ok"}
"""
    result = await PRAnalyzer.analyze_pr_diff(
        repo_url="https://github.com/sample/repo",
        diff_content=diff_with_sqli,
        pr_number=42,
    )

    assert result is not None
    assert result.pr_number == 42
    assert result.risk_level in ("Critical", "High")
    assert result.can_merge_safely is False
    assert len(result.security_delta_findings) >= 1
    assert any("SQL" in f.title for f in result.security_delta_findings)
    assert len(result.review_comments) >= 1
    assert any("SQL" in c.comment for c in result.review_comments)


@pytest.mark.asyncio
async def test_pr_analyzer_clean_diff_with_tests():
    clean_diff = """diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,4 +1,6 @@
 def calculate_metrics(values):
+    if not values:
+        return 0
     return sum(values) / len(values)
diff --git a/tests/test_service.py b/tests/test_service.py
--- a/tests/test_service.py
+++ b/tests/test_service.py
@@ -1,3 +1,5 @@
+def test_calculate_metrics():
+    assert calculate_metrics([10, 20]) == 15
"""
    result = await PRAnalyzer.analyze_pr_diff(
        repo_url="https://github.com/sample/repo",
        diff_content=clean_diff,
        pr_number=101,
    )

    assert result is not None
    assert result.risk_level in ("Low", "Medium")
    assert result.can_merge_safely is True
    assert len(result.security_delta_findings) == 0
    assert result.has_test_changes is True


def test_architecture_drift_detector():
    comp_a = Component(name="AuthController", type="controller", layer="presentation")
    comp_b = Component(name="UserService", type="service", layer="business")
    comp_c = Component(name="UserRepository", type="repository", layer="data_access")
    comp_redis = Component(name="RedisCache", type="cache", layer="persistence")

    # Base: AuthController -> UserService -> UserRepository
    base_model = ArchitectureModel(
        pattern=ArchitecturePattern(primary="Layered Architecture", confidence=0.9, description="Standard layers"),
        components=[comp_a, comp_b, comp_c],
        dependencies=[
            Dependency(source="AuthController", target="UserService"),
            Dependency(source="UserService", target="UserRepository"),
        ],
        risks=[],
        layer_violations=[],
        explanation="Standard 3-tier architecture.",
    )

    # Current: AuthController -> UserService -> UserRepository + RedisCache (and circular cycle)
    current_model = ArchitectureModel(
        pattern=ArchitecturePattern(primary="Layered Architecture with Cache", confidence=0.88, description="Added cache"),
        components=[comp_a, comp_b, comp_c, comp_redis],
        dependencies=[
            Dependency(source="AuthController", target="UserService"),
            Dependency(source="UserService", target="UserRepository"),
            Dependency(source="UserService", target="RedisCache"),
            Dependency(source="UserRepository", target="AuthController"),
        ],
        risks=[
            ArchitectureRisk(
                rule_id="ARCH-CYCLE",
                severity="High",
                type="Circular Dependency",
                title="UserRepository -> AuthController cycle",
                description="Circular dependency detected",
                mitigation="Decouple with events",
            )
        ],
        layer_violations=[],
        explanation="Evolved with Redis cache.",
    )

    drift = ArchitectureDriftDetector.compare_architecture(base_model, current_model)

    assert drift is not None
    assert drift.drift_detected is True
    assert "RedisCache" in drift.added_components
    assert len(drift.added_flows) >= 2
    assert drift.drift_severity in ("Medium", "High")
    assert "flowchart TD" in drift.drift_mermaid


def test_attack_path_tracer_sqli():
    path = AttackPathTracer.trace_attack_path(
        finding_id="find-sqli-1",
        title="SQL Injection in getUser",
        severity="Critical",
        file_path="app/db.py",
        line_number=18,
        cwe_id="CWE-89",
        evidence_code="cursor.execute('SELECT * FROM users WHERE name = ' + username)",
        rule_id="VULN-SQL-INJECTION",
    )

    assert path is not None
    assert path.finding_id == "find-sqli-1"
    assert len(path.nodes) >= 3
    assert path.nodes[0].is_source is True
    assert path.nodes[-1].is_sink is True
    assert "flowchart TD" in path.mermaid_flow
    assert "parameterized" in path.remediation_summary.lower()


@pytest.mark.asyncio
async def test_pr_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/pr/analyze",
            json={
                "repo_url": "https://github.com/sample/repo",
                "diff_content": "diff --git a/app/main.py b/app/main.py\n+api_key = 'sk-12345678901234567890'\n",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["risk_level"] in ("Critical", "High")
        assert len(data["review_comments"]) >= 1
