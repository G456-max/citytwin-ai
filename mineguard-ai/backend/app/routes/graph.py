"""
MineGuard AI - Mining Dependency Graph Route (Phases D1, D2, D4, D6)
Provides network topology access, node-level centrality inspections,
and safety-critical trigger isolation.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import GraphFullResponse, NodeDetailResponse, GraphNode, GraphEdge
from app.engines.graph_data import MINING_NODES, MINING_EDGES, DISCLAIMER, CRITICAL_NODES
from app.engines.graph_builder import (
    GraphBuilder,
    get_nodes_as_dicts,
    get_edges_as_dicts,
    get_node_by_id,
)
from app.engines.centrality import CentralityAnalyzer

router = APIRouter(prefix="/graph", tags=["Dependency Graph"])

# Singleton builder and analyzer
graph_builder = GraphBuilder()
graph_instance = graph_builder.build()
centrality_analyzer = CentralityAnalyzer(graph=graph_instance)


@router.get("", response_model=GraphFullResponse)
async def get_graph():
    """
    Returns complete 20-node, 28-edge representative mining dependency network.
    """
    nodes = get_nodes_as_dicts(graph_instance)
    edges = get_edges_as_dicts(graph_instance)
    critical_count = sum(1 for n in nodes if n.get("criticality") == "CRITICAL")

    return GraphFullResponse(
        nodes=nodes,
        edges=edges,
        metadata={
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "critical_count": critical_count,
            "disclaimer": DISCLAIMER
        }
    )


@router.get("/node/{node_id}", response_model=NodeDetailResponse)
async def get_node_details(node_id: str):
    """
    Retrieves detailed topological metrics and cascade footprint for a specific system node.
    """
    node_data = get_node_by_id(graph_instance, node_id)
    if not node_data:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in topology graph")

    in_deg = graph_instance.in_degree(node_id)
    out_deg = graph_instance.out_degree(node_id)
    all_centralities = centrality_analyzer.compute_centrality(graph_instance)
    node_centrality = all_centralities.get(node_id, {})

    impact_info = centrality_analyzer.compute_cascade_impact(graph_instance, node_id=node_id, q_day=2029)

    return NodeDetailResponse(
        node=GraphNode(**node_data),
        in_degree=in_deg,
        out_degree=out_deg,
        centrality=node_centrality,
        cascade_impact=impact_info.get("cascade_impact", 0),
        is_cascade_trigger=impact_info.get("is_cascade_trigger", False)
    )


@router.get("/centrality")
async def get_centrality_metrics():
    """
    Returns full centrality breakdown (Degree, Betweenness, Closeness, PageRank) for all nodes.
    """
    metrics = centrality_analyzer.compute_centrality(graph_instance)
    return {
        "centrality": metrics,
        "total_nodes": len(metrics)
    }


@router.get("/triggers")
async def get_cascade_triggers():
    """
    Identifies high-centrality system nodes whose compromise amplifies downstream failure propagation.
    """
    triggers = centrality_analyzer.identify_cascade_triggers(graph_instance, q_day=2029)
    return {
        "triggers": triggers,
        "count": len(triggers)
    }


@router.get("/safety-critical")
async def get_safety_critical_nodes():
    """
    Returns all nodes critical to life safety, ventilation, gas monitoring, and mining operations.
    """
    safety_nodes = centrality_analyzer.identify_safety_critical_nodes(graph_instance)
    return {
        "safety_critical_nodes": safety_nodes,
        "count": len(safety_nodes)
    }
