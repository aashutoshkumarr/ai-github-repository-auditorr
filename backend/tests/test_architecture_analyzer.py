import pytest
from backend.app.services.repo_fetcher import RepositoryContext, RepoFile, RepoFetcher
from backend.app.services.analyzers.architecture import ArchitectureAnalyzer
from backend.app.services.llm.provider import OfflineLLMProvider

def create_mock_repo(files_dict):
    ctx = RepositoryContext(url="https://github.com/test/repo", local_path="/mock", owner="test", name="repo")
    for path, content in files_dict.items():
        ext = "." + path.split(".")[-1] if "." in path else ""
        file = RepoFile(relative_path=path, absolute_path="/mock/" + path, size=len(content), extension=ext, content=content)
        ctx.files[path] = file
    return ctx

def test_pillar_1_detection():
    mock_files = {
        "Dockerfile": "FROM python:3.11\nWORKDIR /app",
        "docker-compose.yml": "version: '3.8'\nservices:\n  web:\n    build: .\n  redis:\n    image: redis\n  db:\n    image: postgres",
        ".github/workflows/ci.yml": "name: CI\non: [push]",
        "app/main.py": "from fastapi import FastAPI, APIRouter\nfrom app.api.routes import router\napp = FastAPI()",
        "app/api/routes.py": "from fastapi import APIRouter\nfrom app.services.user_service import UserService\nrouter = APIRouter()",
        "app/services/user_service.py": "from app.repositories.user_repo import UserRepo\nimport redis\nimport celery\nclass UserService:\n    pass",
        "app/repositories/user_repo.py": "import psycopg2\nclass UserRepo:\n    pass",
        "app/models/user.py": "from pydantic import BaseModel\nclass User(BaseModel):\n    id: str",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    # 1. Tech stack detection
    assert metrics["has_backend"] is True
    assert metrics["has_database"] is True
    assert metrics["has_cache"] is True
    assert metrics["has_queue"] is True
    assert metrics["has_docker"] is True
    assert metrics["has_ci"] is True
    assert "FastAPI" in metrics["tech_stack"]["backend"]
    assert "PostgreSQL" in metrics["tech_stack"]["database"]
    assert "Redis" in metrics["tech_stack"]["cache"]
    assert "Celery" in metrics["tech_stack"]["queues"]

    # 2. Checklist items
    checklist_categories = [item["category"] for item in metrics["tech_stack_checklist"] if item["detected"]]
    assert "Backend" in checklist_categories
    assert "Database" in checklist_categories
    assert "Cache" in checklist_categories
    assert "Docker / Containers" in checklist_categories
    assert "CI / CD Pipeline" in checklist_categories

def test_pillar_2_dependency_graph_and_cycles():
    # Construct a circular cycle: A -> B -> C -> A
    mock_files = {
        "app/services/service_a.py": "from app.services.service_b import ServiceB\nclass ServiceA: pass",
        "app/services/service_b.py": "from app.services.service_c import ServiceC\nclass ServiceB: pass",
        "app/services/service_c.py": "from app.services.service_a import ServiceA\nclass ServiceC: pass",
        "app/api/controller.py": "from app.services.service_a import ServiceA\nclass Controller: pass",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    dep_graph = metrics["dependency_graph"]
    assert dep_graph["total_modules"] >= 4
    assert dep_graph["circular_cycles_count"] >= 1
    
    # Verify circular dependency finding
    cycle_findings = [f for f in findings if f["rule_id"] == "ARCH-CIRCULAR-DEP"]
    assert len(cycle_findings) >= 1
    assert any("service_" in f["evidence_code"] for f in cycle_findings)

def test_pillar_3_pattern_classification():
    # Layered architecture test
    mock_files = {
        "src/controllers/auth_controller.py": "from src.services.auth_service import AuthService",
        "src/services/auth_service.py": "from src.repositories.auth_repo import AuthRepository",
        "src/repositories/auth_repo.py": "from src.models.user import UserModel\nimport psycopg2",
        "src/models/user.py": "class UserModel: pass",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    assert metrics["architecture_pattern"] == "Layered Architecture (N-Tier)"
    assert metrics["pattern_confidence"] >= 75
    assert "controllers" in metrics["detected_layers"]
    assert "services" in metrics["detected_layers"]
    assert "repositories" in metrics["detected_layers"]

def test_pillar_4_mermaid_diagram_generation():
    mock_files = {
        "main.py": "from fastapi import FastAPI\nimport redis\nimport psycopg2\napp = FastAPI()",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    assert mermaid.startswith("graph TD")
    assert "API_Layer" in mermaid
    assert "Infrastructure" in mermaid

@pytest.mark.asyncio
async def test_pillar_5_ai_explanation():
    mock_files = {
        "app/controllers/user_ctrl.py": "from app.services.user_svc import UserSvc",
        "app/services/user_svc.py": "from app.repositories.user_repo import UserRepo",
        "app/repositories/user_repo.py": "import psycopg2",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    llm = OfflineLLMProvider()
    explanation = await llm.generate_architecture_explanation({"owner": "org", "name": "app"}, metrics)

    assert "Architecture:" in explanation
    assert "Request Lifecycle" in explanation or "request" in explanation.lower()

def test_pillar_6_risks_and_strengths():
    # Clean repo with positive strengths
    mock_files = {
        "app/routes/item_routes.py": "from app.services.item_service import ItemService\nfrom fastapi import APIRouter",
        "app/services/item_service.py": "from app.repositories.item_repo import ItemRepo",
        "app/repositories/item_repo.py": "import psycopg2",
        "Dockerfile": "FROM python:3.11",
    }
    ctx = create_mock_repo(mock_files)
    score, findings, mermaid, metrics = ArchitectureAnalyzer.analyze(ctx)

    strengths = metrics["architecture_strengths"]
    strength_titles = [s["title"] for s in strengths]
    assert "Clear Separation of Concerns" in strength_titles
    assert "Database Isolated Behind Repository Layer" in strength_titles
    assert "Acyclic Dependency Flow" in strength_titles
    assert "Containerized Runtime Environment" in strength_titles
