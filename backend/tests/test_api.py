import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_health_and_samples():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # Samples list
        res_samples = await client.get("/api/samples")
        assert res_samples.status_code == 200
        samples = res_samples.json()
        assert len(samples) >= 3

@pytest.mark.asyncio
async def test_audit_workflow_and_agent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Run audit on sample vulnerable repo
        payload = {
            "github_url": "https://github.com/sample/vulnerable-python-app",
            "llm_provider": "offline"
        }
        res_audit = await client.post("/api/audit/analyze", json=payload)
        assert res_audit.status_code == 200
        report = res_audit.json()
        
        assert report["overall_score"] > 0
        assert len(report["findings"]) > 0
        assert len(report["dependencies"]) > 0
        assert "graph TD" in report["architecture_mermaid"]
        report_id = report["id"]

        # 2. Query report by ID
        res_get = await client.get(f"/api/audit/{report_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == report_id

        # 3. Test Agent tool chat
        agent_payload = {
            "report_id": report_id,
            "message": "Why is this repository difficult to maintain?",
            "llm_provider": "offline"
        }
        res_agent = await client.post("/api/agent/chat", json=agent_payload)
        assert res_agent.status_code == 200
        agent_resp = res_agent.json()
        assert "reply" in agent_resp
        assert len(agent_resp["tool_steps"]) > 0

        # 4. Test Benchmark Evaluation endpoint
        res_bench = await client.post("/api/benchmark/run", json={"suite_name": "Test Suite"})
        assert res_bench.status_code == 200
        bench_data = res_bench.json()
        assert bench_data["overall_precision"] >= 80.0
        assert bench_data["overall_recall"] >= 80.0
