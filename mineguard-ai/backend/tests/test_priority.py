"""
Unit Tests for Migration Priority Planner (Phases D5 & D7)
Validates multi-criteria scoring, CA-Root top-ranking, phase grouping,
effort and cost estimation, safety weighting, and immediate mitigation of critical assets.
"""

import pytest
from app.engines.priority import MigrationPlanner
from app.engines.graph_data import CA_ROOT_ID, CRITICAL_NODES, SAFETY_NODES


@pytest.fixture
def planner():
    return MigrationPlanner()


# 1. test_priority_computed
def test_priority_computed(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    assert len(priorities) > 0
    for p in priorities:
        assert "rank" in p
        assert "priority_score" in p
        assert "phase" in p
        assert "effort_weeks" in p


# 2. test_ca_root_is_first
def test_ca_root_is_first(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    first_item = priorities[0]
    assert first_item["node_id"] == CA_ROOT_ID
    assert first_item["rank"] == 1


# 3. test_phases_grouped
def test_phases_grouped(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    grouped = planner.group_by_phase(priorities)
    assert "IMMEDIATE" in grouped
    assert "HIGH" in grouped
    assert "MEDIUM" in grouped
    assert len(grouped["IMMEDIATE"]) >= 1


# 4. test_effort_estimated
def test_effort_estimated(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    effort = planner.estimate_total_effort(priorities)
    assert "total_weeks" in effort
    assert effort["total_weeks"] > 0
    assert "by_phase" in effort


# 5. test_cost_positive
def test_cost_positive(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    effort = planner.estimate_total_effort(priorities)
    assert effort["total_cost_usd"] > 0
    assert effort["total_cost_usd"] == effort["total_weeks"] * 15000


# 6. test_safety_critical_boost
def test_safety_critical_boost(planner):
    vent_score = planner.compute_priority_score("ventilation", q_day=2029)
    rep_score = planner.compute_priority_score("reporting", q_day=2029)
    # Ventilation is critical & safety-critical; reporting is medium business reporting
    assert vent_score > rep_score


# 7. test_priority_score_in_range
def test_priority_score_in_range(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    for p in priorities:
        score = p["priority_score"]
        assert 0.0 <= score <= 1.0


# 8. test_all_critical_nodes_are_immediate
def test_all_critical_nodes_are_immediate(planner):
    priorities = planner.compute_migration_priority(q_day=2029)
    priorities_by_id = {p["node_id"]: p for p in priorities}

    for crit_id in CRITICAL_NODES:
        if crit_id in priorities_by_id:
            node_priority = priorities_by_id[crit_id]
            assert node_priority["phase"] == "IMMEDIATE", (
                f"Critical node {crit_id} has phase {node_priority['phase']}, expected IMMEDIATE"
            )
