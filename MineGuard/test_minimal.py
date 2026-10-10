"""
MineGuard — Automated Test Suite for Minimal 4-Feature Architecture
Validates Scanner, Cascade Simulator, Risk Scorer, Migration Planner, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from scanner import scan
from cascade import run_cascade
from scorer import score_risk, rank_priorities
from planner import plan_migration
from main import app

client = TestClient(app)


# Feature 1: Scanner Tests
def test_scanner_returns_findings():
    findings = scan("/path/to/mining-project")
    assert len(findings) == 8
    algorithms = {f["algorithm"] for f in findings}
    assert any("RSA" in a for a in algorithms)
    assert any("ECDSA" in a for a in algorithms)
    assert any("MD5" in a for a in algorithms)


# Feature 2: Cascade Simulator Tests
def test_cascade_2029_unmitigated():
    result = run_cascade(2029, [])
    assert result["total_down"] == 5
    assert result["total_systems"] == 6
    assert "ca-root" not in result["failed"] # RSA-4096 breaches post-2030
    assert "ventilation" in result["failed"]
    assert "haulage" in result["failed"]


def test_cascade_with_migration():
    result = run_cascade(2029, ["ventilation", "haulage"])
    assert "ventilation" not in result["failed"]
    assert "haulage" not in result["failed"]


# Feature 3: Risk Scorer Tests
def test_risk_scorer_calibration():
    findings = scan("/path/to/mining-project")
    risk = score_risk(findings)
    assert risk["score"] == 95
    assert risk["severity"] == "CRITICAL"


def test_priority_ranking_ca_root_first():
    priorities = rank_priorities()
    assert len(priorities) == 5
    assert priorities[0]["rank"] == 1
    assert priorities[0]["system"] == "CA-Root"
    assert priorities[0]["action"] == "MIGRATE FIRST"


# Feature 4: Migration Planner Tests
def test_planner_three_phases():
    plan = plan_migration()
    assert len(plan["phases"]) == 3
    assert plan["total_systems"] == 5
    assert plan["total_weeks"] == 14
    assert plan["total_cost_usd"] == 210000
    assert plan["feasible"] is True


# API Endpoints Integration Tests
def test_api_scan():
    res = client.post("/scan", json={"path": "/path/to/mining-project"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["findings"]) == 8
    assert data["risk"]["score"] == 95


def test_api_cascade():
    res = client.post("/cascade", json={"q_day": 2029, "migrated": []})
    assert res.status_code == 200
    data = res.json()
    assert data["total_down"] == 5


def test_api_priority():
    res = client.post("/priority", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["priorities"][0]["system"] == "CA-Root"


def test_api_plan():
    res = client.post("/plan", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["total_cost_usd"] == 210000
    assert data["total_weeks"] == 14
