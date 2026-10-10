"""
MineGuard AI - Cryptographic Scan Route (Phases B1 & B2)
Integrates real multi-backend scanner, NIST PQC enrichment, and database persistence.
"""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.schemas import ScanRequest, ScanResponse, EnrichedFinding, ProjectResponse
from app.engines.scanner import scan_project
from app.engines.pqc_mapper import enrich_findings, get_migration_summary
from app.services.db_service import (
    get_or_create_project,
    save_findings,
    get_projects,
    get_project_by_id,
    get_project_findings,
)

router = APIRouter(prefix="/scan", tags=["Scanning"])

# Default simulated findings when target path does not exist on disk (for frontend demos)
DEFAULT_SIMULATED_FINDINGS = [
    {
        "file": "auth/jwt_service.py",
        "line": 42,
        "algorithm": "RSA-2048",
        "severity": "CRITICAL",
        "context": "public_key = serialization.load_pem_public_key(key_data)",
        "key_size": 2048,
    },
    {
        "file": "scada/modbus_bridge.py",
        "line": 118,
        "algorithm": "ECDSA-P256",
        "severity": "CRITICAL",
        "context": "signer = ec.generate_private_key(ec.SECP256R1())",
        "key_size": 256,
    },
    {
        "file": "mesh/sensor_node.c",
        "line": 75,
        "algorithm": "AES-128",
        "severity": "MEDIUM",
        "context": "aes_128_gcm_encrypt(payload, key, iv);",
        "key_size": 128,
    },
    {
        "file": "db/telemetry_store.py",
        "line": 33,
        "algorithm": "MD5",
        "severity": "HIGH",
        "context": "checksum = hashlib.md5(payload).hexdigest()",
        "key_size": None,
    },
    {
        "file": "gateway/tls_config.yaml",
        "line": 12,
        "algorithm": "RSA-4096",
        "severity": "CRITICAL",
        "context": "ssl_certificate_key: /etc/ssl/rsa4096.key",
        "key_size": 4096,
    },
    {
        "file": "fleet/truck_dispatch.go",
        "line": 88,
        "algorithm": "ECDH",
        "severity": "CRITICAL",
        "context": "curve := ecdh.P256()",
        "key_size": 256,
    },
    {
        "file": "ventilation/fan_plc.py",
        "line": 54,
        "algorithm": "SHA-1",
        "severity": "HIGH",
        "context": "firmware_hash = hashlib.sha1(firmware_bin).hexdigest()",
        "key_size": None,
    },
    {
        "file": "security/vault_pqc.py",
        "line": 10,
        "algorithm": "ML-KEM-768",
        "severity": "SAFE",
        "context": "kem = oqs.KeyEncapsulation('Kyber768')",
        "key_size": 768,
    },
]


@router.post("", response_model=ScanResponse)
async def run_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    """
    Scans a project path for cryptographic assets and quantum vulnerabilities.
    Persists project and findings in database, enriched with NIST PQC migration mappings.
    """
    logger.info(f"POST /api/scan requested for: {payload.project_path} (Type: {payload.scan_type})")

    # 1. Get or create Project in DB
    project = get_or_create_project(db, project_path=payload.project_path, scan_type=payload.scan_type)

    target_path = Path(payload.project_path)
    
    # 2. Run real scanner if path exists on disk, otherwise fall back to simulated dataset
    if target_path.exists():
        scan_result = scan_project(str(target_path), scan_type=payload.scan_type)
        raw_findings = scan_result["findings"]
        source_label = scan_result["source"]
        scan_time_ms = scan_result["scan_time_ms"]
    else:
        logger.info(f"Path '{payload.project_path}' not on disk; generating simulation findings.")
        raw_findings = DEFAULT_SIMULATED_FINDINGS
        source_label = "simulation"
        scan_time_ms = 45

    # 3. Enrich findings with NIST PQC mapping
    enriched_findings = enrich_findings(raw_findings)
    summary = get_migration_summary(enriched_findings)

    # 4. Persist findings to DB
    save_findings(db, project_id=project.id, findings=enriched_findings)

    return ScanResponse(
        findings=enriched_findings,
        count=len(enriched_findings),
        source=source_label,
        scan_time_ms=scan_time_ms,
        summary=summary
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """
    Lists all scanned projects recorded in the system.
    """
    projects = get_projects(db)
    return projects


@router.get("/projects/{project_id}/findings", response_model=List[EnrichedFinding])
async def get_findings_for_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all cryptographic findings associated with a given project ID.
    """
    project = get_project_by_id(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    findings = get_project_findings(db, project_id=project_id)
    return [f.to_dict() for f in findings]
