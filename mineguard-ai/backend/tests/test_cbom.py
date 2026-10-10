"""
Unit Tests for CBOM Ingestion, Generation, and NIST PQC Mapping (Phase B2)
Validates CycloneDX 1.7 CBOM compliance, NIST FIPS 203/204/205 mapping rules,
findings enrichment, and migration summary aggregation.
"""

import json
import pytest
from pathlib import Path

from app.engines.pqc_mapper import (
    PQCStandard,
    map_to_pqc,
    enrich_findings,
    get_migration_summary,
    normalize_algorithm,
)
from app.engines.cbom_parser import (
    CBOMIngester,
    CBOMGenerator,
    ingest_cbom,
    generate_cbom,
)


@pytest.fixture
def sample_valid_cbom(tmp_path: Path) -> Path:
    """Creates a temporary valid CycloneDX 1.7 CBOM file."""
    cbom_file = tmp_path / "valid_cbom.json"
    content = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "serialNumber": "urn:uuid:12345678-1234-5678-1234-567812345678",
        "version": 1,
        "metadata": {
            "component": {
                "name": "mining-sensor-hub",
                "type": "application"
            }
        },
        "components": [
            {
                "type": "cryptographic-asset",
                "name": "RSA",
                "cryptoProperties": {
                    "assetType": "algorithm",
                    "algorithmProperties": {
                        "name": "RSA",
                        "primitive": "signature",
                        "parameterSetIdentifier": "2048"
                    }
                },
                "properties": [
                    {"name": "mineguard:file", "value": "auth/keys.pem"},
                    {"name": "mineguard:line", "value": "15"},
                    {"name": "mineguard:severity", "value": "CRITICAL"}
                ]
            },
            {
                "type": "cryptographic-asset",
                "name": "AES-256",
                "cryptoProperties": {
                    "assetType": "algorithm",
                    "algorithmProperties": {
                        "name": "AES-256",
                        "primitive": "block-cipher",
                        "parameterSetIdentifier": "256"
                    }
                },
                "properties": [
                    {"name": "mineguard:file", "value": "crypto/cipher.py"},
                    {"name": "mineguard:line", "value": "42"},
                    {"name": "mineguard:severity", "value": "SAFE"}
                ]
            }
        ]
    }
    cbom_file.write_text(json.dumps(content), encoding="utf-8")
    return cbom_file


@pytest.fixture
def sample_invalid_cbom(tmp_path: Path) -> Path:
    """Creates a temporary invalid CBOM (wrong bomFormat)."""
    invalid_file = tmp_path / "invalid_cbom.json"
    content = {
        "bomFormat": "SPDX",
        "spdxVersion": "SPDX-2.3",
        "name": "invalid-spec"
    }
    invalid_file.write_text(json.dumps(content), encoding="utf-8")
    return invalid_file


# 1. test_cbom_parse
def test_cbom_parse(sample_valid_cbom: Path):
    result = ingest_cbom(str(sample_valid_cbom))
    assert result["source"] == "cbom"
    assert result["count"] == 2
    assert len(result["findings"]) == 2

    rsa_item = next(f for f in result["findings"] if "RSA" in f["algorithm"].upper())
    assert rsa_item["file"] == "auth/keys.pem"
    assert rsa_item["line"] == 15
    assert "pqc" in rsa_item
    assert rsa_item["pqc"]["kem"] == "ML-KEM-768"


# 2. test_cbom_rejects_invalid
def test_cbom_rejects_invalid(sample_invalid_cbom: Path):
    with pytest.raises(ValueError) as excinfo:
        ingest_cbom(str(sample_invalid_cbom))
    assert "CycloneDX" in str(excinfo.value)


# 3. test_pqc_mapping_rsa (RSA-2048 -> ML-KEM)
def test_pqc_mapping_rsa():
    pqc = map_to_pqc("RSA-2048")
    assert pqc["quantum_safe"] is False
    assert pqc["kem"] == "ML-KEM-768"
    assert pqc["sig"] == "ML-DSA-65"
    assert pqc["standard"] == PQCStandard.FIPS_203.value
    assert pqc["urgency"] == "CRITICAL"


# 4. test_pqc_mapping_ecdsa (ECDSA -> ML-DSA)
def test_pqc_mapping_ecdsa():
    pqc = map_to_pqc("ECDSA-P256")
    assert pqc["quantum_safe"] is False
    assert pqc["sig"] == "ML-DSA-44"
    assert pqc["standard"] == PQCStandard.FIPS_204.value
    assert pqc["urgency"] == "CRITICAL"


# 5. test_pqc_mapping_safe (AES-256 -> quantum_safe=True)
def test_pqc_mapping_safe():
    pqc = map_to_pqc("AES-256")
    assert pqc["quantum_safe"] is True
    assert pqc["effort_weeks"] == 0
    assert pqc["urgency"] == "NONE"


# 6. test_pqc_mapping_pqc (ML-KEM -> quantum_safe=True)
def test_pqc_mapping_pqc():
    pqc = map_to_pqc("ML-KEM")
    assert pqc["quantum_safe"] is True
    assert pqc["standard"] == PQCStandard.FIPS_203.value
    assert pqc["effort_weeks"] == 0


# 7. test_enrich_findings
def test_enrich_findings():
    raw = [
        {"file": "modbus.py", "line": 50, "algorithm": "RSA-2048", "severity": "CRITICAL"},
        {"file": "sensor.py", "line": 80, "algorithm": "AES-256", "severity": "SAFE"}
    ]
    enriched = enrich_findings(raw)
    assert len(enriched) == 2
    assert "pqc" in enriched[0]
    assert enriched[0]["pqc"]["kem"] == "ML-KEM-768"
    assert "pqc" in enriched[1]
    assert enriched[1]["pqc"]["quantum_safe"] is True


# 8. test_migration_summary
def test_migration_summary():
    raw = [
        {"file": "a.py", "line": 1, "algorithm": "RSA-2048", "severity": "CRITICAL"},
        {"file": "b.py", "line": 2, "algorithm": "ECDSA-P256", "severity": "CRITICAL"},
        {"file": "c.py", "line": 3, "algorithm": "AES-256", "severity": "SAFE"}
    ]
    enriched = enrich_findings(raw)
    summary = get_migration_summary(enriched)

    assert summary["total_findings"] == 3
    assert summary["quantum_safe"] == 1
    assert summary["quantum_vulnerable"] == 2
    assert summary["total_effort_weeks"] >= 12
    assert PQCStandard.FIPS_203.value in summary["by_standard"]
    assert PQCStandard.FIPS_204.value in summary["by_standard"]
    assert summary["by_urgency"].get("CRITICAL", 0) == 2


# 9. test_cbom_generate (CycloneDX 1.7 format)
def test_cbom_generate():
    findings = [
        {"file": "gateway.py", "line": 10, "algorithm": "RSA-2048", "severity": "CRITICAL", "key_size": 2048},
        {"file": "hash.py", "line": 25, "algorithm": "MD5", "severity": "HIGH", "key_size": None}
    ]
    cbom = generate_cbom("mine-haul-network", findings)

    assert cbom["bomFormat"] == "CycloneDX"
    assert cbom["specVersion"] == "1.7"
    assert cbom["serialNumber"].startswith("urn:uuid:")
    assert cbom["metadata"]["component"]["name"] == "mine-haul-network"
    assert len(cbom["components"]) == 2

    comp1 = cbom["components"][0]
    assert comp1["type"] == "cryptographic-asset"
    assert comp1["name"] == "RSA-2048"
    assert comp1["quantumVulnerable"] is True
    assert comp1["recommendedReplacement"] in ["ML-DSA-65", "ML-KEM-768"]
