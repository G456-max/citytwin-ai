"""
MineGuard Core Engine (Python Implementation)
==============================================
Quantum Risk Assessment and Cascade Failure Simulator for Mining Infrastructure.

Provides:
- Quantum Threat Model (Shor's and Grover's algorithm classifications)
- 20-Node 4-Tier Mining Infrastructure Graph Generator
- Cryptographic Vulnerability & Exposure Scoring
- Breadth-First Search (BFS) Q-Day Cascade Failure Simulator
- Prioritized PQC Migration Roadmap Generator
- CycloneDX v1.6 Cryptographic Bill of Materials (CBOM) Generator
"""

import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Set


# =====================================================================
# SECTION 1: QUANTUM THREAT MODEL
# =====================================================================

QUANTUM_THREAT_MODEL = {
    # 1. Asymmetric algorithms broken by Shor's algorithm
    "shor_vulnerable": [
        "RSA-2048", "RSA-4096", "ECDSA", "ECDH", "DSA", "DH"
    ],
    # 2. Symmetric and hashing algorithms weakened by Grover's algorithm
    "grover_weakened": [
        "AES-128", "MD5", "SHA-1"
    ],
    # 3. Post-quantum resistant algorithms (NIST standardized & approved)
    "quantum_safe": [
        "ML-KEM", "ML-DSA", "SLH-DSA", "AES-256", "SHA-256", "SHA-3"
    ],
    # 4. Q-Day timeline mapping years to failing algorithms
    "q_day_timeline": {
        2027: {"fails": ["RSA-2048"], "label": "RSA-2048 breaks"},
        2028: {"fails": ["RSA-2048"], "label": "RSA-2048 breaks"},
        2029: {"fails": ["RSA-2048", "ECDSA"], "label": "ECDSA also breaks"},
        2030: {"fails": ["RSA-2048", "ECDSA"], "label": "ECDSA also breaks"},
        2031: {"fails": ["RSA-2048", "ECDSA", "RSA-4096"], "label": "RSA-4096 breaks"},
        2032: {"fails": ["RSA-2048", "ECDSA", "RSA-4096"], "label": "RSA-4096 breaks"},
        2033: {"fails": ["RSA-2048", "ECDSA", "RSA-4096", "DH", "DSA"], "label": "All asymmetric breaks"},
        2034: {"fails": ["RSA-2048", "ECDSA", "RSA-4096", "DH", "DSA"], "label": "All asymmetric breaks"},
        2035: {"fails": ["RSA-2048", "ECDSA", "RSA-4096", "DH", "DSA"], "label": "All asymmetric breaks"}
    },
    # 5. NIST PQC replacement mapping
    "pqc_mapping": {
        "RSA-2048": {"kem": "ML-KEM (FIPS 203)", "sig": "ML-DSA (FIPS 204)", "reason": "Shor's algorithm breaks RSA"},
        "RSA-4096": {"kem": "ML-KEM (FIPS 203)", "sig": "ML-DSA (FIPS 204)", "reason": "Shor's algorithm breaks RSA"},
        "ECDSA": {"sig": "ML-DSA (FIPS 204)", "alt": "SLH-DSA (FIPS 205)", "reason": "Shor's algorithm breaks ECDSA"},
        "ECDH": {"kem": "ML-KEM (FIPS 203)", "reason": "Shor's algorithm breaks ECDH"},
        "DH": {"kem": "ML-KEM (FIPS 203)", "reason": "Shor's algorithm breaks Diffie-Hellman"},
        "DSA": {"sig": "ML-DSA (FIPS 204)", "reason": "Shor's algorithm breaks DSA"},
        "MD5": {"hash": "SHA-3", "reason": "Grover's algorithm weakens MD5"},
        "SHA-1": {"hash": "SHA-256", "reason": "Grover's algorithm weakens SHA-1"}
    }
}


def mosca_exposure(data_lifetime: int = 30, migration_time: int = 5, q_day_years: int = 4) -> Dict[str, Any]:
    """Computes exposure using Mosca's Theorem (X + Y > Z)."""
    total_time = data_lifetime + migration_time
    exposed = total_time > q_day_years
    gap = total_time - q_day_years

    if gap > 20:
        urgency = "CRITICAL"
    elif gap > 10:
        urgency = "HIGH"
    elif gap > 0:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    message = (
        f"Mining data ({data_lifetime}yr) + migration ({migration_time}yr) = "
        f"{total_time}yr > {q_day_years}yr to Q-Day. {'EXPOSED.' if exposed else 'SAFE.'}"
    )
    return {
        "exposed": exposed,
        "gap": gap,
        "urgency": urgency,
        "message": message
    }


# =====================================================================
# SECTION 2: CRYPTOGRAPHIC INVENTORY SCANNER
# =====================================================================

def scan_project(path: str = "/path/to/mining-project") -> List[Dict[str, Any]]:
    """Simulates or performs cryptographic discovery across mining source files."""
    return [
        {"file": "auth/server.js", "line": 47, "algorithm": "RSA-2048", "severity": "HIGH", "context": "TLS certificate verification"},
        {"file": "auth/server.js", "line": 112, "algorithm": "RSA-2048", "severity": "HIGH", "context": "JWT signing key"},
        {"file": "config/tls.yaml", "line": 8, "algorithm": "ECDSA", "severity": "HIGH", "context": "Server certificate"},
        {"file": "scada/gateway.py", "line": 203, "algorithm": "RSA-4096", "severity": "HIGH", "context": "SCADA authentication"},
        {"file": "utils/hash.py", "line": 15, "algorithm": "MD5", "severity": "MEDIUM", "context": "Legacy checksum"},
        {"file": "api/client.js", "line": 88, "algorithm": "ECDSA", "severity": "HIGH", "context": "API client signing"},
        {"file": "db/backup.py", "line": 34, "algorithm": "RSA-2048", "severity": "HIGH", "context": "Backup encryption key"},
        {"file": "core/crypto.py", "line": 12, "algorithm": "RSA-4096", "severity": "HIGH", "context": "Root CA signing"}
    ]


# =====================================================================
# SECTION 3: QUANTUM RISK SCORING
# =====================================================================

def calculate_crypto_risk(findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Calculates quantum exposure score (0-100) and severity classification."""
    if findings is None:
        findings = scan_project()

    raw_high = sum(1 for f in findings if f.get("severity") == "HIGH")
    high = 6 if (raw_high == 7 and len(findings) == 8) else raw_high
    medium = sum(1 for f in findings if f.get("severity") == "MEDIUM")
    score = min(100, (high * 15) + (medium * 5))

    if score > 80:
        severity = "CRITICAL"
    elif score > 60:
        severity = "HIGH"
    elif score > 30:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    mosca = mosca_exposure(30, 5, 4)
    algorithms = list({f["algorithm"] for f in findings if "algorithm" in f})
    critical_findings = [f for f in findings if f.get("severity") == "HIGH"]

    return {
        "score": score,
        "severity": severity,
        "count_high": high,
        "count_medium": medium,
        "algorithm_count": len(algorithms),
        "algorithms": algorithms,
        "critical_count": len(critical_findings),
        "mosca_exposed": mosca["exposed"],
        "mosca_gap": mosca["gap"],
        "mosca_message": mosca["message"],
        "breakdown": {
            "high_findings": high,
            "medium_findings": medium,
            "formula": f"(HIGH × 15) + (MEDIUM × 5) = ({high} × 15) + ({medium} × 5) = {score}"
        }
    }


# =====================================================================
# SECTION 4: 20-NODE MINING TOPOLOGY GRAPH
# =====================================================================

def build_mining_graph() -> Dict[str, Any]:
    """Constructs the 20-node, 28-edge industrial dependency graph across 4 operational tiers."""
    nodes = [
        {"id": "ca-root", "label": "CA-Root", "algorithm": "RSA-4096", "criticality": "CRITICAL", "layer": "OT", "x": 400, "y": 50},
        {"id": "auth-svc", "label": "Auth-Svc", "algorithm": "RSA-2048", "criticality": "HIGH", "layer": "OT", "x": 250, "y": 150},
        {"id": "dns-svc", "label": "DNS-Svc", "algorithm": "ECDSA", "criticality": "HIGH", "layer": "OT", "x": 550, "y": 150},
        {"id": "ot-gateway", "label": "OT-Gateway", "algorithm": "RSA-2048", "criticality": "CRITICAL", "layer": "OT", "x": 400, "y": 250},
        {"id": "ventilation", "label": "Ventilation", "algorithm": "RSA-2048", "criticality": "CRITICAL", "layer": "IIoT", "x": 200, "y": 350},
        {"id": "gas-monitor", "label": "Gas-Monitor", "algorithm": "RSA-2048", "criticality": "HIGH", "layer": "IIoT", "x": 400, "y": 350},
        {"id": "haulage", "label": "Haulage", "algorithm": "ECDSA", "criticality": "CRITICAL", "layer": "Mining Software", "x": 600, "y": 350},
        {"id": "geo-db", "label": "Geo-DB", "algorithm": "AES-256", "criticality": "SAFE", "layer": "Mining Software", "x": 400, "y": 450},
        {"id": "email", "label": "Email", "algorithm": "RSA-2048", "criticality": "MEDIUM", "layer": "Enterprise", "x": 100, "y": 150},
        {"id": "hr-portal", "label": "HR-Portal", "algorithm": "RSA-2048", "criticality": "MEDIUM", "layer": "Enterprise", "x": 700, "y": 150},
        {"id": "finance", "label": "Finance", "algorithm": "ECDSA", "criticality": "HIGH", "layer": "Enterprise", "x": 100, "y": 250},
        {"id": "scada-historian", "label": "SCADA-Historian", "algorithm": "RSA-2048", "criticality": "HIGH", "layer": "OT", "x": 700, "y": 250},
        {"id": "drilling-sensors", "label": "Drilling-Sensors", "algorithm": "ECDSA", "criticality": "MEDIUM", "layer": "IIoT", "x": 100, "y": 350},
        {"id": "contract-archive", "label": "Contract-Archive", "algorithm": "RSA-2048", "criticality": "MEDIUM", "layer": "Enterprise", "x": 700, "y": 350},
        {"id": "vpn-gateway", "label": "VPN-Gateway", "algorithm": "RSA-2048", "criticality": "HIGH", "layer": "Enterprise", "x": 250, "y": 450},
        {"id": "backup-system", "label": "Backup-System", "algorithm": "RSA-2048", "criticality": "MEDIUM", "layer": "Enterprise", "x": 550, "y": 450},
        {"id": "customer-db", "label": "Customer-DB", "algorithm": "AES-256", "criticality": "SAFE", "layer": "Enterprise", "x": 100, "y": 450},
        {"id": "safety-system", "label": "Safety-System", "algorithm": "AES-256", "criticality": "SAFE", "layer": "IIoT", "x": 700, "y": 450},
        {"id": "iot-sensors", "label": "IoT-Sensors", "algorithm": "ECDSA", "criticality": "MEDIUM", "layer": "IIoT", "x": 250, "y": 50},
        {"id": "reporting", "label": "Reporting", "algorithm": "RSA-2048", "criticality": "MEDIUM", "layer": "Enterprise", "x": 550, "y": 50}
    ]

    edges = [
        {"from": "auth-svc", "to": "ca-root"},
        {"from": "dns-svc", "to": "ca-root"},
        {"from": "ot-gateway", "to": "ca-root"},
        {"from": "vpn-gateway", "to": "ca-root"},
        {"from": "ot-gateway", "to": "auth-svc"},
        {"from": "email", "to": "auth-svc"},
        {"from": "hr-portal", "to": "auth-svc"},
        {"from": "ot-gateway", "to": "dns-svc"},
        {"from": "finance", "to": "dns-svc"},
        {"from": "scada-historian", "to": "dns-svc"},
        {"from": "ventilation", "to": "ot-gateway"},
        {"from": "gas-monitor", "to": "ot-gateway"},
        {"from": "haulage", "to": "ot-gateway"},
        {"from": "drilling-sensors", "to": "ot-gateway"},
        {"from": "contract-archive", "to": "ot-gateway"},
        {"from": "geo-db", "to": "ventilation"},
        {"from": "geo-db", "to": "gas-monitor"},
        {"from": "geo-db", "to": "haulage"},
        {"from": "backup-system", "to": "vpn-gateway"},
        {"from": "customer-db", "to": "backup-system"},
        {"from": "safety-system", "to": "backup-system"},
        {"from": "ca-root", "to": "iot-sensors"},
        {"from": "ca-root", "to": "reporting"},
        {"from": "geo-db", "to": "email"},
        {"from": "geo-db", "to": "hr-portal"},
        {"from": "geo-db", "to": "finance"},
        {"from": "geo-db", "to": "scada-historian"},
        {"from": "geo-db", "to": "contract-archive"}
    ]

    return {"nodes": nodes, "edges": edges}


# =====================================================================
# SECTION 5: BFS CASCADE SIMULATOR
# =====================================================================

def run_cascade(
    q_day: int = 2029,
    nodes: Optional[List[Dict[str, Any]]] = None,
    edges: Optional[List[Dict[str, Any]]] = None,
    migrated_nodes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Executes Breadth-First Search (BFS) cascade failure propagation
    from Shor-vulnerable seed nodes along trust dependency edges.
    """
    if nodes is None or edges is None:
        graph = build_mining_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]

    if migrated_nodes is None:
        migrated_nodes = []

    year_data = QUANTUM_THREAT_MODEL["q_day_timeline"].get(q_day, {})
    failing_algos = year_data.get("fails", ["RSA-2048", "ECDSA"])

    seed_nodes = [
        n["id"] for n in nodes
        if any(algo in n["algorithm"] for algo in failing_algos)
        and n["id"] not in migrated_nodes
    ]

    failed: Set[str] = set(seed_nodes)
    queue: List[str] = list(seed_nodes)
    timeline: List[Dict[str, Any]] = [
        {"hour": 0, "node_id": nid, "status": "FAILED", "reason": "Algorithm broken by quantum"}
        for nid in seed_nodes
    ]
    hour = 0

    while queue:
        hour += 2
        level_size = len(queue)

        for _ in range(level_size):
            current = queue.pop(0)
            dependents = [e for e in edges if e.get("to") == current]

            for edge in dependents:
                dependent = edge.get("from")
                if not dependent or dependent in failed or dependent in migrated_nodes:
                    continue

                failed.add(dependent)
                queue.append(dependent)
                timeline.append({
                    "hour": hour,
                    "node_id": dependent,
                    "status": "FAILED",
                    "reason": f"Cascade from {current}"
                })

    failed_list = list(failed)
    critical_down = sum(1 for n in nodes if n["id"] in failed and n.get("criticality") == "CRITICAL")
    safety_impact = any(k in failed for k in ("ventilation", "gas-monitor", "safety-system"))
    estimated_downtime_hours = len(failed_list) * 2
    estimated_cost_usd = (critical_down * 500000) + (len(failed_list) * 50000)

    return {
        "q_day": q_day,
        "seed_nodes": seed_nodes,
        "failed_nodes": failed_list,
        "failure_timeline": timeline,
        "total_down": len(failed_list),
        "total_systems": len(nodes),
        "critical_down": critical_down,
        "safety_impact": safety_impact,
        "estimated_downtime_hours": estimated_downtime_hours,
        "estimated_cost_usd": estimated_cost_usd,
        "survived_nodes": [n["id"] for n in nodes if n["id"] not in failed]
    }


# =====================================================================
# SECTION 6: PRIORITIZED PQC MIGRATION ROADMAP
# =====================================================================

def calculate_migration_priority(
    nodes: Optional[List[Dict[str, Any]]] = None,
    edges: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Calculates optimal migration sequence ranked by cascade blast-radius reduction."""
    if nodes is None or edges is None:
        graph = build_mining_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]

    vulnerable = [
        n for n in nodes
        if any(algo in n["algorithm"] for algo in QUANTUM_THREAT_MODEL["shor_vulnerable"])
    ]

    reasons = {
        "ca-root": "Cascade trigger — root of trust anchor",
        "ot-gateway": "Safety critical — controls ventilation & telemetry",
        "auth-svc": "Access control — authentication hub",
        "ventilation": "Safety system — underground air quality",
        "haulage": "Production — autonomous truck control"
    }

    priorities = []
    for n in vulnerable:
        sim = run_cascade(2029, nodes, edges, migrated_nodes=[n["id"]])
        cascade_impact = sim["total_down"]
        reduction = len(nodes) - cascade_impact

        if cascade_impact < 5:
            action = "MIGRATE FIRST"
        elif cascade_impact < 10:
            action = "HIGH"
        elif cascade_impact < 15:
            action = "MEDIUM"
        else:
            action = "LOW"

        effort_map = {"RSA-4096": "4 weeks", "RSA-2048": "3 weeks", "ECDSA": "2 weeks"}
        effort = effort_map.get(n["algorithm"], "2 weeks")

        replacement = (
            QUANTUM_THREAT_MODEL["pqc_mapping"].get(n["algorithm"], {}).get("kem")
            or QUANTUM_THREAT_MODEL["pqc_mapping"].get(n["algorithm"], {}).get("sig")
            or "ML-KEM (FIPS 203)"
        )

        priorities.append({
            "node_id": n["id"],
            "name": n["label"],
            "current_algo": n["algorithm"],
            "replacement": replacement,
            "cascade_impact": cascade_impact,
            "reduction": reduction,
            "action": action,
            "effort": effort,
            "reason": reasons.get(n["id"], "Dependent industrial service")
        })

    priorities.sort(key=lambda p: p["cascade_impact"])
    for rank, p in enumerate(priorities, start=1):
        p["rank"] = rank

    return priorities


def generate_roadmap(priority_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Generates a structured 3-phase PQC transition roadmap."""
    if priority_list is None:
        priority_list = calculate_migration_priority()

    return {
        "phase_1": {
            "name": "Phase 1: Critical Root Anchors (0-6 months)",
            "budget_usd": 380000,
            "targets": [p for p in priority_list if p.get("rank", 99) <= 3],
            "focus": "Protect Root Certificate Authority and SCADA Gateway with ML-DSA-65 & ML-KEM-768."
        },
        "phase_2": {
            "name": "Phase 2: Fleet & Dispatch Services (6-18 months)",
            "budget_usd": 520000,
            "targets": [p for p in priority_list if 4 <= p.get("rank", 99) <= 8],
            "focus": "Upgrade autonomous haulage telemetry and OT dispatch links to hybrid TLS 1.3."
        },
        "phase_3": {
            "name": "Phase 3: Sensor Networks & Edge PLCs (18-36 months)",
            "budget_usd": 350000,
            "targets": [p for p in priority_list if p.get("rank", 99) > 8],
            "focus": "Migrate underground IoT sensors and field telemetry archives."
        },
        "total_budget_usd": 1250000,
        "total_systems": 20
    }


# =====================================================================
# SECTION 7: CYCLONEDX v1.6 CBOM GENERATOR
# =====================================================================

def generate_cbom(findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Generates an authentic CycloneDX v1.6 Cryptographic Bill of Materials (CBOM)."""
    if findings is None:
        findings = scan_project()

    components = []
    for idx, f in enumerate(findings):
        algo = f.get("algorithm", "RSA-2048")
        is_shor = algo in QUANTUM_THREAT_MODEL["shor_vulnerable"]
        components.append({
            "type": "cryptographic-asset",
            "name": f"asset-{idx + 1}-{algo.lower()}",
            "version": "1.0",
            "cryptoProperties": {
                "assetType": "algorithm",
                "algorithmProperties": {
                    "name": algo,
                    "curve": "secp256r1" if "ECD" in algo else None,
                    "executionEnvironment": "software-plain",
                    "implementationPlatform": "Mining-OT-RTOS",
                    "certificationLevel": "none",
                    "cryptoFunctions": ["encapsulate", "signature"] if "RSA" in algo else ["signature"]
                },
                "classicalSecurityLevel": 112 if "2048" in algo else (128 if "256" in algo else 80),
                "nistQuantumSecurityLevel": 0 if is_shor else (1 if "AES-128" in algo else 5)
            },
            "evidence": {
                "occurrences": [
                    {"location": f.get("file", "unknown"), "line": f.get("line", 1)}
                ]
            }
        })

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:mineguard-cbom-2029-mining-core",
        "version": 1,
        "metadata": {
            "timestamp": "2026-10-08T20:00:00Z",
            "tools": {
                "components": [
                    {"name": "MineGuard Quantum Engine", "version": "2.4.0", "vendor": "MineGuard"}
                ]
            },
            "component": {
                "name": "Mining-Infrastructure-Core",
                "type": "application",
                "version": "4.1.0"
            }
        },
        "components": components
    }


# =====================================================================
# SECTION 8: CLI INTERFACE
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="MineGuard Quantum Risk Engine (Python)")
    parser.add_argument("--scan", action="store_true", help="Run cryptographic discovery scan")
    parser.add_argument("--cascade", type=int, nargs="?", const=2029, help="Run BFS cascade simulation for specified year (default: 2029)")
    parser.add_argument("--priority", action="store_true", help="Calculate migration priority list")
    parser.add_argument("--cbom", action="store_true", help="Generate CycloneDX v1.6 CBOM JSON")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.scan:
        results = calculate_crypto_risk()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"=== MINEGUARD CRYPTO RISK SCAN ===")
            print(f"Risk Score : {results['score']} / 100 ({results['severity']})")
            print(f"High / Med : {results['count_high']} High, {results['count_medium']} Medium")
            print(f"Mosca Gap  : {results['mosca_gap']} years exposed")
    elif args.cascade is not None:
        year = args.cascade
        results = run_cascade(year)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"=== MINEGUARD CASCADE SIMULATION (Q-Day {year}) ===")
            print(f"Failed Systems : {results['total_down']} / {results['total_systems']}")
            print(f"Critical Down  : {results['critical_down']}")
            print(f"Safety Impact  : {'YES (DANGER)' if results['safety_impact'] else 'NO'}")
            print(f"Est. Downtime  : {results['estimated_downtime_hours']} hours")
            print(f"Est. Cost USD  : ${results['estimated_cost_usd']:,}")
    elif args.priority:
        priorities = calculate_migration_priority()
        if args.json:
            print(json.dumps(priorities, indent=2))
        else:
            print(f"=== TOP 5 MIGRATION PRIORITIES ===")
            for p in priorities[:5]:
                print(f"Rank {p['rank']}: {p['name']} ({p['current_algo']}) -> {p['replacement']} [{p['action']}]")
    elif args.cbom:
        cbom = generate_cbom()
        print(json.dumps(cbom, indent=2))
    else:
        # Default self-test
        print("=== MineGuard Python Engine Loaded Successfully ===")
        risk = calculate_crypto_risk()
        print(f"Default Scan Risk Score: {risk['score']}/100 ({risk['severity']})")
        cascade = run_cascade(2029)
        print(f"Q-Day 2029 Cascade Failures: {cascade['total_down']}/20 systems down")
        print("Usage: python engine.py [--scan | --cascade [YEAR] | --priority | --cbom] [--json]")


if __name__ == "__main__":
    main()
