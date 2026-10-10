"""
MineGuard AI - BFS Quantum Cascade Simulation Engine (Phase D3)
Simulates failure propagation across safety-critical mining systems when
cryptographic primitives are broken at Q-Day.

METHODOLOGY & RATIONALE:
- Why BFS? Cascade propagation follows dependency depth — each layer of dependencies
  is affected one discrete step later.
- Why hour += 2? Each BFS level represents a nominal 2-hour propagation and fault detection window.

LIMITATIONS:
- BFS treats all directed dependency edges uniformly without protocol timeout or retry weights.
- Real-world cascades depend on manual failover switches, isolation valves, and air-gap firewalls.
"""

from typing import List, Dict, Any, Optional, Set
import networkx as nx

from app.engines.graph_data import (
    MINING_NODES,
    MINING_EDGES,
    CRITICAL_NODES,
    SAFETY_NODES,
    CA_ROOT_ID,
)
from app.engines.graph_builder import GraphBuilder

DEFAULT_MIGRATED_NODES: List[str] = [
    "ca-root",
    "ot-gateway",
    "auth-svc"
]


class CascadeEngine:
    """
    Executes deterministic BFS cascade failure simulations across mining infrastructure.
    """

    def __init__(self, graph: Optional[nx.DiGraph] = None):
        self.builder = GraphBuilder()
        self.graph = graph if graph is not None else self.builder.build()

    def determine_seed_nodes(
        self,
        q_day: int,
        graph: Optional[nx.DiGraph] = None,
        migrated_nodes: Optional[Set[str] | List[str]] = None
    ) -> List[str]:
        """
        Identifies initial quantum-compromised seed nodes based on the target Q-Day horizon.
        - 2027-2028: RSA-2048 only
        - 2029-2030: RSA-2048 + ECDSA
        - 2031-2032: RSA-2048 + ECDSA + RSA-4096
        - 2033-2035: All asymmetric algorithms (RSA, ECDSA, DSA, DH)
        """
        g = graph or self.graph
        migrated = set(migrated_nodes or [])
        seed_nodes: List[str] = []

        for node_id, data in g.nodes(data=True):
            if node_id in migrated:
                continue

            algo = str(data.get("algorithm", "")).upper()

            # Rule progression by Q-Day
            compromised = False
            if q_day in {2027, 2028}:
                if "RSA-2048" in algo:
                    compromised = True
            elif q_day in {2029, 2030}:
                if "RSA-2048" in algo or "ECDSA" in algo:
                    compromised = True
            elif q_day in {2031, 2032}:
                if any(k in algo for k in ["RSA-2048", "ECDSA", "RSA-4096"]):
                    compromised = True
            elif q_day >= 2033:
                if any(k in algo for k in ["RSA", "ECDSA", "DSA", "DH"]):
                    compromised = True

            if compromised:
                seed_nodes.append(node_id)

        return sorted(seed_nodes)

    def run_cascade(
        self,
        q_day: int = 2029,
        migrated_nodes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes discrete BFS failure cascade starting from quantum-broken seed nodes.
        """
        g = self.graph
        migrated_set = set(migrated_nodes or [])
        seed = self.determine_seed_nodes(q_day, g, migrated_set)

        failed: Set[str] = set(seed)
        queue: List[str] = list(seed)

        timeline: List[Dict[str, Any]] = [
            {
                "hour": 0,
                "nodeId": s,
                "node_id": s,
                "node_label": g.nodes[s].get("label", s),
                "status": "FAILED",
                "reason": "Algorithm broken by quantum"
            }
            for s in seed
        ]

        hour = 0
        while queue:
            hour += 2
            level_size = len(queue)
            for _ in range(level_size):
                current = queue.pop(0)

                # Find all systems that depend on current: predecessor -> current
                for predecessor in g.predecessors(current):
                    if predecessor in failed:
                        continue
                    if predecessor in migrated_set:
                        continue

                    failed.add(predecessor)
                    queue.append(predecessor)
                    timeline.append({
                        "hour": hour,
                        "nodeId": predecessor,
                        "node_id": predecessor,
                        "node_label": g.nodes[predecessor].get("label", predecessor),
                        "status": "FAILED",
                        "reason": f"Cascade from {current}"
                    })

        sorted_failed = sorted(list(failed))
        critical_down = sum(1 for n in sorted_failed if n in CRITICAL_NODES or g.nodes[n].get("criticality") == "CRITICAL")
        total_down = len(sorted_failed)
        total_systems = len(g.nodes)
        survived = sorted([n for n in g.nodes if n not in failed])
        safety_impact = any(n in failed for n in SAFETY_NODES)

        return {
            "q_day": q_day,
            "seed_nodes": seed,
            "failed_nodes": sorted_failed,
            "failure_timeline": sorted(timeline, key=lambda x: (x["hour"], x["nodeId"])),
            "total_down": total_down,
            "total_systems": total_systems,
            "critical_down": critical_down,
            "safety_impact": safety_impact,
            "estimated_downtime_hours": total_down * 2,
            "estimated_cost_usd": critical_down * 500000 + total_down * 50000,
            "survived_nodes": survived,
            "migrated_nodes": sorted(list(migrated_set))
        }

    def run_cascade_comparison(self, q_day: int = 2029) -> Dict[str, Any]:
        """
        Runs dual cascade simulation: Baseline (unmitigated) vs Migrated (core roots secured).
        """
        left = self.run_cascade(q_day=q_day, migrated_nodes=[])
        right = self.run_cascade(q_day=q_day, migrated_nodes=DEFAULT_MIGRATED_NODES)

        return {
            "q_day": q_day,
            "left": left,
            "right": right
        }

    def run_what_if(self, q_day: int = 2029) -> Dict[str, Any]:
        """
        Executes cascade simulation across 4 progressive migration scenarios.
        """
        scenarios = [
            {
                "id": "scenario_1",
                "name": "No Migration (Baseline)",
                "description": "Zero post-quantum mitigations in place",
                "result": self.run_cascade(q_day, migrated_nodes=[])
            },
            {
                "id": "scenario_2",
                "name": "Phase 1: CA-Root",
                "description": "Root of Trust migrated to ML-DSA/ML-KEM",
                "result": self.run_cascade(q_day, migrated_nodes=["ca-root"])
            },
            {
                "id": "scenario_3",
                "name": "Phase 1 & 2: Core Infrastructure",
                "description": "CA-Root, OT-Gateway, and Auth-Svc migrated",
                "result": self.run_cascade(q_day, migrated_nodes=DEFAULT_MIGRATED_NODES)
            },
            {
                "id": "scenario_4",
                "name": "Full Migration",
                "description": "All critical and operational systems migrated",
                "result": self.run_cascade(
                    q_day,
                    migrated_nodes=[
                        "ca-root", "ot-gateway", "auth-svc", "ventilation",
                        "haulage", "dns-svc", "scada-historian", "gas-monitor",
                        "vpn-gateway", "finance"
                    ]
                )
            }
        ]

        return {
            "q_day": q_day,
            "scenarios": scenarios
        }
