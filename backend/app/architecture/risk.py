from typing import Dict, List, Set, Tuple, Any, Optional
from collections import deque
from pathlib import Path
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.architecture.model import (
    ArchitectureRisk,
    LayerViolation,
    BlastRadius,
    ArchitectureStrength,
    Component,
)

class ArchitectureRiskEngine:
    """
    Evaluates architectural health, detects circular dependency cycles,
    identifies high coupling/god modules, enforces layer boundaries,
    and calculates downstream Blast Radius impact.
    """

    @staticmethod
    def analyze_risks(
        ctx: RepositoryContext,
        components: List[Component],
        adjacency: Dict[str, Set[str]],
        reverse_adjacency: Dict[str, Set[str]],
        node_metadata: Dict[str, Dict[str, Any]],
        technologies: List[Any],
    ) -> Tuple[List[ArchitectureRisk], List[LayerViolation], List[BlastRadius], List[ArchitectureStrength]]:
        risks: List[ArchitectureRisk] = []
        layer_violations: List[LayerViolation] = []
        blast_radii: List[BlastRadius] = []
        strengths: List[ArchitectureStrength] = []

        # -------------------------------------------------------------
        # 1. Circular Dependency Cycles
        # -------------------------------------------------------------
        cycles = ArchitectureRiskEngine._find_cycles(adjacency)
        for cycle in cycles:
            cycle_str = " → ".join(Path(p).name for p in cycle)
            risks.append(ArchitectureRisk(
                rule_id="ARCH-CIRCULAR-DEP",
                severity="High",
                type="Circular Dependency",
                title=f"Circular dependency cycle ({Path(cycle[0]).name} ↔ {Path(cycle[1]).name})",
                description=f"Detected circular dependency loop: {cycle_str}. Tightly coupled modules in a cycle cannot be compiled, unit-tested, or modified in isolation.",
                mitigation="Refactor shared dependencies into an independent lower-level module, or apply Dependency Inversion (interfaces).",
                evidence=f"Cycle: {cycle_str}",
                file_path=cycle[0]
            ))

        # -------------------------------------------------------------
        # 2. Layer Violation Engine
        # -------------------------------------------------------------
        for src_path, targets in adjacency.items():
            src_meta = node_metadata.get(src_path)
            if not src_meta:
                continue
            src_layer = src_meta["layer"]

            for tgt_path in targets:
                tgt_meta = node_metadata.get(tgt_path)
                if not tgt_meta:
                    continue
                tgt_layer = tgt_meta["layer"]

                # Violation: Controller directly accesses DB/ORM bypassing Service/Repository
                if src_layer == "controllers" and tgt_layer in {"repositories", "models"} and "repository" not in tgt_path:
                    file_content = ctx.files.get(src_path, None)
                    if file_content and any(k in file_content.content.lower() for k in ["select(", "session.query", "db.execute", "objects.filter"]):
                        violation = LayerViolation(
                            source_layer="Controller / Presentation",
                            target_layer="Database Persistence",
                            source_file=src_path,
                            target_file=tgt_path,
                            description=f"`{Path(src_path).name}` queries database models directly, bypassing the service/repository boundary.",
                            severity="High"
                        )
                        layer_violations.append(violation)
                        risks.append(ArchitectureRisk(
                            rule_id="ARCH-LAYER-VIOLATION",
                            severity="High",
                            type="Layer Violation",
                            title=f"Layer boundary bypass in `{Path(src_path).name}`",
                            description=violation.description,
                            mitigation="Encapsulate database queries inside a dedicated service or repository method.",
                            evidence=f"{src_path} -> {tgt_path}",
                            file_path=src_path
                        ))

                # Violation: Low-level layer depending on Presentation/Controllers
                if src_layer in {"repositories", "models", "services"} and tgt_layer == "controllers":
                    violation = LayerViolation(
                        source_layer=src_layer.capitalize(),
                        target_layer="Controllers",
                        source_file=src_path,
                        target_file=tgt_path,
                        description=f"Inward layer violation: `{Path(src_path).name}` ({src_layer}) depends on `{Path(tgt_path).name}` (controllers).",
                        severity="High"
                    )
                    layer_violations.append(violation)
                    risks.append(ArchitectureRisk(
                        rule_id="ARCH-LAYER-VIOLATION",
                        severity="High",
                        type="Layer Violation",
                        title=f"Inward architectural boundary violation in `{Path(src_path).name}`",
                        description=violation.description,
                        mitigation="Invert dependency flow so higher-level controllers depend on lower-level services/repositories, not vice-versa.",
                        evidence=f"{src_path} -> {tgt_path}",
                        file_path=src_path
                    ))

        # -------------------------------------------------------------
        # 3. God Modules & High Coupling
        # -------------------------------------------------------------
        for node_id, meta in node_metadata.items():
            if (meta["out_degree"] >= 8 or meta["in_degree"] >= 8 or meta["loc"] >= 600) and meta["layer"] in {"controllers", "services", "repositories", "models"}:
                risks.append(ArchitectureRisk(
                    rule_id="ARCH-GOD-MODULE",
                    severity="Medium",
                    type="God Module",
                    title=f"God Module bottleneck in `{Path(node_id).name}`",
                    description=f"Module `{node_id}` concentrates too many dependencies (In-Degree: {meta['in_degree']}, Out-Degree: {meta['out_degree']}, {meta['loc']} LOC).",
                    mitigation="Decompose this module along domain boundaries to improve testability and reduce collision risk.",
                    evidence=f"in_degree={meta['in_degree']}, out_degree={meta['out_degree']}, loc={meta['loc']}",
                    file_path=node_id
                ))

        # -------------------------------------------------------------
        # 4. Blast Radius Impact Analysis
        # -------------------------------------------------------------
        # Compute blast radius for top imported services/modules
        key_modules = sorted(node_metadata.keys(), key=lambda k: node_metadata[k]["in_degree"], reverse=True)[:5]
        for mod in key_modules:
            if node_metadata[mod]["in_degree"] > 0:
                br = ArchitectureRiskEngine._compute_blast_radius(mod, reverse_adjacency, node_metadata)
                blast_radii.append(br)

        # -------------------------------------------------------------
        # 5. Positive Architectural Strengths
        # -------------------------------------------------------------
        comp_types = set(c.type for c in components)
        if "controller" in comp_types and ("service" in comp_types or "repository" in comp_types):
            strengths.append(ArchitectureStrength(
                title="Clear Separation of Concerns",
                description="The codebase clearly segregates API routing, business logic orchestration, and data access layers.",
                badge="Layer Separation"
            ))

        if "repository" in comp_types:
            strengths.append(ArchitectureStrength(
                title="Database Isolated Behind Repository Layer",
                description="Database queries and persistence operations are encapsulated inside dedicated repository abstractions.",
                badge="Data Isolation"
            ))

        if len(cycles) == 0:
            strengths.append(ArchitectureStrength(
                title="Acyclic Dependency Hierarchy",
                description="Zero circular dependency loops detected across analyzed modules. Clean unidirectional import hierarchy.",
                badge="Clean Hierarchy"
            ))

        if any(t.technology in {"Celery", "RabbitMQ", "Apache Kafka", "BullMQ"} for t in technologies):
            strengths.append(ArchitectureStrength(
                title="Decoupled Asynchronous Processing",
                description="Background tasks and long-running operations are offloaded to dedicated asynchronous worker queues.",
                badge="Async Workers"
            ))

        if any(t.technology in {"Docker", "Docker Compose"} for t in technologies):
            strengths.append(ArchitectureStrength(
                title="Containerized Runtime Environment",
                description="Docker container configurations are established for reproducible development and cloud deployments.",
                badge="Containerization"
            ))

        return risks, layer_violations, blast_radii, strengths

    @staticmethod
    def _find_cycles(adj: Dict[str, Set[str]]) -> List[List[str]]:
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
                    cycle_start_idx = rec_stack.index(neighbor)
                    cycle_path = rec_stack[cycle_start_idx:] + [neighbor]
                    
                    canon = cycle_path[:-1]
                    min_idx = canon.index(min(canon))
                    normalized = canon[min_idx:] + canon[:min_idx]
                    signature = " -> ".join(normalized)
                    
                    if not any(c[0] == signature for c in cycles) and len(canon) <= 6:
                        cycles.append((signature, cycle_path))

            rec_set.remove(node)
            rec_stack.pop()

        for node in list(adj.keys()):
            if node not in visited:
                dfs(node)

        return [c[1] for c in cycles[:10]]

    @staticmethod
    def _compute_blast_radius(
        target_mod: str, reverse_adj: Dict[str, Set[str]], node_meta: Dict[str, Dict[str, Any]]
    ) -> BlastRadius:
        """
        Traverses downstream dependency tree (all modules that depend on target_mod).
        """
        queue = deque([target_mod])
        visited = {target_mod}
        affected_modules = []
        affected_endpoints = []
        affected_services = []
        affected_tests = []

        while queue:
            curr = queue.popleft()
            dependents = reverse_adj.get(curr, set())
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
                    affected_modules.append(dep)
                    
                    layer = node_meta.get(dep, {}).get("layer", "")
                    if layer == "controllers":
                        affected_endpoints.append(dep)
                    elif layer == "services":
                        affected_services.append(dep)
                    elif layer == "tests":
                        affected_tests.append(dep)

        total_impact = len(affected_modules) * 2 + len(affected_endpoints) * 3 + len(affected_services) * 2
        risk_level = "CRITICAL" if total_impact > 15 else ("HIGH" if total_impact > 8 else ("MEDIUM" if total_impact > 3 else "LOW"))

        return BlastRadius(
            target_module=target_mod,
            affected_modules=affected_modules,
            affected_endpoints=affected_endpoints,
            affected_services=affected_services,
            affected_tests=affected_tests,
            risk_level=risk_level,
            total_impact_score=total_impact
        )
