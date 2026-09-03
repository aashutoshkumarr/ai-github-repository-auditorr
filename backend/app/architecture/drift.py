from typing import Dict, Any, List, Optional
from backend.app.architecture.model import ArchitectureModel, Component, Dependency
from backend.app.models.schemas import ArchitectureDriftResult


class ArchitectureDriftDetector:
    """
    Compares baseline architecture model against current architecture model to detect:
    - New or removed components/services/repositories
    - New communication flows or layer bypasses
    - Structural regressions & circular dependency introductions
    - Generates visual Mermaid drift diagrams
    """

    @classmethod
    def compare_architecture(
        cls,
        base_model: ArchitectureModel,
        current_model: ArchitectureModel,
        repo_id: str = "repo",
        base_report_id: str = "base",
        current_report_id: str = "current",
    ) -> ArchitectureDriftResult:
        base_comps = {c.name: c for c in base_model.components}
        curr_comps = {c.name: c for c in current_model.components}

        base_deps = {(d.source, d.target): d for d in base_model.dependencies}
        curr_deps = {(d.source, d.target): d for d in current_model.dependencies}

        # Added & Removed components
        added_components = [name for name in curr_comps if name not in base_comps]
        removed_components = [name for name in base_comps if name not in curr_comps]

        # Added & Removed communication flows
        added_flows = [f"{s} -> {t}" for (s, t) in curr_deps if (s, t) not in base_deps]
        removed_flows = [f"{s} -> {t}" for (s, t) in base_deps if (s, t) not in curr_deps]

        # Structural violations delta
        base_viols = {v.rule_id if hasattr(v, 'rule_id') else f"{v.source_layer}->{v.target_layer}" for v in base_model.layer_violations}
        curr_viols = {v.rule_id if hasattr(v, 'rule_id') else f"{v.source_layer}->{v.target_layer}" for v in current_model.layer_violations}
        new_violations = list(curr_viols - base_viols)

        base_risks = {r.title for r in base_model.risks if "circular" in r.type.lower()}
        curr_risks = {r.title for r in current_model.risks if "circular" in r.type.lower()}
        new_cycles = list(curr_risks - base_risks)
        if new_cycles:
            new_violations.extend([f"Circular dependency: {c}" for c in new_cycles])

        drift_detected = bool(added_components or removed_components or added_flows or removed_flows or new_violations)

        # Calculate severity
        if new_violations or len(new_cycles) > 0:
            drift_severity = "High"
        elif len(added_components) >= 2 or len(added_flows) >= 3:
            drift_severity = "Medium"
        elif drift_detected:
            drift_severity = "Low"
        else:
            drift_severity = "None"

        # Generate Mermaid Drift Diagram
        drift_mermaid = cls._generate_drift_mermaid(curr_comps, base_comps, curr_deps, base_deps)

        # Generate explanation
        explanation = cls._generate_explanation(
            base_model.pattern.primary,
            current_model.pattern.primary,
            added_components,
            removed_components,
            added_flows,
            new_violations,
        )

        return ArchitectureDriftResult(
            repo_id=repo_id,
            base_report_id=base_report_id,
            current_report_id=current_report_id,
            drift_detected=drift_detected,
            drift_severity=drift_severity,
            added_components=added_components,
            removed_components=removed_components,
            added_flows=added_flows,
            removed_flows=removed_flows,
            new_violations=new_violations,
            drift_mermaid=drift_mermaid,
            explanation=explanation,
        )

    @classmethod
    def _generate_drift_mermaid(cls, curr_comps, base_comps, curr_deps, base_deps) -> str:
        lines = [
            "flowchart TD",
            "    classDef added fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;",
            "    classDef normal fill:#1e293b,stroke:#475569,stroke-width:1px,color:#e2e8f0;"
        ]

        for name, comp in curr_comps.items():
            safe_id = name.replace("-", "_").replace(".", "_").replace("/", "_").replace(" ", "_")
            if name not in base_comps:
                lines.append(f'    {safe_id}["[NEW] {comp.name} ({comp.layer})"]:::added')
            else:
                lines.append(f'    {safe_id}["{comp.name} ({comp.layer})"]:::normal')

        for (s, t) in curr_deps:
            s_safe = s.replace("-", "_").replace(".", "_").replace("/", "_").replace(" ", "_")
            t_safe = t.replace("-", "_").replace(".", "_").replace("/", "_").replace(" ", "_")
            if (s, t) not in base_deps:
                lines.append(f"    {s_safe} == New Flow ==> {t_safe}")
            else:
                lines.append(f"    {s_safe} --> {t_safe}")

        return "\n".join(lines)

    @classmethod
    def _generate_explanation(
        cls,
        base_pattern: str,
        curr_pattern: str,
        added: List[str],
        removed: List[str],
        flows: List[str],
        violations: List[str],
    ) -> str:
        if not (added or removed or flows or violations):
            return "No architectural drift detected. System topology and layer boundaries remain stable."

        parts = []
        if base_pattern != curr_pattern:
            parts.append(f"Architecture pattern evolved from '{base_pattern}' to '{curr_pattern}'.")

        if added:
            parts.append(f"Added {len(added)} new component(s): {', '.join(added)}.")

        if removed:
            parts.append(f"Removed {len(removed)} component(s): {', '.join(removed)}.")

        if flows:
            parts.append(f"Introduced {len(flows)} new communication flow(s).")

        if violations:
            parts.append(f"⚠️ Structural Warning: {len(violations)} new architectural violation(s) identified ({'; '.join(violations)}).")

        return " ".join(parts)
