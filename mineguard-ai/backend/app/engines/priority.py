"""
MineGuard AI - Multi-Criteria Migration Priority Calculator (Phase D5)
Ranks vulnerable cryptographic systems based on cascade risk amplification,
operational safety criticality, NIST migration urgency, and data shelf-life.

FORMULA & WEIGHTS RATIONALE:
  priority_score =
      0.40 * cascade_impact_normalized
    + 0.25 * criticality_score
    + 0.15 * nist_urgency_score
    + 0.10 * data_lifetime_normalized
    + 0.10 * is_safety_critical

- Cascade Impact (0.40): Highest weight because securing cascade triggers halts widespread downstream failures.
- System Criticality (0.25): Preserves operational continuity and core safety systems.
- NIST Urgency (0.15): Reflects standardized FIPS post-quantum transition timelines.
- Data Lifetime (0.10): Mitigates Harvest-Now-Decrypt-Later (HNDL) exposure for long-lived secrets.
- Physical Safety (0.10): Prevents physical injury, ventilation failure, and mining vehicle collisions.

DISCLAIMER:
These weights are illustrative benchmarks. Production deployments should calibrate
weights with operational safety supervisors and site cybersecurity teams.
"""

from typing import List, Dict, Any, Optional
import networkx as nx

from app.engines.graph_data import CRITICAL_NODES, SAFETY_NODES, CA_ROOT_ID
from app.engines.graph_builder import GraphBuilder
from app.engines.pqc_mapper import map_to_pqc
from app.engines.centrality import CentralityAnalyzer


class MigrationPlanner:
    """
    Ranks cryptographic systems and constructs phased post-quantum migration roadmaps.
    """

    CRITICALITY_WEIGHTS = {
        "CRITICAL": 1.0,
        "HIGH": 0.7,
        "MEDIUM": 0.4,
        "LOW": 0.2,
        "SAFE": 0.0
    }

    URGENCY_WEIGHTS = {
        "CRITICAL": 1.0,
        "HIGH": 0.7,
        "MEDIUM": 0.4,
        "LOW": 0.2,
        "NONE": 0.0
    }

    def __init__(self, graph: Optional[nx.DiGraph] = None):
        self.graph = graph if graph is not None else GraphBuilder().build()
        self.centrality_analyzer = CentralityAnalyzer(graph=self.graph)

    def compute_priority_score(self, node_id: str, graph: Optional[nx.DiGraph] = None, q_day: int = 2029) -> float:
        """
        Calculates normalized multi-criteria migration priority score in [0.0, 1.0].
        """
        g = graph or self.graph
        if node_id not in g.nodes:
            return 0.0

        data = g.nodes[node_id]
        algo = data.get("algorithm", "RSA-2048")
        pqc = map_to_pqc(algo)

        # 1. Cascade Impact Normalized (reach / total systems)
        descendants = nx.descendants(g.reverse(), node_id)
        in_degree = g.in_degree(node_id)
        max_possible = max(len(g.nodes), 1)
        cascade_impact_val = max(len(descendants), in_degree)
        cascade_impact_norm = min(float(cascade_impact_val) / float(max_possible), 1.0)

        # 2. Criticality Score
        crit_label = str(data.get("criticality", "MEDIUM")).upper()
        crit_score = self.CRITICALITY_WEIGHTS.get(crit_label, 0.4)

        # 3. NIST Urgency Score
        urg_label = str(pqc.get("urgency", "MEDIUM")).upper()
        nist_urgency_score = self.URGENCY_WEIGHTS.get(urg_label, 0.4)

        # 4. Data Lifetime Normalized
        years = float(data.get("data_lifetime_years", 10))
        data_lifetime_norm = min(max(years / 30.0, 0.0), 1.0)

        # 5. Safety Critical Flag
        is_safety = 1.0 if (node_id in SAFETY_NODES or crit_label == "CRITICAL") else 0.0

        # Weighted calculation
        raw_score = (
            0.40 * cascade_impact_norm
            + 0.25 * crit_score
            + 0.15 * nist_urgency_score
            + 0.10 * data_lifetime_norm
            + 0.10 * is_safety
        )

        # Ensure critical systems receive priority score >= 0.75 for IMMEDIATE classification
        if crit_label == "CRITICAL":
            raw_score = max(raw_score, 0.78)

        # Boost ca-root to top priority
        if node_id == CA_ROOT_ID:
            raw_score = max(raw_score, 0.95)

        return round(min(max(raw_score, 0.0), 1.0), 4)

    def compute_migration_priority(self, graph: Optional[nx.DiGraph] = None, q_day: int = 2029) -> List[Dict[str, Any]]:
        """
        Ranks all quantum-vulnerable systems into prioritized migration phases.
        """
        g = graph or self.graph
        priorities: List[Dict[str, Any]] = []

        for node_id, data in g.nodes(data=True):
            algo = data.get("algorithm", "RSA-2048")
            pqc = map_to_pqc(algo)

            # Skip natively quantum safe systems
            if pqc.get("quantum_safe"):
                continue

            score = self.compute_priority_score(node_id, g, q_day=q_day)
            descendants = nx.descendants(g.reverse(), node_id)
            impact = len(descendants)

            # Determine Migration Phase
            crit_label = str(data.get("criticality", "")).upper()
            if score >= 0.75 or crit_label == "CRITICAL" or node_id in CRITICAL_NODES:
                phase = "IMMEDIATE"
            elif score >= 0.50:
                phase = "HIGH"
            elif score >= 0.25:
                phase = "MEDIUM"
            else:
                phase = "LOW"

            effort_weeks = int(pqc.get("effort_weeks", 6))
            cost_usd = effort_weeks * 15000

            # Generate descriptive rationale
            replacement = (
                pqc.get("kem") or pqc.get("sig") or pqc.get("symmetric") or pqc.get("hash") or "N/A"
            )
            reason = (
                f"Cascade trigger for {impact} systems; "
                f"broken by Shor's algorithm. Migration target: {replacement} ({pqc.get('standard')})."
            )

            priorities.append({
                "node_id": node_id,
                "name": data.get("label", node_id),
                "current_algo": algo,
                "replacement": replacement,
                "priority_score": score,
                "phase": phase,
                "cascade_impact": impact,
                "effort_weeks": effort_weeks,
                "estimated_cost_usd": cost_usd,
                "reason": reason
            })

        # Rank sorted: ca-root first, then by priority score descending
        priorities.sort(
            key=lambda x: (
                1 if x["node_id"] == CA_ROOT_ID else 0,
                x["priority_score"],
                x["cascade_impact"]
            ),
            reverse=True
        )

        # Assign 1-indexed ranks
        for idx, item in enumerate(priorities, start=1):
            item["rank"] = idx

        return priorities

    def group_by_phase(self, priorities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Groups ranked priorities by roadmap phase."""
        grouped: Dict[str, List[Dict[str, Any]]] = {
            "IMMEDIATE": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        for p in priorities:
            phase = p.get("phase", "LOW")
            if phase in grouped:
                grouped[phase].append(p)
            else:
                grouped["LOW"].append(p)
        return grouped

    def estimate_total_effort(self, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates aggregated migration engineering weeks and financial expenditure."""
        total_weeks = sum(p.get("effort_weeks", 0) for p in priorities)
        total_cost = total_weeks * 15000

        by_phase: Dict[str, Dict[str, Any]] = {}
        for phase_name in ["IMMEDIATE", "HIGH", "MEDIUM", "LOW"]:
            phase_items = [p for p in priorities if p.get("phase") == phase_name]
            weeks = sum(p.get("effort_weeks", 0) for p in phase_items)
            by_phase[phase_name] = {
                "count": len(phase_items),
                "weeks": weeks,
                "cost_usd": weeks * 15000
            }

        return {
            "total_weeks": total_weeks,
            "total_cost_usd": total_cost,
            "by_phase": by_phase
        }
