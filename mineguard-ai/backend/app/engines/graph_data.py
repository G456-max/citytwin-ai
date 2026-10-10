"""
MineGuard AI - Canonical 20-Node Mining Graph & 28-Dependency Data Model (Phase D1)
Defines the representative industrial topology for underground/open-pit mining OT infrastructure.

DISCLAIMER:
This graph is a representative model of mining infrastructure, not a real facility.
Node IDs and dependencies are illustrative for demonstrating cascade analysis.
"""

from typing import List, Dict, Any

DISCLAIMER: str = (
    "This graph is a representative model of mining infrastructure, not a "
    "real facility. Node IDs and dependencies are illustrative for "
    "demonstrating cascade analysis."
)

CA_ROOT_ID: str = "ca-root"

CRITICAL_NODES: List[str] = [
    "ca-root",
    "ot-gateway",
    "ventilation",
    "haulage"
]

SAFETY_NODES: List[str] = [
    "ventilation",
    "gas-monitor",
    "safety-system"
]

# ============ 20 NODES ACROSS 5 CATEGORIES ============
MINING_NODES: List[Dict[str, Any]] = [
    # --- Infrastructure (3) ---
    {
        "id": "ca-root",
        "label": "CA-Root",
        "algorithm": "RSA-4096",
        "criticality": "CRITICAL",
        "x": 400.0,
        "y": 50.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Infrastructure"
    },
    {
        "id": "dns-svc",
        "label": "DNS-Svc",
        "algorithm": "ECDSA",
        "criticality": "HIGH",
        "x": 550.0,
        "y": 150.0,
        "data_lifetime_years": 5,
        "exposure": "internet",
        "category": "Infrastructure"
    },
    {
        "id": "vpn-gateway",
        "label": "VPN-Gateway",
        "algorithm": "RSA-2048",
        "criticality": "HIGH",
        "x": 250.0,
        "y": 450.0,
        "data_lifetime_years": 10,
        "exposure": "internet",
        "category": "Infrastructure"
    },

    # --- Authentication (2) ---
    {
        "id": "auth-svc",
        "label": "Auth-Svc",
        "algorithm": "RSA-2048",
        "criticality": "HIGH",
        "x": 250.0,
        "y": 150.0,
        "data_lifetime_years": 10,
        "exposure": "internet",
        "category": "Authentication"
    },
    {
        "id": "hr-portal",
        "label": "HR-Portal",
        "algorithm": "RSA-2048",
        "criticality": "MEDIUM",
        "x": 700.0,
        "y": 150.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Authentication"
    },

    # --- OT Gateways (2) ---
    {
        "id": "ot-gateway",
        "label": "OT-Gateway",
        "algorithm": "RSA-2048",
        "criticality": "CRITICAL",
        "x": 400.0,
        "y": 250.0,
        "data_lifetime_years": 20,
        "exposure": "internal",
        "category": "OT Gateways"
    },
    {
        "id": "scada-historian",
        "label": "SCADA-Historian",
        "algorithm": "RSA-2048",
        "criticality": "HIGH",
        "x": 700.0,
        "y": 250.0,
        "data_lifetime_years": 20,
        "exposure": "internal",
        "category": "OT Gateways"
    },

    # --- Safety & Operations (7) ---
    {
        "id": "ventilation",
        "label": "Ventilation",
        "algorithm": "RSA-2048",
        "criticality": "CRITICAL",
        "x": 200.0,
        "y": 350.0,
        "data_lifetime_years": 0,
        "exposure": "internal",
        "category": "Safety & Operations"
    },
    {
        "id": "gas-monitor",
        "label": "Gas-Monitor",
        "algorithm": "RSA-2048",
        "criticality": "HIGH",
        "x": 400.0,
        "y": 350.0,
        "data_lifetime_years": 0,
        "exposure": "internal",
        "category": "Safety & Operations"
    },
    {
        "id": "haulage",
        "label": "Haulage",
        "algorithm": "ECDSA",
        "criticality": "CRITICAL",
        "x": 600.0,
        "y": 350.0,
        "data_lifetime_years": 0,
        "exposure": "internal",
        "category": "Safety & Operations"
    },
    {
        "id": "drilling-sensors",
        "label": "Drilling-Sensors",
        "algorithm": "ECDSA",
        "criticality": "MEDIUM",
        "x": 100.0,
        "y": 350.0,
        "data_lifetime_years": 5,
        "exposure": "internal",
        "category": "Safety & Operations"
    },
    {
        "id": "iot-sensors",
        "label": "IoT-Sensors",
        "algorithm": "ECDSA",
        "criticality": "MEDIUM",
        "x": 250.0,
        "y": 50.0,
        "data_lifetime_years": 5,
        "exposure": "internet",
        "category": "Safety & Operations"
    },
    {
        "id": "reporting",
        "label": "Reporting",
        "algorithm": "RSA-2048",
        "criticality": "MEDIUM",
        "x": 550.0,
        "y": 50.0,
        "data_lifetime_years": 15,
        "exposure": "internal",
        "category": "Safety & Operations"
    },
    {
        "id": "safety-system",
        "label": "Safety-System",
        "algorithm": "AES-256",
        "criticality": "SAFE",
        "x": 700.0,
        "y": 450.0,
        "data_lifetime_years": 0,
        "exposure": "internal",
        "category": "Safety & Operations"
    },

    # --- Data & Business (6) ---
    {
        "id": "geo-db",
        "label": "Geo-DB",
        "algorithm": "AES-256",
        "criticality": "SAFE",
        "x": 400.0,
        "y": 450.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Data & Business"
    },
    {
        "id": "customer-db",
        "label": "Customer-DB",
        "algorithm": "AES-256",
        "criticality": "SAFE",
        "x": 100.0,
        "y": 450.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Data & Business"
    },
    {
        "id": "backup-system",
        "label": "Backup-System",
        "algorithm": "RSA-2048",
        "criticality": "MEDIUM",
        "x": 550.0,
        "y": 450.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Data & Business"
    },
    {
        "id": "contract-archive",
        "label": "Contract-Archive",
        "algorithm": "RSA-2048",
        "criticality": "MEDIUM",
        "x": 700.0,
        "y": 350.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Data & Business"
    },
    {
        "id": "finance",
        "label": "Finance",
        "algorithm": "ECDSA",
        "criticality": "HIGH",
        "x": 100.0,
        "y": 250.0,
        "data_lifetime_years": 30,
        "exposure": "internal",
        "category": "Data & Business"
    },
    {
        "id": "email",
        "label": "Email",
        "algorithm": "RSA-2048",
        "criticality": "MEDIUM",
        "x": 100.0,
        "y": 150.0,
        "data_lifetime_years": 20,
        "exposure": "internet",
        "category": "Data & Business"
    }
]

# ============ 28 EDGES (FROM -> TO: DEPENDENT -> DEPENDENCY) ============
MINING_EDGES: List[Dict[str, str]] = [
    {"from": "auth-svc", "to": "ca-root", "type": "TRUSTS"},
    {"from": "dns-svc", "to": "ca-root", "type": "TRUSTS"},
    {"from": "ot-gateway", "to": "ca-root", "type": "TRUSTS"},
    {"from": "vpn-gateway", "to": "ca-root", "type": "TRUSTS"},
    {"from": "ot-gateway", "to": "auth-svc", "type": "DEPENDS_ON"},
    {"from": "email", "to": "auth-svc", "type": "AUTHENTICATES"},
    {"from": "hr-portal", "to": "auth-svc", "type": "AUTHENTICATES"},
    {"from": "ot-gateway", "to": "dns-svc", "type": "DEPENDS_ON"},
    {"from": "finance", "to": "dns-svc", "type": "DEPENDS_ON"},
    {"from": "scada-historian", "to": "dns-svc", "type": "DEPENDS_ON"},
    {"from": "ventilation", "to": "ot-gateway", "type": "DEPENDS_ON"},
    {"from": "gas-monitor", "to": "ot-gateway", "type": "DEPENDS_ON"},
    {"from": "haulage", "to": "ot-gateway", "type": "DEPENDS_ON"},
    {"from": "drilling-sensors", "to": "ot-gateway", "type": "DEPENDS_ON"},
    {"from": "contract-archive", "to": "ot-gateway", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "ventilation", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "gas-monitor", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "haulage", "type": "DEPENDS_ON"},
    {"from": "backup-system", "to": "vpn-gateway", "type": "DEPENDS_ON"},
    {"from": "customer-db", "to": "backup-system", "type": "DEPENDS_ON"},
    {"from": "safety-system", "to": "backup-system", "type": "DEPENDS_ON"},
    {"from": "ca-root", "to": "iot-sensors", "type": "TRUSTS"},
    {"from": "ca-root", "to": "reporting", "type": "TRUSTS"},
    {"from": "geo-db", "to": "email", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "hr-portal", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "finance", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "scada-historian", "type": "DEPENDS_ON"},
    {"from": "geo-db", "to": "contract-archive", "type": "DEPENDS_ON"}
]
