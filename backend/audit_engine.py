import os
import json
from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.schemas import AuditResponse
from backend.config import RAW_DIR, PROCESSED_DIR
from backend.audit.segmentation_engine import GeospatialSegmentationEngine
from backend.audit.discrepancy_engine import CorridorDiscrepancyAuditor
from backend.audit.report_generator import AuditReportGenerator

router = APIRouter(prefix="/api/audit", tags=["Real Compliance Audit"])

@router.post("/real", response_model=AuditResponse)
def run_real_compliance_audit():
    """
    Executes compliance audits strictly on real-world geospatial datasets:
    1. Loads the downloaded real GeoTIFF and runs segmentation.
    2. Runs vector discrepancy math on UTM metric projection.
    3. Outputs real compliance indices and WGS84 GeoJSON footprints.
    """
    ortho_path = str(RAW_DIR.parent / "real_corridor" / "corridor_orthomosaic.tif")
    row_path = str(RAW_DIR.parent / "real_corridor" / "sanctioned_road_boundary.geojson")
    
    if not os.path.exists(ortho_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Authentic GeoTIFF not found at {ortho_path}. Please run download_real_data.py first."
        )
    if not os.path.exists(row_path):
        raise HTTPException(
            status_code=404, 
            detail=f"OSM Right-of-Way boundary not found at {row_path}. Please run download_real_data.py first."
        )

    try:
        # 1. Run zero-shot CV/SAMGeo segmentation on real raster pixels
        real_struct_out = str(PROCESSED_DIR / "real_detected_structures.geojson")
        segmenter = GeospatialSegmentationEngine()
        structures_gdf = segmenter.extract_footprints_from_raster(ortho_path, real_struct_out)

        # 2. Perform spatial overlay calculations
        real_flags_out = str(PROCESSED_DIR / "real_discrepancy_flags.geojson")
        auditor = CorridorDiscrepancyAuditor(row_path)
        audit_results = auditor.audit_structures(
            structures_gdf,
            target_utm_crs="EPSG:32644",
            output_flags_path=real_flags_out
        )

        # 3. Generate summary report & compliance grade
        report = AuditReportGenerator.generate_json_summary(audit_results, project_name="Kanpur Real Corridor Study")
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

        # Read output GeoJSON layer
        geojson_data = {}
        if os.path.exists(real_flags_out):
            with open(real_flags_out, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

        return AuditResponse(
            status="success",
            flags_count=audit_results["total_violations"],
            total_encroachment_m2=audit_results["total_encroachment_area_m2"],
            compliance_grade=grade,
            geojson=geojson_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real data compliance audit execution failed: {str(e)}")
