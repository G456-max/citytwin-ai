"""
MineGuard AI - Engines Package
Exports cryptographic scanning, NIST PQC mapping, CycloneDX CBOM,
dependency graph topology, BFS cascade simulation, centrality, and migration planning engines.
"""

from app.engines.scanner import (
    CryptoScanner,
    scan_project,
    QUANTUM_VULNERABLE,
    SCANNABLE_EXTENSIONS,
    SKIP_DIRS,
)
from app.engines.pqc_mapper import (
    PQCStandard,
    MigrationComplexity,
    PQC_MAPPING,
    normalize_algorithm,
    map_to_pqc,
    enrich_findings,
    get_migration_summary,
)
from app.engines.cbom_parser import (
    CBOMIngester,
    CBOMGenerator,
    ingest_cbom,
    generate_cbom,
)
from app.engines.graph_data import (
    MINING_NODES,
    MINING_EDGES,
    CA_ROOT_ID,
    CRITICAL_NODES,
    SAFETY_NODES,
    DISCLAIMER,
)
from app.engines.graph_builder import (
    GraphBuilder,
    validate_graph,
    get_nodes_as_dicts,
    get_edges_as_dicts,
    get_node_by_id,
)
from app.engines.cascade import (
    CascadeEngine,
    DEFAULT_MIGRATED_NODES,
)
from app.engines.centrality import (
    CentralityAnalyzer,
)
from app.engines.priority import (
    MigrationPlanner,
)

__all__ = [
    # Scanner (Phase B1)
    "CryptoScanner",
    "scan_project",
    "QUANTUM_VULNERABLE",
    "SCANNABLE_EXTENSIONS",
    "SKIP_DIRS",
    # PQC Mapper (Phase B2)
    "PQCStandard",
    "MigrationComplexity",
    "PQC_MAPPING",
    "normalize_algorithm",
    "map_to_pqc",
    "enrich_findings",
    "get_migration_summary",
    # CBOM (Phase B2)
    "CBOMIngester",
    "CBOMGenerator",
    "ingest_cbom",
    "generate_cbom",
    # Graph Topology (Phase D1, D2)
    "MINING_NODES",
    "MINING_EDGES",
    "CA_ROOT_ID",
    "CRITICAL_NODES",
    "SAFETY_NODES",
    "DISCLAIMER",
    "GraphBuilder",
    "validate_graph",
    "get_nodes_as_dicts",
    "get_edges_as_dicts",
    "get_node_by_id",
    # Cascade Simulation (Phase D3)
    "CascadeEngine",
    "DEFAULT_MIGRATED_NODES",
    # Centrality & Impact (Phase D4)
    "CentralityAnalyzer",
    # Migration Planner (Phase D5)
    "MigrationPlanner",
]
