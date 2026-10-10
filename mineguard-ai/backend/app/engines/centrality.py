"""
MineGuard AI - Centrality & Cascade Impact Analyzer (Phase D4)
Computes network graph centrality metrics (Degree, Betweenness, Closeness, PageRank)
and quantifies system-level failure propagation reduction.
"""

from typing import Dict, Any, List, Optional
import networkx as nx

from app.engines.graph_data import CRITICAL_NODES, SAFETY_NODES, CA_ROOT_ID
from app.engines.graph_builder import GraphBuilder
from app.engines.cascade import CascadeEngine


class CentralityAnalyzer:
    """
    Computes structural topological metrics and isolates cascade amplification points.
    """

    def __init__(self, graph: Optional[nx.DiGraph] = None):
        self.graph = graph if graph is not None else GraphBuilder().build()
        self.cascade_engine = CascadeEngine(graph=self.graph)

    def compute_centrality(self, graph: Optional[nx.DiGraph] = None) -> Dict[str, Dict[str, float]]:
        """
        Calculates In-Degree, Out-Degree, Total Degree, Betweenness, Closeness, and PageRank.
        """
        g = graph or self.graph

        in_deg = nx.in_degree_centrality(g)
        out_deg = nx.out_degree_centrality(g)
        deg = nx.degree_centrality(g)
        betweenness = nx.betweenness_centrality(g)
        closeness = nx.closeness_centrality(g)

        try:
            pagerank = nx.pagerank(g, alpha=0.85)
        except Exception:
            pagerank = {n: 1.0 / len(g.nodes) for n in g.nodes}

        results: Dict[str, Dict[str, float]] = {}
        for n in g.nodes:
            results[n] = {
                "in_degree": round(float(in_deg.get(n, 0.0)), 4),
                "out_degree": round(float(out_deg.get(n, 0.0)), 4),
                "degree": round(float(deg.get(n, 0.0)), 4),
                "betweenness": round(float(betweenness.get(n, 0.0)), 4),
                "closeness": round(float(closeness.get(n, 0.0)), 4),
                "pagerank": round(float(pagerank.get(n, 0.0)), 4)
            }

        return results

    def rank_by_cascade_impact(self, graph: Optional[nx.DiGraph] = None, q_day: int = 2029) -> List[Dict[str, Any]]:
        """
        Ranks every node by impact reduction: how many systems survive when this single node is migrated.
        """
        g = graph or self.graph
        engine = CascadeEngine(graph=g)
        baseline = engine.run_cascade(q_day=q_day, migrated_nodes=[])
        base_down = baseline["total_down"]

        ranked: List[Dict[str, Any]] = []

        for node_id in g.nodes:
            mitigated = engine.run_cascade(q_day=q_day, migrated_nodes=[node_id])
            reduction = max(0, base_down - mitigated["total_down"])

            ranked.append({
                "node_id": node_id,
                "label": g.nodes[node_id].get("label", node_id),
                "impact_reduction": reduction,
                "total_down_without": base_down,
                "total_down_with": mitigated["total_down"],
                "criticality": g.nodes[node_id].get("criticality", "MEDIUM"),
                "is_safety_critical": node_id in SAFETY_NODES
            })

        # Sort descending by impact reduction, then by criticality
        ranked.sort(key=lambda x: (x["impact_reduction"], 1 if x["criticality"] == "CRITICAL" else 0), reverse=True)
        return ranked

    def identify_cascade_triggers(self, graph: Optional[nx.DiGraph] = None, q_day: int = 2029) -> List[Dict[str, Any]]:
        """
        Identifies structural failure triggers (in_degree > 3 or downstream cascade reach > 5).
        """
        g = graph or self.graph
        triggers: List[Dict[str, Any]] = []

        for node_id in g.nodes:
            in_deg_raw = g.in_degree(node_id)
            # Find downstream dependents via BFS reach
            descendants = nx.descendants(g.reverse(), node_id)
            downstream_count = len(descendants)

            if in_deg_raw >= 3 or downstream_count >= 5 or node_id in {CA_ROOT_ID, "ot-gateway"}:
                triggers.append({
                    "node_id": node_id,
                    "label": g.nodes[node_id].get("label", node_id),
                    "in_degree": in_deg_raw,
                    "downstream_dependents_count": downstream_count,
                    "criticality": g.nodes[node_id].get("criticality", "MEDIUM"),
                    "algorithm": g.nodes[node_id].get("algorithm", "RSA-2048")
                })

        triggers.sort(key=lambda x: (x["in_degree"], x["downstream_dependents_count"]), reverse=True)
        return triggers

    def identify_safety_critical_nodes(self, graph: Optional[nx.DiGraph] = None) -> List[Dict[str, Any]]:
        """
        Returns all nodes marked as CRITICAL or designated in SAFETY_NODES.
        """
        g = graph or self.graph
        safety_nodes: List[Dict[str, Any]] = []

        for node_id, data in g.nodes(data=True):
            is_crit = data.get("criticality") == "CRITICAL"
            is_safety = node_id in SAFETY_NODES
            if is_crit or is_safety:
                entry = dict(data)
                entry["node_id"] = node_id
                entry["is_safety_node"] = is_safety
                safety_nodes.append(entry)

        return safety_nodes

    def compute_cascade_impact(self, graph: Optional[nx.DiGraph] = None, node_id: str = "", q_day: int = 2029) -> Dict[str, Any]:
        """
        Calculates individual cascade footprint and survivability gain for a specific node.
        """
        g = graph or self.graph
        if node_id not in g.nodes:
            return {}

        engine = CascadeEngine(graph=g)
        baseline = engine.run_cascade(q_day=q_day, migrated_nodes=[])
        mitigated = engine.run_cascade(q_day=q_day, migrated_nodes=[node_id])
        reduction = max(0, baseline["total_down"] - mitigated["total_down"])

        in_deg = g.in_degree(node_id)
        descendants = nx.descendants(g.reverse(), node_id)

        return {
            "node_id": node_id,
            "label": g.nodes[node_id].get("label", node_id),
            "cascade_impact": len(descendants),
            "reduction": reduction,
            "criticality": g.nodes[node_id].get("criticality", "MEDIUM"),
            "is_cascade_trigger": in_deg >= 4 or len(descendants) >= 5,
            "is_safety_critical": node_id in SAFETY_NODES or g.nodes[node_id].get("criticality") == "CRITICAL"
        }
