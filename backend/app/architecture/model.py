from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TechnologyEvidence(BaseModel):
    technology: str
    category: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    version: Optional[str] = None

class Component(BaseModel):
    name: str
    type: str  # controller, service, repository, model, middleware, worker, database, cache, queue, config, ui
    layer: str  # presentation, business, data_access, persistence, infrastructure, util
    files: List[str] = Field(default_factory=list)
    file_count: int = 0
    loc: int = 0
    description: str = ""
    technology: Optional[str] = None

class Dependency(BaseModel):
    source: str
    target: str
    type: str = "import"  # import, rpc, api, db_query, event
    weight: int = 1

class ArchitecturePattern(BaseModel):
    primary: str
    confidence: float = 0.90
    description: str = ""
    characteristics: List[str] = Field(default_factory=list)

class ArchitectureRisk(BaseModel):
    rule_id: str
    severity: str  # Critical, High, Medium, Low
    type: str  # Circular Dependency, High Coupling, Layer Violation, God Module, Flat Root
    title: str
    description: str
    mitigation: str
    evidence: str = ""
    file_path: str = ""

class LayerViolation(BaseModel):
    source_layer: str
    target_layer: str
    source_file: str
    target_file: str
    description: str
    severity: str = "High"

class BlastRadius(BaseModel):
    target_module: str
    affected_modules: List[str] = Field(default_factory=list)
    affected_endpoints: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    total_impact_score: int = 0

class ArchitectureStrength(BaseModel):
    title: str
    description: str
    badge: str

class ArchitectureModel(BaseModel):
    pattern: ArchitecturePattern
    technologies: List[TechnologyEvidence] = Field(default_factory=list)
    components: List[Component] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    risks: List[ArchitectureRisk] = Field(default_factory=list)
    layer_violations: List[LayerViolation] = Field(default_factory=list)
    blast_radius: List[BlastRadius] = Field(default_factory=list)
    strengths: List[ArchitectureStrength] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    external_services: List[str] = Field(default_factory=list)
    diagram: str = ""
    explanation: str = ""
    score: float = 85.0
    metrics: Dict[str, Any] = Field(default_factory=dict)
