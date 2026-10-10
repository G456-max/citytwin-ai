"""
MineGuard AI - Quantum Cascade Simulation Route (Phases D3 & D7)
Simulates failure cascades, timeline progressions, comparison views, and what-if scenarios.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import (
    CascadeRequest,
    CascadeFullResponse,
    CascadeComparisonResponse,
    CascadeTimelineEntry,
)
from app.engines.cascade import CascadeEngine

router = APIRouter(prefix="/cascade", tags=["Cascade Simulation"])
cascade_engine = CascadeEngine()


@router.post("", response_model=CascadeFullResponse)
async def simulate_cascade(payload: CascadeRequest):
    """
    Executes BFS cascade simulation for a specific Q-Day horizon and set of migrated systems.
    """
    logger.info(f"POST /api/cascade: Q-Day {payload.q_day}, Migrated: {payload.migrated_nodes}")
    result = cascade_engine.run_cascade(
        q_day=payload.q_day,
        migrated_nodes=payload.migrated_nodes
    )
    return CascadeFullResponse(**result)


@router.post("/comparison", response_model=CascadeComparisonResponse)
async def simulate_comparison(payload: Dict[str, Any]):
    """
    Simulates dual side-by-side cascades: Left (Unmitigated) vs Right (Mitigated core).
    """
    q_day = int(payload.get("q_day", 2029))
    result = cascade_engine.run_cascade_comparison(q_day=q_day)
    return CascadeComparisonResponse(**result)


@router.post("/what-if")
async def simulate_what_if(payload: Dict[str, Any]):
    """
    Simulates cascade failure reductions across 4 progressive mitigation milestones.
    """
    q_day = int(payload.get("q_day", 2029))
    result = cascade_engine.run_what_if(q_day=q_day)
    return result


@router.post("/timeline")
async def simulate_timeline(payload: Dict[str, Any]):
    """
    Returns time-ordered failure log tracking hour-by-hour cascade spread.
    """
    q_day = int(payload.get("q_day", 2029))
    migrated = payload.get("migrated_nodes", [])
    result = cascade_engine.run_cascade(q_day=q_day, migrated_nodes=migrated)

    timeline_entries = [
        {
            "hour": t["hour"],
            "node_id": t["node_id"],
            "node_label": t["node_label"],
            "status": t["status"],
            "reason": t["reason"]
        }
        for t in result["failure_timeline"]
    ]
    return {
        "q_day": q_day,
        "timeline": timeline_entries,
        "total_down": result["total_down"],
        "max_hours": max([t["hour"] for t in timeline_entries], default=0)
    }


@router.get("/summary")
async def get_cascade_summary(q_day: int = Query(2029, ge=2027, le=2035)):
    """
    Returns concise key risk performance indicators for cascade impact.
    """
    result = cascade_engine.run_cascade(q_day=q_day, migrated_nodes=[])
    return {
        "q_day": q_day,
        "total_down": result["total_down"],
        "total_systems": result["total_systems"],
        "critical_down": result["critical_down"],
        "safety_impact": result["safety_impact"],
        "estimated_cost_usd": result["estimated_cost_usd"],
        "estimated_downtime_hours": result["estimated_downtime_hours"]
    }
