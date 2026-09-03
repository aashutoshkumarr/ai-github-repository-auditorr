import sys
import httpx

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def verify():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)
    
    # 1. Healthcheck
    health = client.get("/health").json()
    print(f"[OK] Health Check: {health}")
    assert health["status"] == "ok"

    # 2. Samples
    samples = client.get("/api/samples").json()
    print(f"[OK] Samples Count: {len(samples)}")
    assert len(samples) >= 3

    # 3. Full Audit Pipeline on Vulnerable Repo
    payload = {"github_url": "https://github.com/sample/vulnerable-python-app", "llm_provider": "offline"}
    audit = client.post("/api/audit/analyze", json=payload).json()
    print(f"[OK] Audit Completed: ID={audit['id']}, Score={audit['overall_score']}/100, Findings={len(audit['findings'])}, Hotspots={len(audit['hotspots'])}, Deps={len(audit['dependencies'])}")
    assert audit["overall_score"] > 0
    assert len(audit["findings"]) > 0

    # 4. Codebase RAG Query
    rag_payload = {"report_id": audit["id"], "query": "Where is database connection or SQL query executed?"}
    rag = client.post("/api/rag/query", json=rag_payload).json()
    print(f"[OK] Codebase RAG Query: Answer length={len(rag['answer'])}, Citations={len(rag['citations'])}")
    assert len(rag["citations"]) > 0

    # 5. Agent Tool-Calling Chat
    agent_payload = {"report_id": audit["id"], "message": "Why is this repository difficult to maintain?", "llm_provider": "offline"}
    agent = client.post("/api/agent/chat", json=agent_payload).json()
    print(f"[OK] Agent Chat: Reply length={len(agent['reply'])}, Tool Steps executed={len(agent['tool_steps'])}")
    assert len(agent["tool_steps"]) > 0

    # 6. Auto-Fix Remediation Loop
    first_finding_id = audit["findings"][0]["id"]
    autofix = client.post(f"/api/github/autofix/{first_finding_id}").json()
    print(f"[OK] Auto-Fix Sandbox Loop: Status={autofix['status']}, Security Check Passed={autofix['security_check_passed']}")
    assert autofix["status"] == "verified"

    # 7. Benchmark Suite Execution
    bench = client.post("/api/benchmark/run", json={"suite_name": "Live Verification Suite"}).json()
    print(f"[OK] Benchmark Suite: Overall Precision={bench['overall_precision']}%, Recall={bench['overall_recall']}%, F1={bench['overall_f1']}%")
    assert bench["overall_precision"] >= 90.0

    print("\n[SUCCESS] ALL LIVE ENDPOINTS AND SERVICES VERIFIED 100% OPERATIONAL!")

if __name__ == "__main__":
    verify()
