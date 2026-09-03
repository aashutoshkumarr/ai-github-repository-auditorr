import ast
import re
from collections import defaultdict, deque
from typing import List, Dict, Any, Tuple, Set, Optional
from pathlib import Path
from backend.app.services.repo_fetcher import RepositoryContext


class ArchitectureAnalyzer:
    """
    Enterprise-grade 7-pillar Architecture Analysis Engine:
    1. Tech Stack & Component Detection (Frontend/Backend, Frameworks, DBs, Caches, Queues, APIs, Entry Points, Modules, Docker/CI)
    2. AST & Static Import Dependency Graph (Layer mapping, In/Out degree, Instability, Circular cycles, Coupling, Isolated modules)
    3. Architecture Pattern Classification & Confidence Scoring (Modular Monolith, Layered, Clean/Hexagonal, MVC, Microservices, etc.)
    4. Dynamic Repo-Grounded Mermaid Flowchart Generation
    5. AI Architecture Explanation Context & Lifecycle Flow
    6. Architecture Risks (Circular deps, God modules, Layer violations, High coupling) & Positive Strengths Checklist
    7. Structured Dashboard Payload Generation
    """

    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], str, Dict[str, Any]]:
        """
        Analyzes architectural patterns, builds dependency graph, detects circular cycles & risks,
        determines architectural archetype with confidence, and generates dynamic Mermaid diagrams.
        Returns:
            (arch_score: float 0-100, findings: List[Dict], mermaid_diagram: str, metrics: Dict[str, Any])
        """
        paths = list(ctx.files.keys())
        
        # -------------------------------------------------------------
        # PILLAR 1: ARCHITECTURE DETECTION (Tech Stack, Components, Layers)
        # -------------------------------------------------------------
        tech_detection = ArchitectureAnalyzer._detect_tech_and_components(ctx)
        
        # -------------------------------------------------------------
        # PILLAR 2: DEPENDENCY & IMPORT GRAPH (AST / Regex Parsing)
        # -------------------------------------------------------------
        dep_graph_data = ArchitectureAnalyzer._build_dependency_graph(ctx)
        
        # -------------------------------------------------------------
        # PILLAR 3: ARCHITECTURE PATTERN DETECTION & CONFIDENCE
        # -------------------------------------------------------------
        pattern_name, confidence, pattern_desc = ArchitectureAnalyzer._classify_architecture_pattern(
            ctx, tech_detection, dep_graph_data
        )
        
        # -------------------------------------------------------------
        # PILLAR 4: DYNAMIC MERMAID DIAGRAM GENERATION
        # -------------------------------------------------------------
        mermaid_diagram = ArchitectureAnalyzer._generate_mermaid_diagram(
            pattern_name, tech_detection, dep_graph_data
        )
        
        # -------------------------------------------------------------
        # PILLAR 6: ARCHITECTURE RISKS & STRENGTHS
        # -------------------------------------------------------------
        arch_score, findings, risks, strengths, layer_violations, blast_radii = (
            ArchitectureAnalyzer._evaluate_risks_and_strengths(
                ctx, tech_detection, dep_graph_data, pattern_name
            )
        )
        
        # -------------------------------------------------------------
        # PILLAR 5 & 7: EXPLANATION DATA & DASHBOARD METRICS PAYLOAD
        # -------------------------------------------------------------
        layer_flow = ArchitectureAnalyzer._determine_layer_flow(tech_detection, dep_graph_data)
        
        explanation_summary = ArchitectureAnalyzer._generate_deterministic_explanation(
            pattern_name=pattern_name,
            confidence=confidence,
            pattern_desc=pattern_desc,
            tech_detection=tech_detection,
            layer_flow=layer_flow,
            risks=risks,
            strengths=strengths,
        )

        metrics: Dict[str, Any] = {
            # Top-level summary
            "archetype": pattern_name,
            "architecture_pattern": pattern_name,
            "pattern_confidence": confidence,
            "pattern_description": pattern_desc,
            "detected_technologies": tech_detection["all_technologies"],
            
            # Checklist flags
            "has_frontend": tech_detection["has_frontend"],
            "has_backend": tech_detection["has_backend"],
            "has_database": tech_detection["has_db"],
            "has_cache": tech_detection["has_cache"],
            "has_queue": tech_detection["has_queue"],
            "has_docker": tech_detection["has_docker"],
            "has_ci": tech_detection["has_ci"],
            "has_external_apis": len(tech_detection["external_services"]) > 0,
            
            # Structured tech stack
            "tech_stack": {
                "frontend": list(tech_detection["frontend_frameworks"]),
                "backend": list(tech_detection["backend_frameworks"]),
                "database": list(tech_detection["databases"]),
                "cache": list(tech_detection["caches"]),
                "queues": list(tech_detection["queues"]),
                "apis": list(tech_detection["api_protocols"]),
                "entry_points": tech_detection["entry_points"],
                "docker": list(tech_detection["docker_markers"]),
                "ci_cd": list(tech_detection["ci_markers"]),
                "external_services": list(tech_detection["external_services"]),
            },
            
            # Checklist for UI display
            "tech_stack_checklist": [
                {"category": "Frontend", "detected": tech_detection["has_frontend"], "name": ", ".join(tech_detection["frontend_frameworks"]) or ("Detected" if tech_detection["has_frontend"] else "None")},
                {"category": "Backend", "detected": tech_detection["has_backend"], "name": ", ".join(tech_detection["backend_frameworks"]) or ("Detected" if tech_detection["has_backend"] else "None")},
                {"category": "Database", "detected": tech_detection["has_db"], "name": ", ".join(tech_detection["databases"]) or ("Detected" if tech_detection["has_db"] else "None")},
                {"category": "Cache", "detected": tech_detection["has_cache"], "name": ", ".join(tech_detection["caches"]) or ("Detected" if tech_detection["has_cache"] else "None")},
                {"category": "Queue / Worker", "detected": tech_detection["has_queue"], "name": ", ".join(tech_detection["queues"]) or ("Detected" if tech_detection["has_queue"] else "None")},
                {"category": "Docker / Containers", "detected": tech_detection["has_docker"], "name": ", ".join(tech_detection["docker_markers"]) or ("Detected" if tech_detection["has_docker"] else "None")},
                {"category": "CI / CD Pipeline", "detected": tech_detection["has_ci"], "name": ", ".join(tech_detection["ci_markers"]) or ("Detected" if tech_detection["has_ci"] else "None")},
                {"category": "API Protocols", "detected": len(tech_detection["api_protocols"]) > 0, "name": ", ".join(tech_detection["api_protocols"]) or "REST"},
            ],

            # Layer & Flow
            "layer_flow": layer_flow,
            "detected_layers": {
                "controllers": list(dep_graph_data["layers"]["controllers"]),
                "services": list(dep_graph_data["layers"]["services"]),
                "repositories": list(dep_graph_data["layers"]["repositories"]),
                "models": list(dep_graph_data["layers"]["models"]),
                "middleware": list(dep_graph_data["layers"]["middleware"]),
                "workers": list(dep_graph_data["layers"]["workers"]),
            },
            
            # Dependency Graph Metrics
            "dependency_graph": {
                "total_modules": len(dep_graph_data["nodes"]),
                "total_dependencies": len(dep_graph_data["edges"]),
                "circular_cycles_count": len(dep_graph_data["circular_cycles"]),
                "circular_cycles": dep_graph_data["circular_cycles"],
                "tightly_coupled_modules": dep_graph_data["tightly_coupled"],
                "isolated_modules": dep_graph_data["isolated_modules"],
                "god_modules": dep_graph_data["god_modules"],
                "nodes": [
                    {
                        "id": node_id,
                        "label": info["label"],
                        "layer": info["layer"],
                        "in_degree": info["in_degree"],
                        "out_degree": info["out_degree"],
                        "instability": info["instability"],
                        "loc": info["loc"],
                        "is_god_module": node_id in dep_graph_data["god_modules"],
                        "is_isolated": node_id in dep_graph_data["isolated_modules"],
                    }
                    for node_id, info in sorted(dep_graph_data["nodes"].items(), key=lambda x: x[1]["in_degree"] + x[1]["out_degree"], reverse=True)[:30]
                ],
                "edges": [
                    {"source": src, "target": tgt}
                    for src, tgt in dep_graph_data["edges"][:50]
                ],
            },
            
            # Risks, Layer Violations & Blast Radius
            "architecture_risks": risks,
            "layer_violations": layer_violations,
            "blast_radius": blast_radii,
            "architecture_strengths": strengths,
            
            # AI Narrative
            "architecture_explanation": explanation_summary,
        }

        return round(arch_score, 1), findings, mermaid_diagram, metrics

    # =========================================================================
    # PILLAR 1: TECH STACK & COMPONENT DETECTION
    # =========================================================================
    @staticmethod
    def _detect_tech_and_components(ctx: RepositoryContext) -> Dict[str, Any]:
        paths = list(ctx.files.keys())
        dir_roots = set(p.split("/")[0] for p in paths if "/" in p)
        
        frontend_frameworks = set()
        backend_frameworks = set()
        databases = set()
        caches = set()
        queues = set()
        api_protocols = set()
        docker_markers = set()
        ci_markers = set()
        external_services = set()
        entry_points = []

        has_frontend = False
        has_backend = False
        has_docker = False
        has_ci = False
        has_db = False
        has_cache = False
        has_queue = False

        # Directory structure checks
        if any(r in {"frontend", "client", "web", "ui", "apps/web", "src/frontend"} for r in dir_roots):
            has_frontend = True
        if any(r in {"backend", "server", "api", "services", "apps/api", "src/backend"} for r in dir_roots):
            has_backend = True

        # Scan files for entry points
        entry_patterns = {
            "main.py", "app.py", "server.py", "wsgi.py", "asgi.py", "manage.py",
            "index.ts", "server.ts", "main.ts", "index.js", "app.js", "server.js",
            "cmd/main.go", "main.go", "src/main.rs", "Program.cs", "Startup.cs"
        }
        for p in paths:
            if p in entry_patterns or any(p.endswith(f"/{ep}") for ep in entry_patterns):
                entry_points.append(p)

        # Scan file contents & filenames
        for rel_path, file in ctx.files.items():
            content_lower = file.content.lower()
            rel_lower = rel_path.lower()
            
            # Docker & Containerization
            if "dockerfile" in rel_lower or "containerfile" in rel_lower:
                docker_markers.add("Dockerfile")
                has_docker = True
            if "docker-compose" in rel_lower or "compose.yaml" in rel_lower or "compose.yml" in rel_lower:
                docker_markers.add("Docker Compose")
                has_docker = True
            if "k8s" in rel_lower or "kubernetes" in rel_lower or "helm" in rel_lower:
                docker_markers.add("Kubernetes")

            # CI/CD
            if ".github/workflows" in rel_lower:
                ci_markers.add("GitHub Actions")
                has_ci = True
            if ".gitlab-ci.yml" in rel_lower:
                ci_markers.add("GitLab CI")
                has_ci = True
            if "jenkinsfile" in rel_lower:
                ci_markers.add("Jenkins")
                has_ci = True
            if ".circleci" in rel_lower:
                ci_markers.add("CircleCI")
                has_ci = True

            # Frontend Frameworks
            if "next" in content_lower and ("react" in content_lower or "next/router" in content_lower or "next/navigation" in content_lower):
                frontend_frameworks.add("Next.js")
                has_frontend = True
            elif "react" in content_lower and ("from 'react'" in content_lower or 'from "react"' in content_lower or "usestate" in content_lower):
                frontend_frameworks.add("React")
                has_frontend = True
            if "vue" in content_lower and ("createapp" in content_lower or "<template>" in content_lower):
                frontend_frameworks.add("Vue.js")
                has_frontend = True
            if "angular" in content_lower or "@angular" in content_lower:
                frontend_frameworks.add("Angular")
                has_frontend = True
            if "svelte" in content_lower or rel_lower.endswith(".svelte"):
                frontend_frameworks.add("Svelte")
                has_frontend = True
            if "tailwindcss" in content_lower or "tailwind.config" in rel_lower:
                frontend_frameworks.add("Tailwind CSS")

            # Backend Frameworks
            if "fastapi" in content_lower:
                backend_frameworks.add("FastAPI")
                has_backend = True
            if "flask" in content_lower and ("flask(" in content_lower or "blueprint(" in content_lower):
                backend_frameworks.add("Flask")
                has_backend = True
            if "django" in content_lower and ("django." in content_lower or "models.model" in content_lower):
                backend_frameworks.add("Django")
                has_backend = True
            if "express" in content_lower and ("express()" in content_lower or "express." in content_lower):
                backend_frameworks.add("Express.js")
                has_backend = True
            if "nestjs" in content_lower or "@nestjs" in content_lower:
                backend_frameworks.add("NestJS")
                has_backend = True
            if "spring" in content_lower and ("@springbootapplication" in content_lower or "@restcontroller" in content_lower):
                backend_frameworks.add("Spring Boot")
                has_backend = True
            if "gin-gonic" in content_lower or "gin.default()" in content_lower:
                backend_frameworks.add("Gin (Go)")
                has_backend = True
            if "fiber" in content_lower and "fiber.new()" in content_lower:
                backend_frameworks.add("Fiber (Go)")
                has_backend = True

            # Databases
            if any(k in content_lower for k in ["postgresql", "psycopg", "postgres", "pg_"]):
                databases.add("PostgreSQL")
                has_db = True
            if any(k in content_lower for k in ["mysql", "pymysql", "mysqlclient"]):
                databases.add("MySQL")
                has_db = True
            if any(k in content_lower for k in ["sqlite", "aiosqlite"]):
                databases.add("SQLite")
                has_db = True
            if any(k in content_lower for k in ["mongodb", "pymongo", "mongoose"]):
                databases.add("MongoDB")
                has_db = True
            if "prisma" in content_lower or "schema.prisma" in rel_lower:
                databases.add("Prisma ORM")
                has_db = True
            if "sqlalchemy" in content_lower:
                databases.add("SQLAlchemy")
                has_db = True
            if "alembic" in content_lower or "alembic.ini" in rel_lower:
                databases.add("Alembic Migrations")
                has_db = True

            # Caching
            if "redis" in content_lower or "aioredis" in content_lower:
                caches.add("Redis")
                has_cache = True
            if "memcached" in content_lower or "pylibmc" in content_lower:
                caches.add("Memcached")
                has_cache = True

            # Queues & Workers
            if "celery" in content_lower:
                queues.add("Celery")
                has_queue = True
            if "rabbitmq" in content_lower or "pika" in content_lower or "amqp" in content_lower:
                queues.add("RabbitMQ")
                has_queue = True
            if "kafka" in content_lower or "aiokafka" in content_lower:
                queues.add("Apache Kafka")
                has_queue = True
            if "bullmq" in content_lower or "bull" in content_lower:
                queues.add("BullMQ")
                has_queue = True
            if "sqs" in content_lower or "boto3" in content_lower and "sqs" in content_lower:
                queues.add("AWS SQS")
                has_queue = True

            # API Protocols
            if any(k in content_lower for k in ["apirouter", "fastapi", "router.get", "app.get", "@get(", "rest"]):
                api_protocols.add("REST API")
            if any(k in content_lower for k in ["graphql", "strawberry", "graphene", "apollo", "gql`"]):
                api_protocols.add("GraphQL")
            if "grpc" in content_lower or ".proto" in rel_lower:
                api_protocols.add("gRPC")
            if "trpc" in content_lower or "@trpc" in content_lower:
                api_protocols.add("tRPC")
            if "websocket" in content_lower or "socket.io" in content_lower or "ws://" in content_lower:
                api_protocols.add("WebSockets")

            # External Integrations
            if "stripe" in content_lower:
                external_services.add("Stripe Payments")
            if "sendgrid" in content_lower or "smtp" in content_lower:
                external_services.add("Email / SendGrid")
            if "s3" in content_lower or "aws_access_key" in content_lower:
                external_services.add("AWS Cloud Services")
            if "openai" in content_lower:
                external_services.add("OpenAI API")
            if "google.generativeai" in content_lower or "gemini" in content_lower:
                external_services.add("Google Gemini AI")
            if "sentry" in content_lower:
                external_services.add("Sentry Monitoring")

        all_tech = sorted(list(
            frontend_frameworks | backend_frameworks | databases | caches |
            queues | api_protocols | docker_markers | ci_markers | external_services
        ))

        return {
            "all_technologies": all_tech,
            "frontend_frameworks": frontend_frameworks,
            "backend_frameworks": backend_frameworks,
            "databases": databases,
            "caches": caches,
            "queues": queues,
            "api_protocols": api_protocols or {"REST API"},
            "docker_markers": docker_markers,
            "ci_markers": ci_markers,
            "external_services": external_services,
            "entry_points": entry_points,
            "has_frontend": has_frontend,
            "has_backend": has_backend,
            "has_db": has_db,
            "has_cache": has_cache,
            "has_queue": has_queue,
            "has_docker": has_docker,
            "has_ci": has_ci,
            "dir_roots": dir_roots,
        }

    # =========================================================================
    # PILLAR 2: AST & STATIC IMPORT DEPENDENCY GRAPH
    # =========================================================================
    @staticmethod
    def _build_dependency_graph(ctx: RepositoryContext) -> Dict[str, Any]:
        """
        Parses source files into modules and extracts static dependencies.
        Constructs an internal dependency graph, computes coupling metrics,
        and detects circular dependency cycles.
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Tuple[str, str]] = []
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

        layers = {
            "controllers": set(),
            "services": set(),
            "repositories": set(),
            "models": set(),
            "middleware": set(),
            "workers": set(),
            "utils": set(),
            "config": set(),
            "other": set(),
        }

        # Step A: Identify valid code modules
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cs", ".rb", ".php"}
        module_path_map: Dict[str, str] = {}  # alias -> canonical rel_path

        for rel_path, file in ctx.files.items():
            if file.extension in code_exts:
                norm_path = rel_path.replace("\\", "/")
                # Classify layer
                layer = ArchitectureAnalyzer._classify_file_layer(norm_path)
                layers[layer].add(norm_path)

                loc = len(file.content.splitlines())
                nodes[norm_path] = {
                    "id": norm_path,
                    "label": Path(norm_path).stem,
                    "layer": layer,
                    "loc": loc,
                    "in_degree": 0,
                    "out_degree": 0,
                    "instability": 0.0,
                }

                # Register path aliases for import resolution
                # e.g., 'backend/app/api/audit.py' -> 'backend.app.api.audit', 'api.audit', 'audit'
                stem = Path(norm_path).stem
                parts = norm_path.replace("/", ".").replace(file.extension, "").split(".")
                for i in range(len(parts)):
                    alias = ".".join(parts[i:])
                    module_path_map[alias] = norm_path
                    module_path_map[alias.replace(".", "/")] = norm_path
                module_path_map[norm_path] = norm_path
                module_path_map[norm_path.replace(file.extension, "")] = norm_path

        # Step B: Parse imports from files
        for rel_path, file in ctx.files.items():
            if rel_path not in nodes:
                continue
            
            imported_modules = ArchitectureAnalyzer._extract_imports_from_file(file.content, file.extension, rel_path)
            
            for imp in imported_modules:
                target_path = ArchitectureAnalyzer._resolve_import_to_module(imp, rel_path, module_path_map, nodes)
                if target_path and target_path != rel_path:
                    if target_path not in adjacency[rel_path]:
                        adjacency[rel_path].add(target_path)
                        reverse_adjacency[target_path].add(rel_path)
                        edges.append((rel_path, target_path))

        # Step C: Compute fan-in (in_degree), fan-out (out_degree), and instability
        for node_id, node_info in nodes.items():
            out_deg = len(adjacency[node_id])
            in_deg = len(reverse_adjacency[node_id])
            node_info["out_degree"] = out_deg
            node_info["in_degree"] = in_deg
            total_coupling = in_deg + out_deg
            node_info["instability"] = round(out_deg / total_coupling, 2) if total_coupling > 0 else 0.0

        # Step D: Detect Circular Dependencies (Cycle Detection via DFS)
        circular_cycles = ArchitectureAnalyzer._find_circular_dependency_cycles(adjacency)

        # Step E: Detect Tightly Coupled & Isolated & God Modules
        tightly_coupled = []
        for src, targets in adjacency.items():
            for tgt in targets:
                if src in adjacency[tgt] and src < tgt:  # Bidirectional coupling
                    tightly_coupled.append({
                        "module_a": src,
                        "module_b": tgt,
                        "type": "Bidirectional Coupling",
                        "description": f"Direct circular import between `{Path(src).name}` and `{Path(tgt).name}`",
                    })

        isolated_modules = [
            node_id for node_id, info in nodes.items()
            if info["in_degree"] == 0 and info["out_degree"] == 0
            and not any(ep in node_id for ep in ["main", "app", "index", "server", "test", "config", "manage"])
        ]

        god_modules = [
            node_id for node_id, info in nodes.items()
            if (info["out_degree"] >= 8 or info["in_degree"] >= 8 or info["loc"] >= 600)
            and info["layer"] in {"controllers", "services", "repositories", "models", "utils"}
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "adjacency": adjacency,
            "reverse_adjacency": reverse_adjacency,
            "layers": layers,
            "circular_cycles": circular_cycles,
            "tightly_coupled": tightly_coupled,
            "isolated_modules": isolated_modules,
            "god_modules": god_modules,
        }

    @staticmethod
    def _classify_file_layer(path: str) -> str:
        p_lower = path.lower()
        if any(k in p_lower for k in ["controller", "route", "router", "endpoint", "handler", "api/", "/api.", "/views"]):
            return "controllers"
        if any(k in p_lower for k in ["service", "use_case", "usecase", "domain", "manager", "interactor"]):
            return "services"
        if any(k in p_lower for k in ["repository", "repo", "dao", "data_access", "query", "queries"]):
            return "repositories"
        if any(k in p_lower for k in ["model", "schema", "entity", "entities", "dto", "types"]):
            return "models"
        if any(k in p_lower for k in ["middleware", "interceptor", "guard", "filter"]):
            return "middleware"
        if any(k in p_lower for k in ["worker", "job", "task", "queue", "consumer", "subscriber"]):
            return "workers"
        if any(k in p_lower for k in ["util", "helper", "common", "lib/"]):
            return "utils"
        if any(k in p_lower for k in ["config", "setting", "env"]):
            return "config"
        return "other"

    @staticmethod
    def _extract_imports_from_file(content: str, ext: str, file_path: str) -> List[str]:
        imports = []
        if ext == ".py":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        level = node.level  # relative import level
                        if level > 0:
                            # Resolve relative dot import base
                            curr_dir = "/".join(file_path.split("/")[:-1])
                            imports.append(f"RELATIVE:{level}:{curr_dir}:{module}")
                        else:
                            imports.append(module)
            except Exception:
                # Fallback to regex for malformed Python
                matches = re.findall(r"^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", content, re.MULTILINE)
                for m in matches:
                    imp = m[0] or m[1]
                    if imp:
                        imports.append(imp)
        elif ext in {".ts", ".tsx", ".js", ".jsx"}:
            # ES6 imports & requires
            es6_matches = re.findall(r"""(?:import|from|require)\s*\(?['"]([@\w\.\/\-\_]+)['"]\)? """, content)
            imports.extend(es6_matches)
        elif ext == ".go":
            go_matches = re.findall(r"""["']([a-zA-Z0-9_\-\.\/]+)["']""", content)
            imports.extend(go_matches)
        return imports

    @staticmethod
    def _resolve_import_to_module(
        imp: str, current_path: str, module_path_map: Dict[str, str], nodes: Dict[str, Any]
    ) -> Optional[str]:
        if imp.startswith("RELATIVE:"):
            parts = imp.split(":", 3)
            level = int(parts[1])
            curr_dir = parts[2]
            mod = parts[3]
            dir_parts = curr_dir.split("/") if curr_dir else []
            if level <= len(dir_parts):
                base_dir = "/".join(dir_parts[:len(dir_parts) - (level - 1)])
                target_cand = f"{base_dir}/{mod.replace('.', '/')}".strip("/")
                for ext in [".py", ".ts", ".js", ""]:
                    if target_cand + ext in nodes:
                        return target_cand + ext
                    if f"{target_cand}/__init__.py" in nodes:
                        return f"{target_cand}/__init__.py"
            return None

        # Absolute or alias match
        norm_imp = imp.replace(".", "/").strip("/")
        if imp in module_path_map:
            return module_path_map[imp]
        if norm_imp in module_path_map:
            return module_path_map[norm_imp]

        # Suffix matching
        for node_id in nodes:
            node_clean = node_id.rsplit(".", 1)[0]
            if node_clean.endswith(norm_imp) or node_clean.endswith(imp.replace(".", "/")):
                return node_id

        return None

    @staticmethod
    def _find_circular_dependency_cycles(adj: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """
        Finds simple directed circular dependency cycles using DFS cycle detection.
        Returns unique cycle paths like: module_a -> module_b -> module_a
        """
        cycles = []
        visited = set()
        rec_stack = []
        rec_set = set()

        def dfs(node: str):
            visited.add(node)
            rec_stack.append(node)
            rec_set.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_set:
                    # Found a cycle
                    cycle_start_idx = rec_stack.index(neighbor)
                    cycle_path = rec_stack[cycle_start_idx:] + [neighbor]
                    
                    # Normalize cycle path representation to avoid duplicate permutations
                    canon_cycle = cycle_path[:-1]
                    min_idx = canon_cycle.index(min(canon_cycle))
                    normalized = canon_cycle[min_idx:] + canon_cycle[:min_idx]
                    cycle_signature = " -> ".join(normalized)
                    
                    if not any(c["signature"] == cycle_signature for c in cycles) and len(canon_cycle) <= 6:
                        cycles.append({
                            "signature": cycle_signature,
                            "length": len(canon_cycle),
                            "path": [Path(p).name for p in cycle_path],
                            "full_path": cycle_path,
                            "display": " → ".join(Path(p).name for p in cycle_path),
                        })

            rec_set.remove(node)
            rec_stack.pop()

        for node in list(adj.keys()):
            if node not in visited:
                dfs(node)

        return cycles[:10]  # Return top 10 cycles

    # =========================================================================
    # PILLAR 3: ARCHITECTURE PATTERN DETECTION & CONFIDENCE
    # =========================================================================
    @staticmethod
    def _classify_architecture_pattern(
        ctx: RepositoryContext, tech: Dict[str, Any], dep_graph: Dict[str, Any]
    ) -> Tuple[str, int, str]:
        paths = list(ctx.files.keys())
        dir_roots = tech["dir_roots"]
        layers = dep_graph["layers"]
        
        has_controllers = len(layers["controllers"]) > 0
        has_services = len(layers["services"]) > 0
        has_repos = len(layers["repositories"]) > 0
        has_models = len(layers["models"]) > 0

        # Pattern evaluations & scores
        scores: Dict[str, float] = defaultdict(float)

        # 1. Microservices
        if any(p.startswith("services/") or p.startswith("microservices/") or p.startswith("apps/") for p in paths) and len(dir_roots) > 2:
            scores["Microservices"] += 50
        if "docker-compose" in str(tech["docker_markers"]).lower() and len([p for p in paths if "dockerfile" in p.lower()]) >= 2:
            scores["Microservices"] += 40

        # 2. Serverless Architecture
        if any(k in "".join(paths).lower() for k in ["serverless.yml", "template.yaml", "sam.yaml", "sst.config", "netlify/functions", "api/lambda"]):
            scores["Serverless Architecture"] += 70

        # 3. Clean / Hexagonal Architecture
        if any("use_case" in p.lower() or "usecase" in p.lower() or "domain" in p.lower() or "adapter" in p.lower() or "port" in p.lower() for p in paths):
            scores["Clean / Hexagonal Architecture"] += 60

        # 4. Layered Architecture (N-Tier: Controller -> Service -> Repository)
        if has_controllers and has_services and has_repos:
            scores["Layered Architecture (N-Tier)"] += 75
        elif has_controllers and (has_services or has_repos):
            scores["Layered Architecture (N-Tier)"] += 45

        # 5. MVC (Model-View-Controller)
        if has_controllers and has_models and any("view" in p.lower() or "templates" in p.lower() for p in paths):
            scores["Model-View-Controller (MVC)"] += 60

        # 6. Event-Driven Architecture
        if len(tech["queues"]) > 0 or any("event" in p.lower() or "subscriber" in p.lower() or "consumer" in p.lower() for p in paths):
            scores["Event-Driven Architecture"] += 55

        # 7. Frontend + Backend Multi-tier
        if tech["has_frontend"] and tech["has_backend"]:
            scores["Frontend + Backend Multi-Tier"] += 70

        # 8. ML / Data Pipeline
        if any(p.endswith(".ipynb") for p in paths) or any("pipeline" in p.lower() or "train" in p.lower() or "dataset" in p.lower() for p in paths):
            scores["Data / ML Pipeline"] += 65

        # 9. CLI Tool
        if any(p in {"cli.py", "bin/cli.js", "cmd/main.go", "main.rs"} for p in paths) and len(paths) < 25:
            scores["Command Line Interface (CLI)"] += 65

        # Default fallback: Modular Monolith
        scores["Modular Monolith"] += 50
        if has_services or has_controllers or has_models:
            scores["Modular Monolith"] += 25

        # Pick top scoring pattern
        best_pattern = max(scores.items(), key=lambda x: x[1])[0]
        raw_score = scores[best_pattern]
        
        # Calculate algorithmic confidence
        confidence = min(98, max(75, int(raw_score + 15)))

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

        return best_pattern, confidence, descriptions.get(best_pattern, "Modular application architecture.")

    # =========================================================================
    # PILLAR 4: DYNAMIC MERMAID DIAGRAM GENERATION
    # =========================================================================
    @staticmethod
    def _generate_mermaid_diagram(
        pattern_name: str, tech: Dict[str, Any], dep_graph: Dict[str, Any]
    ) -> str:
        lines = ["graph TD"]
        
        # Style classes
        lines.append("    %% Architectural Styling")
        lines.append("    classDef client fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef layer fill:#0f172a,stroke:#64748b,stroke-width:1px,color:#e2e8f0;")
        lines.append("    classDef db fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#e0e7ff;")
        lines.append("    classDef cache fill:#3b0764,stroke:#c084fc,stroke-width:2px,color:#f3e8ff;")
        lines.append("    classDef queue fill:#042f2e,stroke:#2dd4bf,stroke-width:2px,color:#ccfbf1;")
        lines.append("    classDef external fill:#2e1065,stroke:#a855f7,stroke-width:1px,color:#faf5ff;")

        lines.append('    User["👤 Client / Web Browser"]:::client')

        # Frontend Subgraph if present
        if tech["has_frontend"]:
            fe_name = ", ".join(tech["frontend_frameworks"]) or "Web Client"
            lines.append("    subgraph Presentation_FE [Frontend Presentation]")
            lines.append(f'        FE_App["🖥️ {fe_name} App"]:::layer')
            lines.append("    end")
            lines.append("    User -->|HTTP / HTTPS| FE_App")

        # API / Controller Layer Subgraph
        lines.append("    subgraph API_Layer [API & Routing Layer]")
        be_framework = ", ".join(tech["backend_frameworks"]) or "API Gateway"
        protocols = ", ".join(tech["api_protocols"]) or "REST"
        lines.append(f'        Gateway["🌐 {be_framework} ({protocols})"]:::layer')
        
        ctrl_sample = list(dep_graph["layers"]["controllers"])[:2]
        if ctrl_sample:
            ctrl_names = ", ".join(Path(p).stem for p in ctrl_sample)
            lines.append(f'        Controllers["🧭 Controllers ({ctrl_names})"]:::layer')
            lines.append("        Gateway --> Controllers")
        lines.append("    end")

        if tech["has_frontend"]:
            lines.append("    FE_App -->|JSON / API Requests| Gateway")
        else:
            lines.append("    User -->|API Requests| Gateway")

        # Service / Business Logic Layer Subgraph
        lines.append("    subgraph Business_Layer [Business Logic & Domain Services]")
        svc_sample = list(dep_graph["layers"]["services"])[:3]
        if svc_sample:
            svc_names = ", ".join(Path(p).stem for p in svc_sample)
            lines.append(f'        Services["⚙️ Domain Services ({svc_names})"]:::layer')
        else:
            lines.append('        Services["⚙️ Business Logic Engine"]:::layer')
        lines.append("    end")

        if ctrl_sample:
            lines.append("    Controllers -->|Invokes Logic| Services")
        else:
            lines.append("    Gateway -->|Dispatches| Services")

        # Data Access / Repository Layer Subgraph
        repo_sample = list(dep_graph["layers"]["repositories"])[:2]
        model_sample = list(dep_graph["layers"]["models"])[:2]
        
        lines.append("    subgraph Data_Layer [Data Access & Repository Layer]")
        if repo_sample:
            repo_names = ", ".join(Path(p).stem for p in repo_sample)
            lines.append(f'        Repos["🗄️ Repositories ({repo_names})"]:::layer')
            lines.append("        Services -->|Queries Data| Repos")
            target_data_entry = "Repos"
        else:
            target_data_entry = "Services"

        if model_sample:
            model_names = ", ".join(Path(p).stem for p in model_sample)
            lines.append(f'        Models["📐 Data Models ({model_names})"]:::layer')
            if repo_sample:
                lines.append("        Repos -.->|Maps| Models")
        lines.append("    end")

        # Persistence & Infrastructure Subgraph
        lines.append("    subgraph Infrastructure [Persistence & Infrastructure]")
        if tech["has_db"]:
            db_label = ", ".join(tech["databases"]) or "Database"
            lines.append(f'        DB[("🗄️ {db_label}")]:::db')
            lines.append(f"        {target_data_entry} -->|Persists / Queries| DB")
        
        if tech["has_cache"]:
            cache_label = ", ".join(tech["caches"]) or "Redis Cache"
            lines.append(f'        Cache[("⚡ {cache_label}")]:::cache')
            lines.append(f"        Services -->|Cache Lookup / Set| Cache")

        if tech["has_queue"]:
            queue_label = ", ".join(tech["queues"]) or "Async Queue"
            lines.append(f'        Queue["📬 {queue_label}"]:::queue')
            lines.append(f'        Workers["👷 Async Workers"]:::queue')
            lines.append("        Services -->|Enqueues Tasks| Queue")
            lines.append("        Queue -->|Processes| Workers")
            if tech["has_db"]:
                lines.append("        Workers -->|Updates State| DB")
        lines.append("    end")

        # External Services Subgraph
        if tech["external_services"]:
            lines.append("    subgraph External_APIs [Third-Party & Cloud Services]")
            ext_label = ", ".join(list(tech["external_services"])[:3])
            lines.append(f'        Ext["☁️ External APIs ({ext_label})"]:::external')
            lines.append("        Services -->|Third-Party Calls| Ext")
            lines.append("    end")

        return "\n".join(lines)

    # =========================================================================
    # PILLAR 6: ARCHITECTURE RISKS & POSITIVE STRENGTHS EVALUATION
    # =========================================================================
    @staticmethod
    def _evaluate_risks_and_strengths(
        ctx: RepositoryContext, tech: Dict[str, Any], dep_graph: Dict[str, Any], pattern_name: str
    ) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        score = 88.0
        findings: List[Dict[str, Any]] = []
        risks: List[Dict[str, Any]] = []
        strengths: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # STRENGTHS (Positive Architectural Traits)
        # -------------------------------------------------------------
        layers = dep_graph["layers"]
        if len(layers["controllers"]) > 0 and (len(layers["services"]) > 0 or len(layers["repositories"]) > 0):
            strengths.append({
                "title": "Clear Separation of Concerns",
                "description": "The codebase cleanly segregates API routing/controllers from business logic and data access layers.",
                "badge": "Layer Separation"
            })
            score += 4.0

        if len(layers["repositories"]) > 0 and tech["has_db"]:
            strengths.append({
                "title": "Database Isolated Behind Repository Layer",
                "description": "Database queries and persistence operations are encapsulated inside dedicated repository/DAO abstractions.",
                "badge": "Data Isolation"
            })
            score += 3.0

        if len(dep_graph["circular_cycles"]) == 0:
            strengths.append({
                "title": "Acyclic Dependency Flow",
                "description": "Zero circular dependency cycles detected across analyzed modules. Clean unidirectional import hierarchy.",
                "badge": "Clean Hierarchy"
            })
            score += 3.0

        if tech["has_queue"]:
            strengths.append({
                "title": "Decoupled Asynchronous Processing",
                "description": f"Background tasks and long-running operations are offloaded to dedicated workers via {', '.join(tech['queues'])}.",
                "badge": "Async Workers"
            })
            score += 2.0

        if tech["has_docker"]:
            strengths.append({
                "title": "Containerized Runtime Environment",
                "description": "Docker container configuration is established for reproducible development and cloud deployments.",
                "badge": "Containerization"
            })

        if tech["has_ci"]:
            strengths.append({
                "title": "Automated CI/CD Workflows",
                "description": "Continuous integration pipelines verify code changes and run automated validation checks.",
                "badge": "CI/CD"
            })

        # -------------------------------------------------------------
        # RISKS: 1. Circular Dependencies
        # -------------------------------------------------------------
        if dep_graph["circular_cycles"]:
            score -= min(15.0, len(dep_graph["circular_cycles"]) * 5.0)
            for cycle in dep_graph["circular_cycles"][:3]:
                cycle_str = cycle["display"]
                risks.append({
                    "severity": "High",
                    "type": "Circular Dependency",
                    "title": f"Circular Dependency Cycle: {cycle['path'][0]} ↔ {cycle['path'][1]}",
                    "description": f"Detected circular dependency loop: {cycle_str}. This creates tight coupling, prevents isolated unit testing, and risks runtime initialization deadlocks.",
                    "mitigation": "Introduce dependency inversion (interfaces/protocols) or extract shared domain models into a common leaf module.",
                    "file_path": cycle["full_path"][0],
                })
                findings.append({
                    "category": "Architecture",
                    "severity": "High",
                    "title": f"Circular dependency cycle ({cycle_str})",
                    "file_path": cycle["full_path"][0],
                    "line_number": 1,
                    "problem": f"Modules form a circular dependency loop: {cycle_str}. Modules in a cycle cannot be compiled, tested, or reasoned about in isolation.",
                    "recommendation": "Refactor the shared functionality into an independent lower-level module, or apply Dependency Inversion.",
                    "evidence_code": f"Cycle: {cycle_str}",
                    "confidence": 0.95,
                    "rule_id": "ARCH-CIRCULAR-DEP",
                })

        # -------------------------------------------------------------
        # RISKS: 2. God Modules (Central Bottlenecks)
        # -------------------------------------------------------------
        if dep_graph["god_modules"]:
            score -= min(12.0, len(dep_graph["god_modules"]) * 3.0)
            for gm_path in dep_graph["god_modules"][:3]:
                node = dep_graph["nodes"][gm_path]
                risks.append({
                    "severity": "Medium",
                    "type": "God Module",
                    "title": f"God Module: {Path(gm_path).name}",
                    "description": f"Module `{gm_path}` has high afferent/efferent coupling (In: {node['in_degree']}, Out: {node['out_degree']}, LOC: {node['loc']}). It acts as an architectural bottleneck.",
                    "mitigation": "Decompose into smaller single-responsibility services or helper utilities.",
                    "file_path": gm_path,
                })
                findings.append({
                    "category": "Architecture",
                    "severity": "Medium",
                    "title": f"God Module detected (`{Path(gm_path).name}`)",
                    "file_path": gm_path,
                    "line_number": 1,
                    "problem": f"File `{gm_path}` concentrates too many dependencies (In-Degree: {node['in_degree']}, Out-Degree: {node['out_degree']}, {node['loc']} LOC).",
                    "recommendation": "Split this module along domain boundaries to improve testability and reduce change collision risk.",
                    "evidence_code": f"Coupling: in={node['in_degree']}, out={node['out_degree']}, loc={node['loc']}",
                    "confidence": 0.90,
                    "rule_id": "ARCH-GOD-MODULE",
                })

        # -------------------------------------------------------------
        # RISKS: 3. Tightly Coupled Modules
        # -------------------------------------------------------------
        if dep_graph["tightly_coupled"]:
            for tc in dep_graph["tightly_coupled"][:2]:
                risks.append({
                    "severity": "Medium",
                    "type": "High Coupling",
                    "title": f"Tight Bidirectional Coupling: {Path(tc['module_a']).name} ↔ {Path(tc['module_b']).name}",
                    "description": tc["description"],
                    "mitigation": "Decouple using event emitters, callback interfaces, or intermediary services.",
                    "file_path": tc["module_a"],
                })

        # -------------------------------------------------------------
        # RISKS: 4. Layer Boundary Violations
        # -------------------------------------------------------------
        layer_violations = []
        for src_path, targets in dep_graph["adjacency"].items():
            src_layer = dep_graph["nodes"].get(src_path, {}).get("layer", "")
            for tgt_path in targets:
                tgt_layer = dep_graph["nodes"].get(tgt_path, {}).get("layer", "")
                if src_layer == "controllers" and tgt_layer in {"repositories", "models"} and "repository" not in tgt_path:
                    file_obj = ctx.files.get(src_path)
                    if file_obj and any(k in file_obj.content.lower() for k in ["select(", "session.query", "db.execute", "objects.filter"]):
                        desc = f"`{Path(src_path).name}` queries database models directly, bypassing the service/repository boundary."
                        layer_violations.append({
                            "source_layer": "Controller",
                            "target_layer": "Database",
                            "source_file": src_path,
                            "target_file": tgt_path,
                            "description": desc,
                            "severity": "High"
                        })
                        risks.append({
                            "severity": "High",
                            "type": "Layer Violation",
                            "title": f"Layer boundary bypass in `{Path(src_path).name}`",
                            "description": desc,
                            "mitigation": "Encapsulate database queries inside a dedicated service or repository method.",
                            "file_path": src_path
                        })
                        findings.append({
                            "category": "Architecture",
                            "severity": "High",
                            "title": f"Layer boundary violation (`{Path(src_path).name}` -> `{Path(tgt_path).name}`)",
                            "file_path": src_path,
                            "line_number": 1,
                            "problem": desc,
                            "recommendation": "Encapsulate persistence queries inside a dedicated repository abstraction.",
                            "evidence_code": f"{src_path} -> {tgt_path}",
                            "confidence": 0.92,
                            "rule_id": "ARCH-LAYER-VIOLATION"
                        })

        # -------------------------------------------------------------
        # RISKS: 5. Flat Directory Structure / Lack of Modular Packaging
        # -------------------------------------------------------------
        paths = list(ctx.files.keys())
        root_code_files = [p for p in paths if "/" not in p and ctx.files[p].extension in {".py", ".ts", ".js"}]
        if len(root_code_files) > 8:
            score -= 15.0
            risks.append({
                "severity": "Low",
                "type": "Flat Structure",
                "title": "Flat Root Code Organization",
                "description": f"Found {len(root_code_files)} source files dumped in root directory without sub-package separation.",
                "mitigation": "Organize code into standard domain packages (e.g. `src/api/`, `src/services/`, `src/core/`).",
                "file_path": "repository_root",
            })
            findings.append({
                "category": "Architecture",
                "severity": "Medium",
                "title": "Flat root directory structure (lack of modular packages)",
                "file_path": "repository_root",
                "line_number": 1,
                "problem": f"Found {len(root_code_files)} source files in project root without domain directory separation.",
                "recommendation": "Organize code into distinct layers or feature modules (e.g. `src/core/`, `src/services/`, `src/api/`).",
                "evidence_code": f"Root files: {', '.join(root_code_files[:5])}...",
                "confidence": 0.90,
                "rule_id": "ARCH-FLAT-ROOT",
            })

        # -------------------------------------------------------------
        # Blast Radius Computation
        # -------------------------------------------------------------
        blast_radii = []
        key_modules = sorted(dep_graph["nodes"].keys(), key=lambda k: dep_graph["nodes"][k]["in_degree"], reverse=True)[:5]
        for mod in key_modules:
            if dep_graph["nodes"][mod]["in_degree"] > 0:
                queue = deque([mod])
                visited = {mod}
                affected_modules = []
                affected_endpoints = []
                affected_services = []
                affected_tests = []
                while queue:
                    curr = queue.popleft()
                    for dep in dep_graph["reverse_adjacency"].get(curr, set()):
                        if dep not in visited:
                            visited.add(dep)
                            queue.append(dep)
                            affected_modules.append(dep)
                            layer = dep_graph["nodes"].get(dep, {}).get("layer", "")
                            if layer == "controllers":
                                affected_endpoints.append(dep)
                            elif layer == "services":
                                affected_services.append(dep)
                            elif layer == "tests":
                                affected_tests.append(dep)
                total_impact = len(affected_modules) * 2 + len(affected_endpoints) * 3 + len(affected_services) * 2
                risk_lvl = "CRITICAL" if total_impact > 15 else ("HIGH" if total_impact > 8 else ("MEDIUM" if total_impact > 3 else "LOW"))
                blast_radii.append({
                    "target_module": mod,
                    "affected_modules": affected_modules,
                    "affected_endpoints": affected_endpoints,
                    "affected_services": affected_services,
                    "affected_tests": affected_tests,
                    "risk_level": risk_lvl,
                    "total_impact_score": total_impact
                })

        score = max(25.0, min(100.0, score))
        return score, findings, risks, strengths, layer_violations, blast_radii

    # =========================================================================
    # PILLAR 5 & 7: LAYER FLOW & EXPLANATION GENERATOR
    # =========================================================================
    @staticmethod
    def _determine_layer_flow(tech: Dict[str, Any], dep_graph: Dict[str, Any]) -> List[Dict[str, str]]:
        layers = dep_graph["layers"]
        flow = []

        if tech["has_frontend"]:
            flow.append({
                "layer": "Frontend UI",
                "icon": "Monitor",
                "description": f"{', '.join(tech['frontend_frameworks']) or 'Client Web App'} renders user interface and issues HTTP/WebSocket API requests.",
            })

        flow.append({
            "layer": "Controller / API Layer",
            "icon": "Globe",
            "description": f"{', '.join(tech['backend_frameworks']) or 'API Gateway'} handles HTTP routing, request validation, authentication, and dispatching.",
        })

        if len(layers["services"]) > 0 or not len(layers["repositories"]):
            flow.append({
                "layer": "Domain Service Layer",
                "icon": "Cpu",
                "description": "Executes core business rules, transactional orchestrations, and integration logic.",
            })

        if len(layers["repositories"]) > 0 or tech["has_db"]:
            flow.append({
                "layer": "Repository / Data Access",
                "icon": "Database",
                "description": "Encapsulates database operations, ORM mapping, and transactional persistence.",
            })

        if tech["has_cache"] or tech["has_queue"]:
            extras = []
            if tech["has_cache"]:
                extras.append(f"Cache ({', '.join(tech['caches'])})")
            if tech["has_queue"]:
                extras.append(f"Async Queue ({', '.join(tech['queues'])})")
            flow.append({
                "layer": "Infrastructure & Storage",
                "icon": "Server",
                "description": f"Provides persistence, fast key-value caching, and asynchronous background worker processing ({' & '.join(extras)}).",
            })

        return flow

    @staticmethod
    def _generate_deterministic_explanation(
        pattern_name: str,
        confidence: int,
        pattern_desc: str,
        tech_detection: Dict[str, Any],
        layer_flow: List[Dict[str, str]],
        risks: List[Dict[str, Any]],
        strengths: List[Dict[str, Any]],
    ) -> str:
        """
        Generates an authoritative engineering explanation of the detected architecture.
        """
        paragraphs = []
        
        # 1. Pattern Overview
        paragraphs.append(
            f"### Architecture: {pattern_name} (Confidence: {confidence}%)\n"
            f"{pattern_desc}"
        )

        # 2. Request Lifecycle Walkthrough
        flow_steps = " ➔ ".join(f"**{step['layer']}**" for step in layer_flow)
        paragraphs.append(
            f"#### 🔄 Request Lifecycle & Data Flow\n"
            f"The request execution pipeline follows an organized sequence: {flow_steps}.\n\n"
            + "\n".join(f"1. **{s['layer']}**: {s['description']}" for s in layer_flow)
        )

        # 3. Infrastructure & Component Separation
        db_str = ", ".join(tech_detection["databases"]) or "In-Memory / File Storage"
        cache_str = f" paired with **{', '.join(tech_detection['caches'])}** for low-latency caching" if tech_detection["has_cache"] else ""
        queue_str = f" and **{', '.join(tech_detection['queues'])}** for background job offloading" if tech_detection["has_queue"] else ""
        
        paragraphs.append(
            f"#### 🏗️ Infrastructure & Storage Topology\n"
            f"The application persists state using **{db_str}**{cache_str}{queue_str}. "
            f"Container orchestration is {'configured with Docker' if tech_detection['has_docker'] else 'managed without Docker containers'} "
            f"and automated CI/CD is {'active via ' + ', '.join(tech_detection['ci_markers']) if tech_detection['has_ci'] else 'not detected in standard paths'}."
        )

        # 4. Architectural Health & Risk Profile
        if risks:
            risk_bullets = "\n".join(f"- ⚠️ **{r['title']}**: {r['description']}" for r in risks[:3])
            paragraphs.append(f"#### ⚠️ Key Architectural Risks\n{risk_bullets}")
        else:
            paragraphs.append(
                "#### ✅ Architectural Health\n"
                "The repository maintains solid architectural boundaries with zero circular dependencies or high-risk coupling bottlenecks detected."
            )

        return "\n\n".join(paragraphs)

