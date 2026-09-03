import ast
import re
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from pathlib import Path
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.architecture.model import Component, Dependency

class DependencyGraphBuilder:
    """
    Constructs an AST and static import graph across source files,
    maps files to high-level architectural components, and computes coupling metrics.
    """

    @staticmethod
    def build_graph(
        ctx: RepositoryContext, scan_result: Dict[str, Any]
    ) -> Tuple[List[Component], List[Dependency], Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Dict[str, Any]]]:
        """
        Returns:
            (components, dependencies, adjacency, reverse_adjacency, node_metadata)
        """
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cs", ".rb", ".php"}
        module_path_map: Dict[str, str] = {}
        node_metadata: Dict[str, Dict[str, Any]] = {}
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

        # Step 1: Register module nodes and build alias mapping
        for rel_path, file in ctx.files.items():
            if file.extension in code_exts:
                norm_path = rel_path.replace("\\", "/")
                loc = len(file.content.splitlines())
                layer = DependencyGraphBuilder._detect_file_layer(norm_path)
                
                node_metadata[norm_path] = {
                    "id": norm_path,
                    "label": Path(norm_path).stem,
                    "layer": layer,
                    "loc": loc,
                    "extension": file.extension
                }

                # Path aliases (e.g. backend.app.api.routes -> backend/app/api/routes.py)
                stem = Path(norm_path).stem
                parts = norm_path.replace("/", ".").replace(file.extension, "").split(".")
                for i in range(len(parts)):
                    alias = ".".join(parts[i:])
                    module_path_map[alias] = norm_path
                    module_path_map[alias.replace(".", "/")] = norm_path
                module_path_map[norm_path] = norm_path
                module_path_map[norm_path.replace(file.extension, "")] = norm_path

        # Step 2: Extract imports and establish dependency edges
        dependencies: List[Dependency] = []
        for rel_path, file in ctx.files.items():
            if rel_path not in node_metadata:
                continue
            
            imports = DependencyGraphBuilder._extract_imports(file.content, file.extension, rel_path)
            for imp in imports:
                target = DependencyGraphBuilder._resolve_import(imp, rel_path, module_path_map, node_metadata)
                if target and target != rel_path:
                    if target not in adjacency[rel_path]:
                        adjacency[rel_path].add(target)
                        reverse_adjacency[target].add(rel_path)
                        dependencies.append(Dependency(
                            source=rel_path,
                            target=target,
                            type="import",
                            weight=1
                        ))

        # Step 3: Compute coupling metrics per node
        for node_id, meta in node_metadata.items():
            out_deg = len(adjacency[node_id])
            in_deg = len(reverse_adjacency[node_id])
            meta["out_degree"] = out_deg
            meta["in_degree"] = in_deg
            total = in_deg + out_deg
            meta["instability"] = round(out_deg / total, 2) if total > 0 else 0.0

        # Step 4: Group files into logical Components
        components = DependencyGraphBuilder._build_components(node_metadata, ctx)

        return components, dependencies, adjacency, reverse_adjacency, node_metadata

    @staticmethod
    def _detect_file_layer(path: str) -> str:
        p = path.lower()
        if any(k in p for k in ["controller", "route", "router", "endpoint", "handler", "api/", "/api.", "/views"]):
            return "controllers"
        if any(k in p for k in ["service", "use_case", "usecase", "domain", "manager", "interactor"]):
            return "services"
        if any(k in p for k in ["repository", "repo", "dao", "data_access", "query", "queries"]):
            return "repositories"
        if any(k in p for k in ["model", "schema", "entity", "entities", "dto", "types"]):
            return "models"
        if any(k in p for k in ["middleware", "interceptor", "guard", "filter"]):
            return "middleware"
        if any(k in p for k in ["worker", "job", "task", "queue", "consumer", "subscriber"]):
            return "workers"
        if any(k in p for k in ["components/", "pages/", "views/", "frontend/", "client/"]):
            return "ui"
        if any(k in p for k in ["config", "setting", "env"]):
            return "config"
        if any(k in p for k in ["test", "spec"]):
            return "tests"
        return "utils"

    @staticmethod
    def _extract_imports(content: str, ext: str, file_path: str) -> List[str]:
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
                        level = node.level
                        if level > 0:
                            curr_dir = "/".join(file_path.split("/")[:-1])
                            imports.append(f"RELATIVE:{level}:{curr_dir}:{module}")
                        else:
                            imports.append(module)
            except Exception:
                matches = re.findall(r"^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", content, re.MULTILINE)
                for m in matches:
                    imp = m[0] or m[1]
                    if imp:
                        imports.append(imp)
        elif ext in {".ts", ".tsx", ".js", ".jsx"}:
            matches = re.findall(r"""(?:import|from|require)\s*\(?['"]([@\w\.\/\-\_]+)['"]\)? """, content)
            imports.extend(matches)
        elif ext == ".go":
            matches = re.findall(r"""["']([a-zA-Z0-9_\-\.\/]+)["']""", content)
            imports.extend(matches)
        return imports

    @staticmethod
    def _resolve_import(
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

        norm_imp = imp.replace(".", "/").strip("/")
        if imp in module_path_map:
            return module_path_map[imp]
        if norm_imp in module_path_map:
            return module_path_map[norm_imp]

        for node_id in nodes:
            node_clean = node_id.rsplit(".", 1)[0]
            if node_clean.endswith(norm_imp) or node_clean.endswith(imp.replace(".", "/")):
                return node_id

        return None

    @staticmethod
    def _build_components(nodes: Dict[str, Dict[str, Any]], ctx: RepositoryContext) -> List[Component]:
        layer_buckets: Dict[str, List[str]] = defaultdict(list)
        for node_id, meta in nodes.items():
            layer_buckets[meta["layer"]].append(node_id)

        components = []
        layer_configs = [
            ("API / Presentation", "controller", "presentation", "controllers", "API routing, controllers, and presentation handlers."),
            ("Business Logic", "service", "business", "services", "Core domain services and business rule orchestrations."),
            ("Persistence / Repositories", "repository", "data_access", "repositories", "Data access layer and repository query isolation."),
            ("Domain Models & Schemas", "model", "data_access", "models", "Data models, entity schemas, and DTOs."),
            ("Middleware & Guards", "middleware", "infrastructure", "middleware", "Request interceptors, authentication guards, and filters."),
            ("Workers & Async Tasks", "worker", "infrastructure", "workers", "Background tasks and asynchronous worker processing."),
            ("UI Components", "ui", "presentation", "ui", "Client-side frontend views and interface components."),
            ("Utilities & Core", "util", "util", "utils", "Shared utility helpers and common modules.")
        ]

        for name, comp_type, layer, bucket_key, desc in layer_configs:
            file_list = layer_buckets.get(bucket_key, [])
            if file_list:
                total_loc = sum(len(ctx.files[f].content.splitlines()) for f in file_list if f in ctx.files)
                components.append(Component(
                    name=name,
                    type=comp_type,
                    layer=layer,
                    files=sorted(file_list),
                    file_count=len(file_list),
                    loc=total_loc,
                    description=desc
                ))

        return components
