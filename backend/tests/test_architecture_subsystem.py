import pytest
from backend.app.services.repo_fetcher import RepositoryContext, RepoFile
from backend.app.architecture.scanner import FileStructureScanner
from backend.app.architecture.detector import TechnologyDetector, PatternDetector
from backend.app.architecture.graph import DependencyGraphBuilder
from backend.app.architecture.risk import ArchitectureRiskEngine
from backend.app.architecture.diagram import MermaidDiagramGenerator
from backend.app.architecture.service import ArchitectureService
from backend.app.architecture.model import ArchitectureModel

def create_mock_ctx(files: dict) -> RepositoryContext:
    ctx = RepositoryContext(url="https://github.com/org/ecommerce", local_path="/mock", owner="org", name="ecommerce")
    for path, content in files.items():
        ext = "." + path.split(".")[-1] if "." in path else ""
        ctx.files[path] = RepoFile(relative_path=path, absolute_path="/mock/" + path, size=len(content), extension=ext, content=content)
    return ctx

def test_file_structure_scanner():
    files = {
        "Dockerfile": "FROM node:18\nWORKDIR /app",
        "package.json": '{"name": "app", "dependencies": {"express": "^4.18.2"}}',
        "src/controllers/orderController.ts": "export class OrderController {}",
        "src/services/orderService.ts": "export class OrderService {}",
        "src/repositories/orderRepo.ts": "export class OrderRepo {}",
        "src/models/order.ts": "export interface Order {}",
        "src/tests/order.test.ts": "test('orders', () => {});",
        "src/index.ts": "import express from 'express';",
    }
    ctx = create_mock_ctx(files)
    scan = FileStructureScanner.scan(ctx)

    assert "src/index.ts" in scan["entry_points"]
    assert "package.json" in scan["manifests"]
    assert "Dockerfile" in scan["infra_files"]
    assert len(scan["directories"]["controllers"]) == 1
    assert len(scan["directories"]["services"]) == 1
    assert len(scan["directories"]["repositories"]) == 1
    assert len(scan["directories"]["tests"]) == 1

def test_evidence_backed_technology_detection():
    files = {
        "requirements.txt": "fastapi>=0.110.0\npsycopg2-binary>=2.9.9\nredis>=5.0.0\ncelery>=5.3.0",
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "app/routes/orders.py": "from fastapi import APIRouter\n@router.get('/orders')\ndef get_orders(): pass",
        "docker-compose.yml": "version: '3.8'\nservices:\n  db:\n    image: postgres:15",
    }
    ctx = create_mock_ctx(files)
    scan = FileStructureScanner.scan(ctx)
    techs = TechnologyDetector.detect_technologies(ctx, scan)

    tech_names = [t.technology for t in techs]
    assert "FastAPI" in tech_names
    assert "PostgreSQL" in tech_names
    assert "Redis" in tech_names
    assert "Celery" in tech_names
    assert "Docker Compose" in tech_names

    # Check evidence format
    fastapi_tech = next(t for t in techs if t.technology == "FastAPI")
    assert any("requirements.txt" in e for e in fastapi_tech.evidence)
    assert fastapi_tech.confidence >= 0.95

def test_pattern_detection_characteristics():
    files = {
        "src/controllers/auth.py": "from src.services.auth import AuthService",
        "src/services/auth.py": "from src.repositories.user import UserRepository",
        "src/repositories/user.py": "import psycopg2",
        "src/models/user.py": "class User: pass",
        "Dockerfile": "FROM python:3.11",
    }
    ctx = create_mock_ctx(files)
    scan = FileStructureScanner.scan(ctx)
    techs = TechnologyDetector.detect_technologies(ctx, scan)
    pattern = PatternDetector.detect_pattern(ctx, scan, techs)

    assert pattern.primary in {"Layered Architecture (N-Tier)", "Modular Monolith"}
    assert pattern.confidence >= 0.75
    assert len(pattern.characteristics) >= 1

def test_ast_dependency_graph_and_instability():
    files = {
        "app/controllers/user_ctrl.py": "from app.services.user_svc import UserSvc",
        "app/services/user_svc.py": "from app.repositories.user_repo import UserRepo",
        "app/repositories/user_repo.py": "from app.models.user import User",
        "app/models/user.py": "class User: pass",
    }
    ctx = create_mock_ctx(files)
    scan = FileStructureScanner.scan(ctx)
    components, deps, adj, rev_adj, meta = DependencyGraphBuilder.build_graph(ctx, scan)

    assert len(components) >= 3
    assert len(deps) >= 3
    # user_ctrl depends on user_svc -> out_degree > 0
    assert meta["app/controllers/user_ctrl.py"]["out_degree"] >= 1
    # user_repo has in_degree from user_svc
    assert meta["app/repositories/user_repo.py"]["in_degree"] >= 1

def test_risk_engine_layer_violation_and_blast_radius():
    # Construct a layer violation: Controller directly queries DB bypassing Service & Repo
    files = {
        "app/controllers/orders.py": "from app.models.order import OrderModel\ndef get_orders():\n    return db.execute('SELECT * FROM orders')",
        "app/models/order.py": "class OrderModel: pass",
        "app/services/payment.py": "from app.services.auth import AuthService",
        "app/services/auth.py": "class AuthService: pass",
        "app/controllers/payment_ctrl.py": "from app.services.payment import PaymentService",
        "tests/test_payment.py": "from app.services.payment import PaymentService",
    }
    ctx = create_mock_ctx(files)
    scan = FileStructureScanner.scan(ctx)
    components, deps, adj, rev_adj, meta = DependencyGraphBuilder.build_graph(ctx, scan)
    techs = TechnologyDetector.detect_technologies(ctx, scan)

    risks, violations, blast_radii, strengths = ArchitectureRiskEngine.analyze_risks(
        ctx, components, adj, rev_adj, meta, techs
    )

    # 1. Layer violation
    assert len(violations) >= 1
    assert violations[0].source_layer == "Controller / Presentation"

    # 2. Blast Radius on AuthService (imported by PaymentService, which is imported by PaymentCtrl and tests)
    auth_br = next((br for br in blast_radii if "auth.py" in br.target_module), None)
    if auth_br:
        assert len(auth_br.affected_modules) >= 1

@pytest.mark.asyncio
async def test_architecture_service_end_to_end():
    files = {
        "src/api/routes.ts": "import { UserService } from '../services/userService';",
        "src/services/userService.ts": "import { UserRepo } from '../repositories/userRepo';",
        "src/repositories/userRepo.ts": "export class UserRepo {}",
        "package.json": '{"dependencies": {"express": "^4.18.2", "pg": "^8.11.0"}}',
        "Dockerfile": "FROM node:18",
    }
    ctx = create_mock_ctx(files)
    model = await ArchitectureService.analyze(ctx, llm_provider="offline")

    assert isinstance(model, ArchitectureModel)
    assert model.pattern.primary != ""
    assert model.score > 70.0
    assert len(model.technologies) >= 1
    assert len(model.components) >= 2
    assert "graph TD" in model.diagram
    assert "Architecture:" in model.explanation
