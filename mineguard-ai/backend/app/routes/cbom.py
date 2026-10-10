"""
MineGuard AI - CBOM Route (Phase B2)
Handles CycloneDX 1.7 CBOM ingestion, PQC enrichment, and export.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from loguru import logger

from app.database import get_db
from app.models.schemas import (
    CBOMIngestRequest,
    CBOMIngestResponse,
    Finding,
    EnrichedFinding,
    MigrationSummary,
)
from app.engines.cbom_parser import ingest_cbom, generate_cbom
from app.engines.pqc_mapper import enrich_findings, get_migration_summary
from app.services.db_service import get_project_by_id, get_project_findings

router = APIRouter(prefix="/cbom", tags=["CBOM"])


@router.post("/ingest", response_model=CBOMIngestResponse)
async def ingest_cbom_endpoint(payload: CBOMIngestRequest):
    """
    Ingests an external CycloneDX CBOM JSON file, validates schema compliance,
    extracts cryptographic assets, and enriches them with NIST PQC migration targets.
    """
    logger.info(f"POST /api/cbom/ingest requested for: {payload.cbom_path}")

    try:
        result = ingest_cbom(payload.cbom_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CBOM file not found at path: {payload.cbom_path}")
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.error(f"CBOM parsing failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to process CBOM: {str(exc)}")

    return CBOMIngestResponse(
        findings=result["findings"],
        count=result["count"],
        source=result["source"],
        summary=result["summary"],
        cbom_metadata=result["cbom_metadata"]
    )


@router.get("/export/{project_id}")
async def export_cbom_endpoint(project_id: int, db: Session = Depends(get_db)):
    """
    Generates and exports a CycloneDX 1.7 compliant CBOM for a given project ID.
    Returns JSON download with Content-Disposition header.
    """
    logger.info(f"GET /api/cbom/export/{project_id} requested")

    project = get_project_by_id(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    finding_records = get_project_findings(db, project_id=project_id)
    findings = [f.to_dict() for f in finding_records]

    cbom_data = generate_cbom(name=project.name, findings=findings)
    filename = f"{project.name.replace(' ', '_')}-cbom.json"

    return JSONResponse(
        content=cbom_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/enrich-findings")
async def enrich_findings_endpoint(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Utility endpoint to enrich an arbitrary list of cryptographic findings with NIST PQC mappings.
    """
    raw_findings = payload.get("findings", [])
    enriched = enrich_findings(raw_findings)
    summary = get_migration_summary(enriched)

    return {
        "findings": enriched,
        "count": len(enriched),
        "summary": summary
    }
