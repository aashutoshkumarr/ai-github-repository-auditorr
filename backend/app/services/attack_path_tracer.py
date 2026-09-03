from typing import List, Optional, Dict, Any
from backend.app.models.schemas import AttackPathNode, AttackPathResult


class AttackPathTracer:
    """
    Traces end-to-end security attack paths:
    Untrusted User Input / Entry Point -> Controller / Router -> Service Logic -> Vulnerable Sink
    """

    @classmethod
    def trace_attack_path(
        cls,
        finding_id: str,
        title: str,
        severity: str,
        file_path: str,
        line_number: int,
        cwe_id: Optional[str] = None,
        evidence_code: Optional[str] = None,
        rule_id: Optional[str] = None,
    ) -> AttackPathResult:
        nodes: List[AttackPathNode] = []
        rule_lower = (rule_id or "").lower()
        title_lower = title.lower()

        if "sql" in rule_lower or "sql" in title_lower or cwe_id == "CWE-89":
            entry_point = "HTTP Client / Untrusted Request (API Endpoint)"
            sink_point = f"{file_path}:{line_number} (SQL Execution Engine)"

            nodes.append(
                AttackPathNode(
                    step_number=1,
                    layer="API / Entry Point",
                    component_or_file="FastAPI / Express Router",
                    action_or_call="Receives unvalidated HTTP query parameters or JSON body",
                    risk_description="Untrusted user input enters the application perimeter.",
                    is_source=True,
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=2,
                    layer="Controller Layer",
                    component_or_file="app/controllers/user_controller.py",
                    action_or_call="Forwards raw parameter to database service without type coercion",
                    risk_description="Missing input sanitization and schema bounds validation.",
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=3,
                    layer="Repository / DB Layer",
                    component_or_file=file_path,
                    action_or_call="String formatting / interpolation: " + (evidence_code or "query = f'SELECT...'"),
                    risk_description="Dynamic concatenation allows attacker to break out of SQL syntax.",
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=4,
                    layer="Database Engine (Sink)",
                    component_or_file="PostgreSQL / SQLite Connection",
                    action_or_call="cursor.execute(unvalidated_sql)",
                    risk_description="Arbitrary SQL payload executed with database connection privileges.",
                    is_sink=True,
                )
            )
            remediation = "Replace string interpolation with parameterized queries (:id or %s) to let the database engine isolate SQL tokens from user data."

        elif "secret" in rule_lower or "key" in rule_lower or cwe_id == "CWE-798":
            entry_point = f"{file_path}:{line_number} (Source Code Repository)"
            sink_point = "Public VCS / Build Artifact Exfiltration"

            nodes.append(
                AttackPathNode(
                    step_number=1,
                    layer="Source Code (Source)",
                    component_or_file=file_path,
                    action_or_call="Hardcoded credential plaintext: " + (evidence_code or "api_key = '...'"),
                    risk_description="Sensitive cryptographic or cloud tokens committed directly to Git.",
                    is_source=True,
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=2,
                    layer="CI/CD Build & Version Control",
                    component_or_file="GitHub Push / Artifact Registry",
                    action_or_call="Secrets cloned into build runners and container images",
                    risk_description="Token exposed in build logs and repository commit history.",
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=3,
                    layer="External Cloud API (Sink)",
                    component_or_file="AWS / OpenAI / DB Endpoint",
                    action_or_call="Unauthorized API invocation by unauthorized actors",
                    risk_description="Compromised credentials permit lateral movement and account takeover.",
                    is_sink=True,
                )
            )
            remediation = "Rotate the exposed secret immediately, remove from Git history with git-filter-repo, and migrate to environment variables (os.getenv)."

        else:
            entry_point = "Untrusted Client Input"
            sink_point = f"{file_path}:{line_number}"

            nodes.append(
                AttackPathNode(
                    step_number=1,
                    layer="Perimeter (Source)",
                    component_or_file="Public Interface",
                    action_or_call="Inbound payload received from user",
                    risk_description="External data enters the system boundary.",
                    is_source=True,
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=2,
                    layer="Application Logic",
                    component_or_file=file_path,
                    action_or_call=evidence_code or "Unsafe execution function",
                    risk_description="Inadequate boundary validation before reaching sensitive sink.",
                )
            )
            nodes.append(
                AttackPathNode(
                    step_number=3,
                    layer="System Runtime (Sink)",
                    component_or_file="Runtime Engine",
                    action_or_call="Execution of unvalidated instruction",
                    risk_description="Security invariant breached.",
                    is_sink=True,
                )
            )
            remediation = "Apply defense-in-depth sanitization and enforce strict architectural boundary isolation."

        mermaid_flow = cls._generate_mermaid_flow(nodes)

        return AttackPathResult(
            finding_id=finding_id,
            title=title,
            severity=severity,
            cwe_id=cwe_id,
            entry_point=entry_point,
            sink_point=sink_point,
            nodes=nodes,
            mermaid_flow=mermaid_flow,
            remediation_summary=remediation,
        )

    @classmethod
    def _generate_mermaid_flow(cls, nodes: List[AttackPathNode]) -> str:
        lines = ["flowchart TD", "    classDef source fill:#b91c1c,stroke:#f87171,stroke-width:2px,color:#fff;", "    classDef step fill:#1e293b,stroke:#475569,stroke-width:1px,color:#e2e8f0;", "    classDef sink fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fff;"]

        for i, n in enumerate(nodes):
            style = ":::source" if n.is_source else (":::sink" if n.is_sink else ":::step")
            safe_text = f"Step {n.step_number}: {n.layer}<br/><b>{n.component_or_file}</b><br/><i>{n.action_or_call[:45]}</i>"
            lines.append(f'    node{i}["{safe_text}"]{style}')
            if i > 0:
                lines.append(f"    node{i-1} == Tainted Data Flow ==> node{i}")

        return "\n".join(lines)
