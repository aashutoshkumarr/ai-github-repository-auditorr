from typing import Dict, List, Set, Any
from pathlib import Path
from backend.app.services.repo_fetcher import RepositoryContext

class FileStructureScanner:
    """
    Scans repository file structure and classifies directory roles,
    entry points, configuration files, manifests, tests, and infrastructure markers.
    """

    @staticmethod
    def scan(ctx: RepositoryContext) -> Dict[str, Any]:
        paths = list(ctx.files.keys())
        
        directories: Dict[str, List[str]] = {
            "controllers": [],
            "services": [],
            "repositories": [],
            "models": [],
            "middleware": [],
            "workers": [],
            "config": [],
            "tests": [],
            "infra": [],
            "utils": [],
            "ui": [],
            "other": []
        }

        entry_points = []
        manifests = []
        infra_files = []
        test_files = []
        config_files = []

        entry_names = {
            "main.py", "app.py", "server.py", "wsgi.py", "asgi.py", "manage.py",
            "index.ts", "server.ts", "main.ts", "index.js", "app.js", "server.js",
            "cmd/main.go", "main.go", "src/main.rs", "main.rs", "Program.cs"
        }

        manifest_names = {
            "package.json", "requirements.txt", "pyproject.toml", "setup.py",
            "Pipfile", "poetry.lock", "go.mod", "Cargo.toml", "pom.xml",
            "build.gradle", "Gemfile", "composer.json"
        }

        for rel_path, file in ctx.files.items():
            norm_path = rel_path.replace("\\", "/")
            p_lower = norm_path.lower()
            file_name = Path(norm_path).name.lower()

            # Entry point check
            if file_name in entry_names or any(norm_path.endswith("/" + ep) for ep in entry_names):
                entry_points.append(norm_path)

            # Manifest check
            if file_name in manifest_names or any(norm_path.endswith("/" + m) for m in manifest_names):
                manifests.append(norm_path)

            # Infrastructure check
            if any(k in p_lower for k in ["dockerfile", "docker-compose", "k8s", "kubernetes", "helm", "terraform", ".github/workflows", ".gitlab-ci"]):
                infra_files.append(norm_path)
                directories["infra"].append(norm_path)

            # Test files check
            if any(k in p_lower for k in ["test", "spec", "__tests__", "test_", "_test"]):
                test_files.append(norm_path)
                directories["tests"].append(norm_path)

            # Config files check
            elif any(k in p_lower for k in ["config", "setting", ".env", "alembic.ini", "tsconfig", "webpack", "vite.config", "tailwind.config"]):
                config_files.append(norm_path)
                directories["config"].append(norm_path)

            # Controller / Presentation layer
            elif any(k in p_lower for k in ["controller", "route", "router", "endpoint", "handler", "api/", "/api.", "/views"]):
                directories["controllers"].append(norm_path)

            # Services / Business Logic
            elif any(k in p_lower for k in ["service", "use_case", "usecase", "domain", "manager", "interactor"]):
                directories["services"].append(norm_path)

            # Repositories / Data Access
            elif any(k in p_lower for k in ["repository", "repo", "dao", "data_access", "query", "queries", "database"]):
                directories["repositories"].append(norm_path)

            # Models / Entities
            elif any(k in p_lower for k in ["model", "schema", "entity", "entities", "dto", "types"]):
                directories["models"].append(norm_path)

            # Middleware
            elif any(k in p_lower for k in ["middleware", "interceptor", "guard", "filter"]):
                directories["middleware"].append(norm_path)

            # Workers / Background jobs
            elif any(k in p_lower for k in ["worker", "job", "task", "queue", "consumer", "subscriber"]):
                directories["workers"].append(norm_path)

            # UI / Frontend
            elif any(k in p_lower for k in ["components/", "pages/", "views/", "frontend/", "client/", "web/", "app/"]) and file.extension in {".tsx", ".jsx", ".vue", ".svelte", ".html", ".css"}:
                directories["ui"].append(norm_path)

            # Utils
            elif any(k in p_lower for k in ["util", "helper", "common", "lib/"]):
                directories["utils"].append(norm_path)

            else:
                directories["other"].append(norm_path)

        dir_roots = sorted(list(set(p.split("/")[0] for p in paths if "/" in p)))

        return {
            "directories": directories,
            "entry_points": sorted(entry_points),
            "manifests": sorted(manifests),
            "infra_files": sorted(infra_files),
            "test_files": sorted(test_files),
            "config_files": sorted(config_files),
            "dir_roots": dir_roots,
            "total_files": len(paths),
        }
