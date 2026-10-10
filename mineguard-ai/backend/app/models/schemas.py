from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ HEALTH ============
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


# ============ PQC MAPPING & ENRICHMENT ============
class PQCMapping(BaseModel):
    algorithm: str
    normalized: str
    mapped: bool
    kem: Optional[str] = None
    sig: Optional[str] = None
    alt_sig: Optional[str] = None
    hash: Optional[str] = None
    symmetric: Optional[str] = None
    standard: str
    complexity: str
    effort_weeks: int
    reason: str
    urgency: str
    quantum_safe: bool


class Finding(BaseModel):
    file: str
    line: int
    algorithm: str
    severity: str
    context: Optional[str] = None
    key_size: Optional[int] = None
    pqc: Optional[PQCMapping] = None


class EnrichedFinding(Finding):
    pass


class MigrationSummary(BaseModel):
    total_findings: int
    quantum_safe: int
    quantum_vulnerable: int
    total_effort_weeks: int
    by_standard: Dict[str, int] = Field(default_factory=dict)
    by_urgency: Dict[str, int] = Field(default_factory=dict)


# ============ SCAN & PROJECT ============
class ScanRequest(BaseModel):
    project_path: str = Field(..., description="Path to project to scan")
    scan_type: str = Field("source", description="source | config | dependencies")


class ScanResponse(BaseModel):
    findings: List[EnrichedFinding]
    count: int
    source: str = "simulation"
    scan_time_ms: int = 0
    summary: Optional[MigrationSummary] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    path: str
    scan_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ CBOM ============
class CBOMIngestRequest(BaseModel):
    cbom_path: str = Field(..., description="Path to CycloneDX CBOM JSON file")


class CBOMIngestResponse(BaseModel):
    findings: List[EnrichedFinding]
    count: int
    source: str = "cbom"
    summary: MigrationSummary
    cbom_metadata: Dict[str, Any] = Field(default_factory=dict)


# ============ RISK ============
class RiskRequest(BaseModel):
    findings: List[Finding]


class RiskResponse(BaseModel):
    score: int
    severity: str
    mosca_exposed: bool
    mosca_gap: int
    breakdown: Dict[str, Any] = Field(default_factory=dict)


# ============ GRAPH ============
class Node(BaseModel):
    id: str
    label: str
    algorithm: str
    criticality: str
    x: float
    y: float
    data_lifetime_years: int = 10
    exposure: str = "internal"
    category: Optional[str] = "General"


class GraphNode(Node):
    pass


class Edge(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    type: str = "DEPENDS_ON"

    class Config:
        populate_by_name = True


class GraphEdge(Edge):
    pass


class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class GraphFullResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any]


class NodeDetailResponse(BaseModel):
    node: GraphNode
    in_degree: int
    out_degree: int
    centrality: Dict[str, float]
    cascade_impact: int
    is_cascade_trigger: bool


# ============ CASCADE ============
class CascadeRequest(BaseModel):
    q_day: int = Field(2029, ge=2027, le=2035)
    migrated_nodes: List[str] = Field(default_factory=list)


class CascadeTimelineEntry(BaseModel):
    hour: int
    node_id: str
    node_label: str
    status: str
    reason: str


class CascadeResponse(BaseModel):
    q_day: int
    failed_nodes: List[str]
    failure_timeline: List[Dict[str, Any]]
    total_down: int
    total_systems: int


class CascadeFullResponse(BaseModel):
    q_day: int
    seed_nodes: List[str]
    failed_nodes: List[str]
    failure_timeline: List[Dict[str, Any]]
    total_down: int
    total_systems: int
    critical_down: int
    safety_impact: bool
    estimated_downtime_hours: int
    estimated_cost_usd: int
    survived_nodes: List[str]


class CascadeComparisonResponse(BaseModel):
    q_day: int
    left: Dict[str, Any]
    right: Dict[str, Any]


# ============ PRIORITY ============
class PriorityItem(BaseModel):
    rank: int
    node_id: str
    name: str
    action: str
    reason: str
    effort: str


class PriorityResponse(BaseModel):
    priorities: List[PriorityItem]


class PriorityScore(BaseModel):
    rank: int
    node_id: str
    name: str
    current_algo: str
    replacement: str
    priority_score: float
    phase: str
    cascade_impact: int
    effort_weeks: int
    estimated_cost_usd: int
    reason: str


class PriorityListResponse(BaseModel):
    q_day: int
    priorities: List[PriorityScore]
    total_weeks: int
    total_cost_usd: int


# ============ PLAN ============
class PlanRequest(BaseModel):
    budget_usd: int = 500000
    max_downtime_hours: int = 24
    deadline_weeks: int = 52
    priorities: List[PriorityItem] = Field(default_factory=list)


class PlanResponse(BaseModel):
    phases: List[Dict[str, Any]]
    total_cost_usd: int
    total_weeks: int
    feasible: bool


# ============ EXPLAIN ============
class CitationModel(BaseModel):
    title: str
    url: str
    category: str
    year: int
    relevance: float
    excerpt: str
    verified: bool = True


class GuardrailResultModel(BaseModel):
    passed: bool
    flags: List[str] = Field(default_factory=list)
    confidence: str
    reason: str


class FindingExplainItem(BaseModel):
    file: str = "unknown"
    line: int = 0
    algorithm: str
    severity: str = "MEDIUM"
    replacement: Optional[str] = None
    score: Optional[float] = None
    risk_score: Optional[float] = None
    standard: Optional[str] = None


class ExplainFindingRequest(BaseModel):
    finding: FindingExplainItem
    question: Optional[str] = "Explain this finding and migration path"


class ExplainCascadeRequest(BaseModel):
    q_day: str = "2029-2030"
    total_down: int = 10
    total_systems: int = 20
    critical_down: int = 4
    safety_impact: str = "Critical operational disruption to haulage and ventilation"
    question: Optional[str] = "Explain why this cascade occurs and what it means for mining safety"


class ExplainCompareRequest(BaseModel):
    current_algorithm: str = "RSA-2048"
    recommended_algorithm: str = "ML-DSA-65"
    standard: Optional[str] = "NIST FIPS 204"
    question: Optional[str] = "Why is the recommended algorithm safer?"


class ExplainFreeRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class ExplainFullResponse(BaseModel):
    answer: str
    sources: List[CitationModel] = Field(default_factory=list)
    guardrails: GuardrailResultModel
    model: str
    duration_ms: int


class ExplainRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class ExplainResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: str = "medium"
