"""
Unit Tests for Quantum Cascade Simulation Engine (Phase D3 & D7)
Validates seed determination by Q-Day, BFS failure propagation, timeline sequencing,
impact reduction via migration, and downtime/financial impact metrics.
"""

import pytest
from app.engines.cascade import CascadeEngine
from app.engines.graph_data import CA_ROOT_ID


@pytest.fixture
def engine():
    return CascadeEngine()


# 1. test_seed_nodes_2027 (only RSA-2048)
def test_seed_nodes_2027(engine):
    seeds = engine.determine_seed_nodes(q_day=2027)
    assert len(seeds) > 0
    # ca-root is RSA-4096, so it must NOT be in 2027 seed nodes
    assert CA_ROOT_ID not in seeds
    # auth-svc is RSA-2048, so it MUST be in 2027 seed nodes
    assert "auth-svc" in seeds


# 2. test_seed_nodes_2029 (RSA-2048 + ECDSA)
def test_seed_nodes_2029(engine):
    seeds = engine.determine_seed_nodes(q_day=2029)
    # Haulage is ECDSA, ot-gateway is RSA-2048
    assert "haulage" in seeds
    assert "ot-gateway" in seeds
    # ca-root is RSA-4096, not yet broken in 2029
    assert CA_ROOT_ID not in seeds


# 3. test_seed_nodes_2031 (adds RSA-4096)
def test_seed_nodes_2031(engine):
    seeds = engine.determine_seed_nodes(q_day=2031)
    # ca-root is RSA-4096, now broken
    assert CA_ROOT_ID in seeds
    assert "ot-gateway" in seeds
    assert "haulage" in seeds


# 4. test_cascade_without_migration_2029
def test_cascade_without_migration_2029(engine):
    res = engine.run_cascade(q_day=2029, migrated_nodes=[])
    assert res["total_down"] >= 10
    assert len(res["failed_nodes"]) == res["total_down"]
    assert res["safety_impact"] is True


# 5. test_cascade_with_migration_2029
def test_cascade_with_migration_2029(engine):
    migrated = ["ca-root", "ot-gateway", "auth-svc"]
    res = engine.run_cascade(q_day=2029, migrated_nodes=migrated)
    for m in migrated:
        assert m not in res["failed_nodes"]


# 6. test_migration_reduces_total_down
def test_migration_reduces_total_down(engine):
    baseline = engine.run_cascade(q_day=2029, migrated_nodes=[])
    mitigated = engine.run_cascade(q_day=2029, migrated_nodes=["ca-root", "ot-gateway", "auth-svc"])
    assert mitigated["total_down"] < baseline["total_down"]


# 7. test_cascade_timeline_sorted_by_hour
def test_cascade_timeline_sorted_by_hour(engine):
    res = engine.run_cascade(q_day=2029)
    timeline = res["failure_timeline"]
    hours = [t["hour"] for t in timeline]
    assert hours == sorted(hours)


# 8. test_ca_root_fails_at_hour_0
def test_ca_root_fails_at_hour_0(engine):
    # At Q-Day 2031, RSA-4096 is broken directly
    res = engine.run_cascade(q_day=2031, migrated_nodes=[])
    ca_event = next(t for t in res["failure_timeline"] if t["node_id"] == CA_ROOT_ID)
    assert ca_event["hour"] == 0
    assert ca_event["status"] == "FAILED"


# 9. test_ventilation_affected_by_hour_8
def test_ventilation_affected_by_hour_8(engine):
    res = engine.run_cascade(q_day=2029, migrated_nodes=[])
    assert "ventilation" in res["failed_nodes"]
    vent_event = next(t for t in res["failure_timeline"] if t["node_id"] == "ventilation")
    assert vent_event["hour"] <= 8


# 10. test_total_down_matches_failed_list
def test_total_down_matches_failed_list(engine):
    res = engine.run_cascade(q_day=2029)
    assert res["total_down"] == len(res["failed_nodes"])


# 11. test_critical_down_counted
def test_critical_down_counted(engine):
    res = engine.run_cascade(q_day=2029)
    assert res["critical_down"] >= 1
    assert res["critical_down"] <= res["total_down"]


# 12. test_estimated_cost_positive
def test_estimated_cost_positive(engine):
    res = engine.run_cascade(q_day=2029)
    assert res["estimated_cost_usd"] > 0
    assert res["estimated_downtime_hours"] > 0
