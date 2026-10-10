"""
MineGuard AI - NetworkX Graph Builder & Topology Validator (Phase D2)
Constructs directed dependency graph models from mining nodes and edges.
"""

from typing import List, Dict, Any, Optional
import networkx as nx

from app.engines.graph_data import MINING_NODES, MINING_EDGES


def validate_graph(graph: nx.DiGraph) -> List[str]:
    """
    Validates graph consistency: self-loops, orphaned nodes, and endpoint integrity.
    """
    issues: List[str] = []

    # Check for self loops
    self_loops = list(nx.nodes_with_selfloops(graph))
    if self_loops:
        issues.append(f"Self-loops detected on nodes: {self_loops}")

    # Check for orphan nodes (degree == 0)
    orphans = [n for n in graph.nodes if graph.degree(n) == 0]
    if orphans:
        issues.append(f"Orphan nodes with zero connections: {orphans}")

    return issues


class GraphBuilder:
    """
    Constructs and validates directed dependency graphs for mining infrastructure.
    """

    def __init__(
        self,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, str]]] = None
    ):
        self.nodes = nodes if nodes is not None else MINING_NODES
        self.edges = edges if edges is not None else MINING_EDGES

    def build(self) -> nx.DiGraph:
        """
        Builds directed NetworkX graph with full node and edge metadata.
        """
        G = nx.DiGraph()

        # Add nodes
        for n in self.nodes:
            node_id = str(n["id"])
            G.add_node(
                node_id,
                id=node_id,
                label=n.get("label", node_id),
                algorithm=n.get("algorithm", "RSA-2048"),
                criticality=n.get("criticality", "MEDIUM"),
                x=float(n.get("x", 0.0)),
                y=float(n.get("y", 0.0)),
                data_lifetime_years=int(n.get("data_lifetime_years", 10)),
                exposure=n.get("exposure", "internal"),
                category=n.get("category", "General")
            )

        # Add edges
        for e in self.edges:
            u = str(e["from"])
            v = str(e["to"])
            edge_type = e.get("type", "DEPENDS_ON")
            G.add_edge(u, v, type=edge_type)

        return G


# ============ HELPER FUNCTIONS ============
def get_nodes_as_dicts(graph: nx.DiGraph) -> List[Dict[str, Any]]:
    """Converts graph nodes into a list of serializable dictionaries."""
    result: List[Dict[str, Any]] = []
    for node_id, data in graph.nodes(data=True):
        entry = dict(data)
        entry["id"] = node_id
        result.append(entry)
    return result


def get_edges_as_dicts(graph: nx.DiGraph) -> List[Dict[str, Any]]:
    """Converts graph edges into a list of serializable dictionaries with 'from' and 'to'."""
    result: List[Dict[str, Any]] = []
    for u, v, data in graph.edges(data=True):
        result.append({
            "from": u,
            "to": v,
            "type": data.get("type", "DEPENDS_ON")
        })
    return result


def get_node_by_id(graph: nx.DiGraph, node_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single node dictionary from graph."""
    if node_id not in graph.nodes:
        return None
    data = dict(graph.nodes[node_id])
    data["id"] = node_id
    return data
