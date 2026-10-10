"""
MineGuard AI - Migration Priority & Roadmap Route (Phases D5 & D7)
Calculates multi-criteria priority rankings, phase allocations, and resource requirements.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import PriorityListResponse, PriorityScore
from app.engines.priority import MigrationPlanner

router = APIRouter(prefix="/priority", tags=["Migration Priority"])
planner = MigrationPlanner()


@router.post("", response_model=PriorityListResponse)
async def get_migration_priorities(payload: Optional[Dict[str, Any]] = None):
    """
    Ranks cryptographic systems by composite migration priority score.
    """
    q_day = int(payload.get("q_day", 2029)) if payload else 2029
    priorities = planner.compute_migration_priority(q_day=q_day)
    effort_data = planner.estimate_total_effort(priorities)

    return PriorityListResponse(
        q_day=q_day,
        priorities=[PriorityScore(**p) for p in priorities],
        total_weeks=effort_data["total_weeks"],
        total_cost_usd=effort_data["total_cost_usd"]
    )


@router.get("/phases")
async def get_priorities_by_phase(q_day: int = Query(2029, ge=2027, le=2035)):
    """
    Groups prioritized systems into roadmap phases (IMMEDIATE, HIGH, MEDIUM, LOW).
    """
    priorities = planner.compute_migration_priority(q_day=q_day)
    grouped = planner.group_by_phase(priorities)
    effort_data = planner.estimate_total_effort(priorities)

    return {
        "q_day": q_day,
        "phases": grouped,
        "summary": effort_data
    }


@router.get("/effort")
async def get_effort_estimation(q_day: int = Query(2029, ge=2027, le=2035)):
    """
    Returns aggregated labor weeks, projected contractor expenses, and phase breakdowns.
    """
    priorities = planner.compute_migration_priority(q_day=q_day)
    effort_data = planner.estimate_total_effort(priorities)
    return {
        "q_day": q_day,
        **effort_data
    }
