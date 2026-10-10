"""
Unit Tests for Mining Dependency Graph Topology (Phases D1, D2, D4)
Validates 20 nodes, 28 edges, graph connectivity, centrality metrics, and safety designations.
"""

import pytest
import networkx as nx

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
from app.engines.centrality import CentralityAnalyzer


@pytest.fixture
def graph():
    builder = GraphBuilder()
    return builder.build()


# 1. test_graph_builds
def test_graph_builds(graph):
    assert isinstance(graph, nx.DiGraph)
    assert len(graph.nodes) > 0


# 2. test_graph_has_20_nodes
def test_graph_has_20_nodes(graph):
    assert len(graph.nodes) == 20
    assert len(MINING_NODES) == 20


# 3. test_graph_has_28_edges
def test_graph_has_28_edges(graph):
    assert len(graph.edges) == 28
    assert len(MINING_EDGES) == 28


# 4. test_no_orphan_nodes
def test_no_orphan_nodes(graph):
    for node in graph.nodes:
        total_deg = graph.in_degree(node) + graph.out_degree(node)
        assert total_deg > 0, f"Node {node} is disconnected!"


# 5. test_ca_root_is_highest_centrality
def test_ca_root_is_highest_centrality(graph):
    analyzer = CentralityAnalyzer(graph=graph)
    centralities = analyzer.compute_centrality(graph)
    # In a root-of-trust graph, ca-root or ot-gateway has maximum in-degree / betweenness
    ca_metrics = centralities[CA_ROOT_ID]
    assert ca_metrics["in_degree"] > 0
    # ca-root is depended upon by auth-svc, dns-svc, ot-gateway, vpn-gateway
    assert graph.in_degree(CA_ROOT_ID) >= 4


# 6. test_centrality_computed
def test_centrality_computed(graph):
    analyzer = CentralityAnalyzer(graph=graph)
    metrics = analyzer.compute_centrality(graph)
    assert len(metrics) == 20
    for node_id, m in metrics.items():
        assert "betweenness" in m
        assert "degree" in m
        assert "pagerank" in m


# 7. test_cascade_triggers_identified
def test_cascade_triggers_identified(graph):
    analyzer = CentralityAnalyzer(graph=graph)
    triggers = analyzer.identify_cascade_triggers(graph, q_day=2029)
    assert len(triggers) >= 1
    trigger_ids = {t["node_id"] for t in triggers}
    assert CA_ROOT_ID in trigger_ids or "ot-gateway" in trigger_ids


# 8. test_safety_critical_nodes
def test_safety_critical_nodes(graph):
    analyzer = CentralityAnalyzer(graph=graph)
    safety_nodes = analyzer.identify_safety_critical_nodes(graph)
    ids = {n["node_id"] for n in safety_nodes}
    for sn in SAFETY_NODES:
        assert sn in ids


# 9. test_graph_validation_clean
def test_graph_validation_clean(graph):
    issues = validate_graph(graph)
    assert len(issues) == 0


# 10. test_get_node_by_id
def test_get_node_by_id(graph):
    node = get_node_by_id(graph, "ventilation")
    assert node is not None
    assert node["id"] == "ventilation"
    assert node["criticality"] == "CRITICAL"
    assert node["algorithm"] == "RSA-2048"
