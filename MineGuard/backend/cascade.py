"""
MineGuard — Feature 2: Cascade Simulator
Simulates upstream failure cascades across mining systems based on quantum horizon and migrated nodes.
"""

from typing import List, Dict, Any, Optional

NODES = [
    {"id": "ca-root", "name": "CA-Root", "algorithm": "RSA-4096", "critical": True},
    {"id": "auth-svc", "name": "Auth-Svc", "algorithm": "RSA-2048", "critical": True},
    {"id": "ot-gateway", "name": "OT-Gateway", "algorithm": "RSA-2048", "critical": True},
    {"id": "ventilation", "name": "Ventilation", "algorithm": "RSA-2048", "critical": True},
    {"id": "haulage", "name": "Haulage", "algorithm": "ECDSA", "critical": True},
    {"id": "geo-db", "name": "Geo-DB", "algorithm": "AES-256", "critical": False},
]

# Directed dependencies: (dependent_system, dependency)
# When dependency fails, dependent system also fails.
EDGES = [
    ("auth-svc", "ca-root"),
    ("ot-gateway", "auth-svc"),
    ("ventilation", "ot-gateway"),
    ("haulage", "ot-gateway"),
    ("geo-db", "ventilation"),
]


def run_cascade(q_day: int, migrated: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Simulate failure cascade starting from seed quantum breaches.
    Returns compromised systems and hourly breakdown.
    """
    migrated = migrated or []
    # Normalize migrated list to lowercase
    migrated_set = set(m.lower().replace(" ", "-") for m in migrated)

    # Vulnerability threshold by quantum horizon
    if q_day < 2029:
        failing_algos = ["RSA-2048"]
    elif q_day < 2031:
        failing_algos = ["RSA-2048", "ECDSA"]
    else:
        failing_algos = ["RSA-2048", "ECDSA", "RSA-4096"]

    # Initial breached systems at hour 0
    seed = [
        n["id"] for n in NODES
        if any(a in n["algorithm"] for a in failing_algos)
        and n["id"] not in migrated_set
        and n["name"].lower() not in migrated_set
    ]

    failed = set(seed)
    queue = list(seed)
    timeline = [{"hour": 0, "node": n, "status": "FAILED"} for n in seed]
    hour = 0

    # BFS cascade propagation across dependencies
    while queue:
        hour += 2
        size = len(queue)
        for _ in range(size):
            current = queue.pop(0)
            for src, dst in EDGES:
                if dst == current and src not in failed and src not in migrated_set:
                    failed.add(src)
                    queue.append(src)
                    timeline.append({"hour": hour, "node": src, "status": "FAILED"})

    survived = [n["id"] for n in NODES if n["id"] not in failed]

    return {
        "q_day": q_day,
        "failed": list(failed),
        "survived": survived,
        "timeline": timeline,
        "total_down": len(failed),
        "total_systems": len(NODES),
        "hours_to_shutdown": max([t["hour"] for t in timeline], default=0),
        "nodes": NODES,
        "edges": [{"from": src, "to": dst} for src, dst in EDGES]
    }
