"""
MineGuard AI - Synthetic Mining Dataset Generator (Phase C2)
Generates statistically representative synthetic cryptographic findings
specifically tailored to mining operational technology (SCADA, PLC, mesh networks, fleet telemetry).

DISCLAIMER:
This dataset is strictly SYNTHETIC for pipeline verification and offline ML benchmarking.
Because real-world post-quantum cyber incident datasets do not yet exist,
no claims of empirical production breach accuracy should be made from models
trained solely on synthetic data.
"""

from typing import List, Dict, Any
import numpy as np


class SyntheticDatasetGenerator:
    """
    Synthesizes realistic cryptographic inventories for mining OT environments.
    """

    ALGORITHM_SPECS = [
        # (algorithm, weight, severity, key_size, context_template)
        ("RSA-2048", 0.25, "CRITICAL", 2048, "cert = rsa.generate_private_key(public_exponent=65537, key_size=2048)"),
        ("RSA-4096", 0.10, "CRITICAL", 4096, "root_ca = load_pem_x509_certificate(data) # RSA-4096 signature"),
        ("ECDSA", 0.20, "CRITICAL", 256, "signer = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)"),
        ("MD5", 0.05, "HIGH", None, "checksum = hashlib.md5(scada_packet).hexdigest()"),
        ("SHA-1", 0.05, "HIGH", None, "digest = hashlib.sha1(firmware_image).digest()"),
        ("AES-256", 0.20, "SAFE", 256, "cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)"),
        ("SHA-256", 0.15, "SAFE", None, "audit_hash = hashlib.sha256(haul_telemetry).hexdigest()"),
    ]

    MINING_SUBSYSTEMS = [
        "scada/modbus_concentrator.py",
        "scada/plc_auth_gateway.py",
        "ventilation/fan_speed_controller.c",
        "ventilation/methane_sensor_mesh.rs",
        "fleet/haul_truck_dispatch.go",
        "fleet/autonomous_dozer_telemetry.py",
        "drilling/blast_pattern_planner.cpp",
        "tailings/dam_pore_pressure_monitor.py",
        "hoist/vertical_shaft_signaling.py",
        "conveyor/belt_weightometer_bridge.py",
        "auth/mine_worker_rfid_badges.yaml",
        "telemetry/geo_seismic_database.py"
    ]

    CRITICALITY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    EXPOSURE_LEVELS = ["EXTERNAL", "PERIMETER", "INTERNAL", "ISOLATED"]

    def __init__(self, seed: int = 42):
        self.seed = seed

    def generate(self, n_samples: int = 1000, seed: int = 42) -> List[Dict[str, Any]]:
        """
        Generates n_samples synthetic findings adhering to target algorithm distributions.
        """
        rng = np.random.default_rng(seed)

        algos = [s[0] for s in self.ALGORITHM_SPECS]
        weights = [s[1] for s in self.ALGORITHM_SPECS]
        spec_map = {s[0]: s for s in self.ALGORITHM_SPECS}

        chosen_algos = rng.choice(algos, size=n_samples, p=weights)
        findings: List[Dict[str, Any]] = []

        for idx, algo in enumerate(chosen_algos, start=1):
            spec = spec_map[algo]
            subsystem = str(rng.choice(self.MINING_SUBSYSTEMS))
            line_no = int(rng.integers(10, 850))
            crit = str(rng.choice(self.CRITICALITY_LEVELS, p=[0.4, 0.35, 0.2, 0.05]))
            exposure = str(rng.choice(self.EXPOSURE_LEVELS, p=[0.25, 0.35, 0.3, 0.1]))
            shelf_life = float(rng.uniform(5.0, 30.0))

            findings.append({
                "file": subsystem,
                "line": line_no,
                "algorithm": spec[0],
                "severity": spec[2],
                "key_size": spec[3],
                "context": spec[4],
                "criticality": crit,
                "exposure": exposure,
                "data_lifetime_years": shelf_life,
                "dataset_type": "SYNTHETIC",
                "sample_id": f"synthetic-{idx}"
            })

        return findings
