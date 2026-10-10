"""
MineGuard — Minimal 4-Feature Backend API
Core endpoints: /scan, /cascade, /priority, /plan
"""

from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from scanner import scan
from cascade import run_cascade
from scorer import score_risk, rank_priorities
from planner import plan_migration

app = FastAPI(
    title="MineGuard Minimal API",
    description="Intelligent Post-Quantum Cybersecurity for Mining Infrastructure (4 Core Features)",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    path: str = "/path/to/mining-project"


class CascadeRequest(BaseModel):
    q_day: int = 2029
    migrated: List[str] = []


class PriorityRequest(BaseModel):
    cascade: Optional[Dict[str, Any]] = None


class PlanRequest(BaseModel):
    priorities: Optional[List[Dict[str, Any]]] = None
    budget: int = 500000
    max_weeks: int = 14


@app.get("/")
def api_root():
    return {
        "app": "MineGuard Minimal API",
        "tagline": "Predict the risk. Trace the impact. Plan the migration.",
        "endpoints": ["/scan", "/cascade", "/priority", "/plan"]
    }


@app.post("/scan")
def api_scan(payload: Optional[ScanRequest] = None, path: Optional[str] = Query(None)):
    """
    Feature 1: Cryptographic Scanner
    Input: Project path
    Output: Findings list + Risk score
    """
    target_path = path or (payload.path if payload else "/path/to/mining-project")
    findings = scan(target_path)
    risk = score_risk(findings)
    return {
        "project_path": target_path,
        "findings": findings,
        "risk": risk
    }


@app.post("/cascade")
def api_cascade(payload: Optional[CascadeRequest] = None, q_day: Optional[int] = Query(None)):
    """
    Feature 2: Cascade Simulator
    Input: Q-Day, migrated nodes
    Output: Failure timeline
    """
    target_q_day = q_day or (payload.q_day if payload else 2029)
    migrated = payload.migrated if payload else []
    return run_cascade(target_q_day, migrated)


@app.post("/priority")
def api_priority(payload: Optional[PriorityRequest] = None):
    """
    Feature 3: Risk Scorer & Priorities
    Input: Cascade result
    Output: Priority ranking list
    """
    cascade_data = payload.cascade if payload else {}
    return {
        "priorities": rank_priorities(cascade_data)
    }


@app.post("/plan")
def api_plan(payload: Optional[PlanRequest] = None):
    """
    Feature 4: Migration Planner
    Input: Priorities, constraints
    Output: 3-phase roadmap
    """
    priorities = payload.priorities if payload else None
    budget = payload.budget if payload else 500000
    max_weeks = payload.max_weeks if payload else 14
    return plan_migration(priorities, budget=budget, max_weeks=max_weeks)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
