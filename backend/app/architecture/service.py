from typing import Dict, Any, Optional
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.architecture.model import ArchitectureModel
from backend.app.architecture.scanner import FileStructureScanner
from backend.app.architecture.detector import TechnologyDetector, PatternDetector
from backend.app.architecture.graph import DependencyGraphBuilder
from backend.app.architecture.risk import ArchitectureRiskEngine
from backend.app.architecture.diagram import MermaidDiagramGenerator
from backend.app.ai.architecture_agent import ArchitectureAgent

class ArchitectureService:
    """
    Central orchestration service for Architecture Intelligence.
    Consumes RepositoryContext and produces a comprehensive ArchitectureModel.
    """

    @staticmethod
    async def analyze(
        ctx: RepositoryContext,
        llm_provider: Optional[str] = "offline",
        api_key: Optional[str] = None
    ) -> ArchitectureModel:
        # 1. Scan file tree & directory roles
        scan_result = FileStructureScanner.scan(ctx)

        # 2. Detect evidence-backed technologies & frameworks
        technologies = TechnologyDetector.detect_technologies(ctx, scan_result)

        # 3. Detect architecture pattern (Primary + Characteristics)
        pattern = PatternDetector.detect_pattern(ctx, scan_result, technologies)

        # 4. Build AST & Static Dependency Graph
        components, dependencies, adjacency, reverse_adjacency, node_metadata = (
            DependencyGraphBuilder.build_graph(ctx, scan_result)
        )

        # 5. Analyze Risks, Layer Violations, Blast Radius, and Strengths
        risks, layer_violations, blast_radii, strengths = (
            ArchitectureRiskEngine.analyze_risks(
                ctx=ctx,
                components=components,
                adjacency=adjacency,
                reverse_adjacency=reverse_adjacency,
                node_metadata=node_metadata,
                technologies=technologies,
            )
        )

        # 6. Generate Dynamic Mermaid Diagram
        diagram = MermaidDiagramGenerator.generate(
            components=components,
            dependencies=dependencies,
            technologies=technologies,
            pattern_name=pattern.primary,
        )

        # 7. Calculate Architecture Score (0-100)
        score = 88.0
        if len(strengths) >= 2:
            score += 6.0
        if len(risks) > 0:
            score -= min(25.0, len(risks) * 5.0)
        if len(layer_violations) > 0:
            score -= min(15.0, len(layer_violations) * 6.0)
        score = max(25.0, min(100.0, score))

        # 8. External Services list
        ext_services = [t.technology for t in technologies if t.category in {"Cloud Infrastructure", "Payment Gateway", "AI & LLM Services", "External Communication"}]

        # Intermediate Model
        model = ArchitectureModel(
            pattern=pattern,
            technologies=technologies,
            components=components,
            dependencies=dependencies,
            risks=risks,
            layer_violations=layer_violations,
            blast_radius=blast_radii,
            strengths=strengths,
            entry_points=scan_result.get("entry_points", []),
            external_services=ext_services,
            diagram=diagram,
            score=round(score, 1),
            metrics={
                "total_modules": len(node_metadata),
                "total_dependencies": len(dependencies),
                "total_components": len(components),
                "total_risks": len(risks),
                "total_layer_violations": len(layer_violations),
            }
        )

        # 9. Synthesize AI Architecture Explanation
        explanation = await ArchitectureAgent.explain(
            model=model,
            repo_info={"owner": ctx.owner, "name": ctx.name, "url": ctx.url},
            provider_name=llm_provider,
            api_key=api_key
        )
        model.explanation = explanation

        return model
