from typing import Dict, Any, Optional
from backend.app.architecture.model import ArchitectureModel
from backend.app.services.llm.provider import get_llm_provider, OfflineLLMProvider

class ArchitectureAgent:
    """
    Synthesizes natural language architectural explanations strictly grounded
    in the detected ArchitectureModel (patterns, components, dependencies, risks, blast radius).
    """

    @staticmethod
    async def explain(
        model: ArchitectureModel,
        repo_info: Dict[str, Any],
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> str:
        llm = get_llm_provider(provider_name, api_key)
        
        # If offline or fallback, use deterministic high-fidelity synthesis
        if isinstance(llm, OfflineLLMProvider):
            return ArchitectureAgent._synthesize_offline(model, repo_info)

        # Grounded prompt for online LLM
        prompt = (
            f"You are a Principal Enterprise Software Architect auditing {repo_info.get('owner')}/{repo_info.get('name')}.\n\n"
            f"Ground-Truth Architecture Model:\n"
            f"- Pattern: {model.pattern.primary} (Confidence: {int(model.pattern.confidence * 100)}%)\n"
            f"- Characteristics: {', '.join(model.pattern.characteristics)}\n"
            f"- Technologies: {', '.join(t.technology for t in model.technologies)}\n"
            f"- Components: {', '.join(f'{c.name} ({c.file_count} files)' for c in model.components)}\n"
            f"- Identified Risks ({len(model.risks)}): {', '.join(r.title for r in model.risks[:3])}\n"
            f"- Layer Violations ({len(model.layer_violations)}): {', '.join(v.description for v in model.layer_violations[:2])}\n"
            f"- Blast Radius Targets: {len(model.blast_radius)} modules analyzed\n\n"
            f"Write an authoritative 3-part markdown report:\n"
            f"1. **Architecture & Topology**: Pattern classification and component roles.\n"
            f"2. **Request Lifecycle Flow**: Step-by-step traversal from client to persistence.\n"
            f"3. **Architectural Health & Risks**: Clear analysis of risks, layer violations, and strengths."
        )

        try:
            explanation = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                context=f"Architecture Model: {model.model_dump_json()[:2000]}"
            )
            if explanation and len(explanation.strip()) > 50:
                return explanation
        except Exception:
            pass

        return ArchitectureAgent._synthesize_offline(model, repo_info)

    @staticmethod
    def _synthesize_offline(model: ArchitectureModel, repo_info: Dict[str, Any]) -> str:
        paragraphs = []

        # 1. Pattern & Overview
        chars_str = "\n".join(f"- {c}" for c in model.pattern.characteristics)
        paragraphs.append(
            f"### Architecture: {model.pattern.primary} (Confidence: {int(model.pattern.confidence * 100)}%)\n\n"
            f"The repository **{repo_info.get('owner', 'repo')}/{repo_info.get('name', 'project')}** is structured as a **{model.pattern.primary}**. "
            f"{model.pattern.description}\n\n"
            f"**Key Architectural Characteristics**:\n{chars_str}"
        )

        # 2. Request Lifecycle & Flow
        comp_names = [c.name for c in model.components if c.type in {"controller", "service", "repository", "database", "ui"}]
        flow_chain = " ➔ ".join(f"**{name}**" for name in comp_names)
        
        paragraphs.append(
            f"#### 🔄 Request Lifecycle & Component Traversal\n"
            f"Client requests traverse the system hierarchy: {flow_chain or '**Presentation** ➔ **Business Logic** ➔ **Data Access**'}.\n\n"
            + "\n".join(f"1. **{c.name}** (`{c.type}`): {c.description} ({c.file_count} source files, {c.loc:,} LOC)" for c in model.components[:5])
        )

        # 3. Technologies & Infrastructure
        tech_str = ", ".join(f"**{t.technology}** ({t.category})" for t in model.technologies[:6])
        paragraphs.append(
            f"#### 🛠️ Technology Stack & Infrastructure\n"
            f"The application leverages {tech_str}. "
            f"Entry points include {', '.join(f'`{ep}`' for ep in model.entry_points[:3]) or 'standard framework defaults'}."
        )

        # 4. Architectural Risks & Violations
        if model.risks or model.layer_violations:
            risk_bullets = []
            for r in model.risks[:3]:
                risk_bullets.append(f"- ⚠️ **[{r.severity}] {r.title}**: {r.description}")
            for v in model.layer_violations[:2]:
                risk_bullets.append(f"- 🚨 **Layer Violation**: {v.description}")
            paragraphs.append(
                f"#### ⚠️ Identified Architectural Risks\n"
                + "\n".join(risk_bullets)
            )
        else:
            paragraphs.append(
                "#### ✅ Architectural Health & Boundary Integrity\n"
                "The repository adheres to strict layer boundaries with zero circular dependencies or leaky abstractions detected."
            )

        return "\n\n".join(paragraphs)
