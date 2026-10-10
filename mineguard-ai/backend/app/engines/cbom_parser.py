"""
MineGuard AI - CycloneDX 1.7 Cryptography Bill of Materials (CBOM) Engine (Phase B2)
Parses external CycloneDX CBOMs and generates compliant CycloneDX 1.7 CBOMs
for safety-critical mining and OT infrastructure assets.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.engines.pqc_mapper import map_to_pqc, enrich_findings, get_migration_summary


class CBOMIngester:
    """
    Ingests and validates CycloneDX Cryptography Bill of Materials (CBOM) JSON files.
    """

    def __init__(self, cbom_path: str):
        self.cbom_path = Path(cbom_path)

    def parse(self) -> Dict[str, Any]:
        """
        Parses CBOM, validates CycloneDX schema compliance, and extracts cryptographic findings.
        Raises ValueError if invalid CBOM format.
        """
        if not self.cbom_path.exists():
            raise FileNotFoundError(f"CBOM file not found: {self.cbom_path}")

        try:
            with open(self.cbom_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as err:
            raise ValueError(f"Invalid JSON file in CBOM: {err}")

        # Validate CycloneDX specification
        if data.get("bomFormat") != "CycloneDX":
            raise ValueError(f"Invalid CBOM: 'bomFormat' must be 'CycloneDX', got '{data.get('bomFormat')}'")

        spec_version = data.get("specVersion", "1.7")
        serial_number = data.get("serialNumber", "")
        components = data.get("components", [])

        findings: List[Dict[str, Any]] = []

        for comp in components:
            comp_type = comp.get("type")
            crypto_props = comp.get("cryptoProperties", {})

            # Ingest if designated as cryptographic asset or contains cryptoProperties
            if comp_type == "cryptographic-asset" or crypto_props:
                algo_props = crypto_props.get("algorithmProperties", {})
                algo_name = algo_props.get("name") or comp.get("name") or "UNKNOWN"

                # Extract custom properties
                props = {p.get("name"): p.get("value") for p in comp.get("properties", [])}

                file_path = props.get("mineguard:file") or comp.get("purl", "unknown_source")
                line_val = props.get("mineguard:line")
                try:
                    line_no = int(line_val) if line_val is not None else 1
                except (ValueError, TypeError):
                    line_no = 1

                key_size = None
                param_id = algo_props.get("parameterSetIdentifier") or props.get("mineguard:keySize")
                if param_id:
                    try:
                        key_size = int(param_id)
                    except (ValueError, TypeError):
                        pass

                severity = props.get("mineguard:severity")
                if not severity:
                    pqc_meta = map_to_pqc(algo_name)
                    severity = "CRITICAL" if not pqc_meta["quantum_safe"] else "SAFE"

                findings.append({
                    "file": file_path,
                    "line": line_no,
                    "algorithm": algo_name,
                    "severity": severity,
                    "context": props.get("mineguard:context") or f"CBOM component: {comp.get('name')}",
                    "key_size": key_size
                })

        enriched = enrich_findings(findings)
        summary = get_migration_summary(enriched)

        return {
            "findings": enriched,
            "count": len(enriched),
            "source": "cbom",
            "summary": summary,
            "cbom_metadata": {
                "specVersion": spec_version,
                "serialNumber": serial_number,
                "total_components": len(components)
            }
        }


class CBOMGenerator:
    """
    Constructs CycloneDX 1.7 compliant Cryptography Bill of Materials (CBOM).
    """

    def __init__(self, project_name: str = "mining-project"):
        self.project_name = project_name

    def generate(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a full CycloneDX 1.7 CBOM dictionary including cryptoProperties,
        NIST FIPS migration mappings, and quantum vulnerability metrics.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        cbom_uuid = str(uuid.uuid4())

        components: List[Dict[str, Any]] = []

        for idx, f in enumerate(findings, start=1):
            algo = f.get("algorithm", "UNKNOWN")
            pqc = f.get("pqc") or map_to_pqc(algo)
            severity = f.get("severity", "CRITICAL" if not pqc["quantum_safe"] else "SAFE")
            key_size = f.get("key_size")

            comp_id = f"crypto-asset-{idx}-{algo.lower()}"

            # Determine cryptographic primitive
            primitive = "signature"
            if pqc.get("kem"):
                primitive = "kem"
            elif pqc.get("symmetric") or "AES" in algo.upper():
                primitive = "block-cipher"
            elif pqc.get("hash") or "SHA" in algo.upper() or "MD5" in algo.upper():
                primitive = "message-digest"

            component_entry: Dict[str, Any] = {
                "type": "cryptographic-asset",
                "bom-ref": comp_id,
                "name": algo,
                "version": "1.0",
                "cryptoProperties": {
                    "assetType": "algorithm",
                    "algorithmProperties": {
                        "name": algo,
                        "primitive": primitive,
                        "parameterSetIdentifier": str(key_size) if key_size else algo
                    }
                },
                "properties": [
                    {"name": "mineguard:file", "value": str(f.get("file", ""))},
                    {"name": "mineguard:line", "value": str(f.get("line", 1))},
                    {"name": "mineguard:severity", "value": severity},
                    {"name": "mineguard:quantumSafe", "value": str(pqc["quantum_safe"]).lower()},
                    {"name": "mineguard:nistStandard", "value": str(pqc.get("standard", "None"))},
                    {"name": "mineguard:migrationEffortWeeks", "value": str(pqc.get("effort_weeks", 0))}
                ],
                "quantumVulnerable": not pqc["quantum_safe"],
                "recommendedReplacement": (
                    pqc.get("sig") or pqc.get("kem") or pqc.get("symmetric") or pqc.get("hash") or "N/A"
                )
            }
            components.append(component_entry)

        cbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.7",
            "serialNumber": f"urn:uuid:{cbom_uuid}",
            "version": 1,
            "metadata": {
                "timestamp": now_iso,
                "tools": [
                    {
                        "vendor": "MineGuard",
                        "name": "MineGuard AI",
                        "version": "0.1.0"
                    }
                ],
                "component": {
                    "type": "application",
                    "name": self.project_name
                }
            },
            "components": components
        }

        return cbom


# ============ CONVENIENCE FUNCTIONS ============
def ingest_cbom(path: str) -> Dict[str, Any]:
    """Convenience wrapper to parse and enrich CBOM file."""
    ingester = CBOMIngester(path)
    return ingester.parse()


def generate_cbom(name: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience wrapper to generate CycloneDX 1.7 CBOM."""
    generator = CBOMGenerator(project_name=name)
    return generator.generate(findings)
