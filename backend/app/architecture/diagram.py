from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.architecture.model import Component, Dependency, TechnologyEvidence

class MermaidDiagramGenerator:
    """
    Generates a dynamic, syntax-validated Mermaid.js flowchart
    directly from detected components, layers, and dependency edges.
    """

    @staticmethod
    def generate(
        components: List[Component],
        dependencies: List[Dependency],
        technologies: List[TechnologyEvidence],
        pattern_name: str
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

        # Find components by type
        comp_map = {c.type: c for c in components}
        tech_map = {t.technology: t for t in technologies}

        # 1. UI / Frontend Subgraph
        has_ui = "ui" in comp_map
        if has_ui:
            ui_comp = comp_map["ui"]
            fe_tech = next((t.technology for t in technologies if t.category in {"Frontend UI Library", "Fullstack / Frontend Framework"}), "Web Client")
            lines.append("    subgraph Frontend_Presentation [Frontend Presentation]")
            lines.append(f'        FE_App["🖥️ {fe_tech} ({ui_comp.file_count} files)"]:::layer')
            lines.append("    end")
            lines.append("    User -->|HTTP / WebSocket| FE_App")

        # 2. API / Controller Gateway Subgraph
        lines.append("    subgraph API_Layer [API & Routing Layer]")
        be_tech = next((t.technology for t in technologies if t.category == "Backend Framework"), "API Gateway")
        ctrl_comp = comp_map.get("controller")
        ctrl_label = f"Controllers ({ctrl_comp.file_count} files)" if ctrl_comp else "Routing Gateway"
        lines.append(f'        Gateway["🌐 {be_tech} Gateway"]:::layer')
        lines.append(f'        Controllers["🧭 {ctrl_label}"]:::layer')
        lines.append("        Gateway --> Controllers")
        lines.append("    end")

        if has_ui:
            lines.append("    FE_App -->|JSON / API Requests| Gateway")
        else:
            lines.append("    User -->|API Requests| Gateway")

        # 3. Business Logic / Services Subgraph
        svc_comp = comp_map.get("service")
        lines.append("    subgraph Business_Layer [Business Logic & Domain Services]")
        if svc_comp:
            svc_names = ", ".join(Path(f).stem for f in svc_comp.files[:3])
            lines.append(f'        Services["⚙️ Domain Services ({svc_comp.file_count} files)"]:::layer')
        else:
            lines.append('        Services["⚙️ Core Application Logic"]:::layer')
        lines.append("    end")
        lines.append("    Controllers -->|Invokes Logic| Services")

        # 4. Data Access / Repository Subgraph
        repo_comp = comp_map.get("repository")
        model_comp = comp_map.get("model")
        
        lines.append("    subgraph Data_Layer [Data Access & Repository Layer]")
        if repo_comp:
            lines.append(f'        Repos["🗄️ Repositories ({repo_comp.file_count} files)"]:::layer')
            lines.append("        Services -->|Queries / Persists| Repos")
            target_storage_caller = "Repos"
        else:
            target_storage_caller = "Services"

        if model_comp:
            lines.append(f'        Models["📐 Entity Models ({model_comp.file_count} files)"]:::layer')
            if repo_comp:
                lines.append("        Repos -.->|Hydrates| Models")
        lines.append("    end")

        # 5. Infrastructure & Storage Subgraph
        db_tech = next((t.technology for t in technologies if t.category == "Database"), None)
        cache_tech = next((t.technology for t in technologies if t.category in {"Cache & Key-Value Store", "Cache"}), None)
        queue_tech = next((t.technology for t in technologies if t.category in {"Queue / Worker", "Message Broker"}), None)

        if db_tech or cache_tech or queue_tech or "worker" in comp_map:
            lines.append("    subgraph Infrastructure_Layer [Persistence & Infrastructure]")
            if db_tech:
                lines.append(f'        DB[("🗄️ Database [{db_tech}]")]:::db')
                lines.append(f"        {target_storage_caller} -->|SQL / ORM| DB")
            if cache_tech:
                lines.append(f'        Cache[("⚡ Cache [{cache_tech}]")]:::cache')
                lines.append(f"        Services -->|Fast Lookup| Cache")
            if queue_tech or "worker" in comp_map:
                q_label = queue_tech or "Async Queue"
                lines.append(f'        Queue["📬 {q_label}"]:::queue')
                lines.append('        Worker["👷 Async Worker Engine"]:::queue')
                lines.append("        Services -->|Enqueues Tasks| Queue")
                lines.append("        Queue -->|Processes Jobs| Worker")
                if db_tech:
                    lines.append("        Worker -->|Persists Results| DB")
            lines.append("    end")

        # 6. External Cloud Services Subgraph
        ext_techs = [t.technology for t in technologies if t.category in {"Cloud Infrastructure", "Payment Gateway", "AI & LLM Services", "External Communication"}]
        if ext_techs:
            lines.append("    subgraph External_APIs [Third-Party & Cloud Services]")
            ext_label = ", ".join(ext_techs[:3])
            lines.append(f'        Ext["☁️ External Services ({ext_label})"]:::external')
            lines.append("        Services -->|Integrates| Ext")
            lines.append("    end")

        return "\n".join(lines)
