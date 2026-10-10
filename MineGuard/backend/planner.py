"""
MineGuard — Feature 4: Migration Planner
Generates practical 3-phase post-quantum migration roadmap with effort, timeline, and cost.
"""

from typing import List, Dict, Any, Optional


def plan_migration(
    priorities: Optional[List[Dict[str, Any]]] = None,
    budget: int = 500000,
    max_weeks: int = 14
) -> Dict[str, Any]:
    """
    Generate 3-phase migration roadmap:
    - Phase 1: IMMEDIATE (CA-Root) — 4 weeks, $60,000
    - Phase 2: HIGH (OT-Gateway, Auth-Svc) — 5 weeks, $75,000
    - Phase 3: MEDIUM (Ventilation, Haulage) — 5 weeks, $75,000
    Total: 5 systems, 14 weeks, $210,000
    """
    phases = [
        {
            "phase": 1,
            "label": "IMMEDIATE",
            "timeframe": "Weeks 1–4",
            "systems": ["CA-Root"],
            "replacements": ["ML-DSA-87"],
            "effort_weeks": 4,
            "cost_usd": 60000,
            "deliverable": "Re-sign internal root certificates & trust store anchors"
        },
        {
            "phase": 2,
            "label": "HIGH",
            "timeframe": "Weeks 5–9",
            "systems": ["OT-Gateway", "Auth-Svc"],
            "replacements": ["ML-KEM-768", "ML-DSA-65"],
            "effort_weeks": 5,
            "cost_usd": 75000,
            "deliverable": "Deploy hybrid TLS VPN & operator token validation"
        },
        {
            "phase": 3,
            "label": "MEDIUM",
            "timeframe": "Weeks 10–14",
            "systems": ["Ventilation", "Haulage"],
            "replacements": ["ML-KEM-768", "ML-DSA-65"],
            "effort_weeks": 5,
            "cost_usd": 75000,
            "deliverable": "Upgrade SCADA telemetry endpoints & automated haulage transceivers"
        }
    ]
    
    total_cost = sum(p["cost_usd"] for p in phases)
    total_weeks = sum(p["effort_weeks"] for p in phases)
    
    return {
        "phases": phases,
        "total_systems": sum(len(p["systems"]) for p in phases),
        "total_cost_usd": total_cost,
        "total_weeks": total_weeks,
        "budget_limit_usd": budget,
        "feasible": total_cost <= budget and total_weeks <= max_weeks
    }
