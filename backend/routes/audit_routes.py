import os
import json
import geopandas as gpd
from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.schemas import AuditRequest, AuditResponse
from backend.config import RAW_DIR, PROCESSED_DIR
from backend.audit.segmentation_engine import GeospatialSegmentationEngine
from backend.audit.discrepancy_engine import CorridorDiscrepancyAuditor
from backend.audit.report_generator import AuditReportGenerator

router = APIRouter(prefix="/api/audit", tags=["Compliance Audit"])

@router.post("/run", response_model=AuditResponse)
def run_compliance_audit(request: Optional[AuditRequest] = None):
    """
    Triggers the end-to-end vector audit pipeline:
    1. Segments structures from orthomosaic.
    2. Runs geometric discrepancy checks against the Right-of-Way boundary.
    3. Grades overall corridor compliance.
    """
    try:
        # Load paths or apply synthetic defaults
        ortho_path = (request.orthomosaic_path if request and request.orthomosaic_path 
                      else str(RAW_DIR / "corridor_orthomosaic.tif"))
        row_path = (request.sanctioned_row_path if request and request.sanctioned_row_path 
                    else str(RAW_DIR / "sanctioned_road_boundary.geojson"))

        if not os.path.exists(ortho_path):
            raise HTTPException(status_code=404, detail=f"Orthomosaic raster not found: {ortho_path}")
        if not os.path.exists(row_path):
            raise HTTPException(status_code=404, detail=f"Sanctioned road boundary vector not found: {row_path}")

        # 1. Segment structural footprints from drone GeoTIFF
        segmentation_out = str(PROCESSED_DIR / "detected_structures.geojson")
        segmenter = GeospatialSegmentationEngine()
        structures_gdf = segmenter.extract_footprints_from_raster(ortho_path, segmentation_out)

        # 2. Audit structures against RoW boundary
        flags_out = str(PROCESSED_DIR / "discrepancy_flags.geojson")
        auditor = CorridorDiscrepancyAuditor(row_path)
        audit_results = auditor.audit_structures(
            structures_gdf, 
            target_utm_crs="EPSG:32644", 
            output_flags_path=flags_out
        )

        # 3. Generate summary report and calculate compliance grade
        report = AuditReportGenerator.generate_json_summary(audit_results, project_name="Kanpur Transit Corridor")
        clearance_pct = report["compliance_summary"]["corridor_clearance_percentage"]

        if clearance_pct >= 98:
            grade = "A+"
        elif clearance_pct >= 90:
            grade = "A"
        elif clearance_pct >= 80:
            grade = "B"
        elif clearance_pct >= 60:
            grade = "C"
        else:
            grade = "F"

        # Load GeoJSON geometry payload
        geojson_data = {}
        if os.path.exists(flags_out):
            with open(flags_out, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

        return AuditResponse(
            status="success",
            flags_count=audit_results["total_violations"],
            total_encroachment_m2=audit_results["total_encroachment_area_m2"],
            compliance_grade=grade,
            geojson=geojson_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance audit failed: {str(e)}")

@router.get("/flags")
def get_cached_discrepancy_flags():
    """Returns the cached discrepancy_flags.geojson from the server disk."""
    flags_path = PROCESSED_DIR / "discrepancy_flags.geojson"
    if not flags_path.exists():
        # Return empty geojson structure if not audited yet
        return {
            "type": "FeatureCollection",
            "features": []
        }
        
    try:
        with open(flags_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read discrepancy flags: {str(e)}")
