import re
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
from pathlib import Path
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.architecture.model import TechnologyEvidence, ArchitecturePattern

class TechnologyDetector:
    """
    Scans repository files and manifests for evidence-backed framework,
    database, cache, queue, cloud, and language detection.
    """

    @staticmethod
    def detect_technologies(ctx: RepositoryContext, scan_result: Dict[str, Any]) -> List[TechnologyEvidence]:
        evidences: Dict[str, Dict[str, Any]] = {}

        def record(tech: str, category: str, evidence_item: str, conf: float = 0.95):
            if tech not in evidences:
                evidences[tech] = {
                    "technology": tech,
                    "category": category,
                    "evidence": set(),
                    "confidence": conf
                }
            evidences[tech]["evidence"].add(evidence_item)
            evidences[tech]["confidence"] = max(evidences[tech]["confidence"], conf)

        paths = list(ctx.files.keys())
        
        # 1. Inspect manifests
        for manifest_path in scan_result.get("manifests", []):
            file = ctx.files.get(manifest_path)
            if not file:
                continue
            content = file.content.lower()

            # Python manifests
            if "requirements.txt" in manifest_path or "pyproject.toml" in manifest_path or "setup.py" in manifest_path:
                if "fastapi" in content:
                    record("FastAPI", "Backend Framework", f"{manifest_path}: fastapi dependency", 0.98)
                if "flask" in content:
                    record("Flask", "Backend Framework", f"{manifest_path}: flask dependency", 0.95)
                if "django" in content:
                    record("Django", "Backend Framework", f"{manifest_path}: django dependency", 0.98)
                if "sqlalchemy" in content:
                    record("SQLAlchemy", "ORM / Database Access", f"{manifest_path}: sqlalchemy dependency", 0.95)
                if "psycopg" in content or "psycopg2" in content or "asyncpg" in content:
                    record("PostgreSQL", "Database", f"{manifest_path}: PostgreSQL driver", 0.96)
                if "redis" in content or "aioredis" in content:
                    record("Redis", "Cache & Key-Value Store", f"{manifest_path}: redis client", 0.95)
                if "celery" in content:
                    record("Celery", "Queue / Worker", f"{manifest_path}: celery distributed tasks", 0.95)
                if "pydantic" in content:
                    record("Pydantic", "Data Validation", f"{manifest_path}: pydantic models", 0.95)

            # Node / JS / TS manifests
            if "package.json" in manifest_path:
                if "next" in content:
                    record("Next.js", "Fullstack / Frontend Framework", f"{manifest_path}: next dependency", 0.98)
                if "react" in content:
                    record("React", "Frontend UI Library", f"{manifest_path}: react dependency", 0.98)
                if "vue" in content:
                    record("Vue.js", "Frontend Framework", f"{manifest_path}: vue dependency", 0.98)
                if "express" in content:
                    record("Express.js", "Backend Framework", f"{manifest_path}: express dependency", 0.95)
                if "nestjs" in content or "@nestjs/core" in content:
                    record("NestJS", "Backend Framework", f"{manifest_path}: nestjs dependency", 0.98)
                if "tailwindcss" in content:
                    record("Tailwind CSS", "Styling Framework", f"{manifest_path}: tailwindcss dependency", 0.95)
                if "prisma" in content:
                    record("Prisma ORM", "ORM / Database Access", f"{manifest_path}: @prisma/client", 0.98)
                if "bull" in content or "bullmq" in content:
                    record("BullMQ", "Queue / Worker", f"{manifest_path}: bull/bullmq dependency", 0.95)

        # 2. Inspect source code contents
        for rel_path, file in ctx.files.items():
            content = file.content
            c_lower = content.lower()
            p_lower = rel_path.lower()

            # Infrastructure
            if "dockerfile" in p_lower:
                record("Docker", "Containerization", f"Dockerfile at `{rel_path}`", 0.98)
            if "docker-compose" in p_lower:
                record("Docker Compose", "Container Orchestration", f"Compose file at `{rel_path}`", 0.98)
                if "postgres" in c_lower:
                    record("PostgreSQL", "Database", f"{rel_path}: postgres container image", 0.95)
                if "redis" in c_lower:
                    record("Redis", "Cache & Key-Value Store", f"{rel_path}: redis container image", 0.95)
                if "rabbitmq" in c_lower:
                    record("RabbitMQ", "Message Broker", f"{rel_path}: rabbitmq container image", 0.95)

            if ".github/workflows" in p_lower:
                record("GitHub Actions", "CI / CD Pipeline", f"Workflow manifest at `{rel_path}`", 0.98)

            # Code-level evidence
            if "apirouter(" in c_lower or "@router." in c_lower:
                record("FastAPI", "Backend Framework", f"{rel_path}: APIRouter declaration", 0.95)
            if "@app.get" in c_lower or "@app.post" in c_lower:
                record("FastAPI", "Backend Framework", f"{rel_path}: FastAPI route decorator", 0.95)
            if "@controller(" in c_lower or "@injectable(" in c_lower:
                record("NestJS", "Backend Framework", f"{rel_path}: NestJS decorator", 0.96)
            if "useserver" in c_lower or "useclient" in c_lower:
                record("Next.js", "Fullstack / Frontend Framework", f"{rel_path}: React Server Components directive", 0.95)
            if "usestate(" in c_lower or "useeffect(" in c_lower:
                record("React", "Frontend UI Library", f"{rel_path}: React hooks", 0.90)

            # Cloud & External Services
            if "stripe" in c_lower:
                record("Stripe", "Payment Gateway", f"{rel_path}: Stripe SDK references", 0.90)
            if "sendgrid" in c_lower or "smtp" in c_lower:
                record("SendGrid / Email", "External Communication", f"{rel_path}: Email dispatch logic", 0.90)
            if "boto3" in c_lower or "aws_access_key" in c_lower:
                record("AWS Cloud Services", "Cloud Infrastructure", f"{rel_path}: AWS Boto3 SDK", 0.92)
            if "openai" in c_lower:
                record("OpenAI API", "AI & LLM Services", f"{rel_path}: OpenAI client", 0.92)
            if "google.generativeai" in c_lower or "gemini" in c_lower:
                record("Google Gemini AI", "AI & LLM Services", f"{rel_path}: Gemini SDK", 0.92)

        result = []
        for tech, data in sorted(evidences.items()):
            result.append(TechnologyEvidence(
                technology=data["technology"],
                category=data["category"],
                evidence=sorted(list(data["evidence"]))[:5],
                confidence=round(data["confidence"], 2)
            ))
        return result


class PatternDetector:
    """
    Classifies architectural archetype (Primary + Characteristics) based on
    directory hierarchy, layer separation, graph connectivity, and component presence.
    """

    @staticmethod
    def detect_pattern(
        ctx: RepositoryContext, scan_result: Dict[str, Any], technologies: List[TechnologyEvidence]
    ) -> ArchitecturePattern:
        dirs = scan_result.get("directories", {})
        dir_roots = scan_result.get("dir_roots", [])
        paths = list(ctx.files.keys())

        has_ctrl = len(dirs.get("controllers", [])) > 0
        has_svc = len(dirs.get("services", [])) > 0
        has_repo = len(dirs.get("repositories", [])) > 0
        has_model = len(dirs.get("models", [])) > 0
        has_ui = len(dirs.get("ui", [])) > 0
        has_worker = len(dirs.get("workers", [])) > 0
        has_queue = any(t.technology in {"Celery", "RabbitMQ", "Apache Kafka", "BullMQ"} for t in technologies)
        has_docker = any(t.technology in {"Docker", "Docker Compose"} for t in technologies)

        scores: Dict[str, float] = defaultdict(float)
        characteristics = []

        # Evaluate pattern candidates
        # 1. Microservices
        if any(p.startswith("services/") or p.startswith("microservices/") or p.startswith("apps/") for p in paths) and len(dir_roots) > 2:
            scores["Microservices"] += 60
            characteristics.append("Distributed Service Repositories")

        # 2. Serverless
        if any(k in "".join(paths).lower() for k in ["serverless.yml", "template.yaml", "sam.yaml", "sst.config", "netlify/functions"]):
            scores["Serverless Architecture"] += 70
            characteristics.append("Event-Driven Cloud Functions")

        # 3. Clean / Hexagonal
        if any("use_case" in p.lower() or "usecase" in p.lower() or "domain" in p.lower() or "adapter" in p.lower() or "port" in p.lower() for p in paths):
            scores["Clean / Hexagonal Architecture"] += 65
            characteristics.append("Domain-Centric Inward Dependency Rule")

        # 4. Layered Architecture (N-Tier)
        if has_ctrl and has_svc and has_repo:
            scores["Layered Architecture (N-Tier)"] += 75
            characteristics.append("3-Tier Layered Request Flow (Controller → Service → Repository)")
        elif has_ctrl and (has_svc or has_repo):
            scores["Layered Architecture (N-Tier)"] += 50
            characteristics.append("Controller-Service Separation")

        # 5. MVC
        if has_ctrl and has_model and any("view" in p.lower() or "templates" in p.lower() for p in paths):
            scores["Model-View-Controller (MVC)"] += 60
            characteristics.append("Model-View-Controller Abstraction")

        # 6. Event-Driven
        if has_queue or has_worker:
            scores["Event-Driven Architecture"] += 45
            characteristics.append("Asynchronous Worker Offloading")

        # 7. Frontend + Backend Multi-tier
        if has_ui and (has_ctrl or has_svc or "backend" in dir_roots):
            scores["Frontend + Backend Multi-Tier"] += 70
            characteristics.append("Decoupled Client & Server Applications")

        # 8. Data / ML Pipeline
        if any(p.endswith(".ipynb") for p in paths) or any("pipeline" in p.lower() or "train" in p.lower() for p in paths):
            scores["Data / ML Pipeline"] += 60
            characteristics.append("Sequential Data Ingestion & Transformation")

        # 9. CLI Tool
        if any(p in {"cli.py", "bin/cli.js", "cmd/main.go"} for p in paths) and len(paths) < 25:
            scores["Command Line Interface (CLI)"] += 65
            characteristics.append("Command Line Argument Dispatching")

        # Fallback: Modular Monolith
        scores["Modular Monolith"] += 50
        if has_svc or has_ctrl or has_model:
            scores["Modular Monolith"] += 25
            characteristics.append("Cohesive Domain Modules with Unified Storage")

        if has_repo:
            characteristics.append("Repository Pattern Data Isolation")
        if has_docker:
            characteristics.append("Containerized Runtime Environment")

        best_pattern = max(scores.items(), key=lambda x: x[1])[0]
        raw_score = scores[best_pattern]
        confidence = min(0.98, max(0.75, round((raw_score + 15) / 100, 2)))

        descriptions = {
            "Modular Monolith": "Structured monolithic codebase composed of cohesive domain modules, unified data models, and isolated business logic layers.",
            "Layered Architecture (N-Tier)": "Strict hierarchical separation of concerns where presentation controllers invoke business services, which delegate persistence to repositories.",
            "Clean / Hexagonal Architecture": "Domain-centric architecture isolating business entities and use cases from external frameworks and persistence adapters.",
            "Frontend + Backend Multi-Tier": "Decoupled full-stack architecture featuring a distinct client web interface communicating via REST/GraphQL with a backend API service.",
            "Microservices": "Distributed system partitioned into independently deployable domain services coordinated via API gateways and message buses.",
            "Event-Driven Architecture": "Asynchronous decoupling where producers publish domain events to message queues and specialized workers consume tasks.",
            "Model-View-Controller (MVC)": "Classic UI and server architecture separating application data models, templated views, and routing controllers.",
            "Serverless Architecture": "Stateless, event-triggered cloud functions executing on-demand without dedicated server process management.",
            "Data / ML Pipeline": "Sequential data transformation, feature engineering, model training, and analytical inference workflow.",
            "Command Line Interface (CLI)": "Terminal-driven utility structured around command parsing, argument validation, and standard I/O execution.",
        }

        # Deduplicate characteristics preserving order
        seen = set()
        dedup_chars = [c for c in characteristics if not (c in seen or seen.add(c))]

        return ArchitecturePattern(
            primary=best_pattern,
            confidence=confidence,
            description=descriptions.get(best_pattern, "Modular application architecture."),
            characteristics=dedup_chars[:6]
        )
