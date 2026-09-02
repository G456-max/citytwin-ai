import os
import time
import torch
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pathlib import Path
from typing import Optional

from backend.schemas import SystemHealthResponse, AuditResponse, RenderRequest, RenderResponse
from backend.config import BASE_DIR, RAW_DIR, PROCESSED_DIR

# Import Core Engines
from backend.ingestion.raster_handler import OrthomosaicHandler
from backend.audit.segmentation_engine import GeospatialSegmentationEngine
from backend.audit.discrepancy_engine import CorridorDiscrepancyAuditor
from backend.audit.tree_canopy_audit import TreeCanopyAuditor
from backend.visualizer.controlnet_engine import BlueprintLockedVisualizer, HAS_DIFFUSERS
from backend.reports.pdf_generator import CompliancePDFGenerator

app = FastAPI(
    title="CityTwin AI Compliance Server",
    description="Enterprise server for municipal highway Right-of-Way compliance auditing and visual verification.",
    version="3.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths configuration
ortho_path = str(RAW_DIR.parent / "real_corridor" / "corridor_orthomosaic.tif")
row_path = str(RAW_DIR.parent / "real_corridor" / "sanctioned_road_boundary.geojson")
depth_path = str(RAW_DIR.parent / "real_corridor" / "real_corridor_depth.png")

# Initialize rendering pipeline
visualizer = BlueprintLockedVisualizer()

# -------------------------------------------------------------------------
# 1. Health Diagnostics Route
# -------------------------------------------------------------------------
@app.get("/api/health", response_model=SystemHealthResponse)
def get_system_health():
    """Returns computational device details and system readiness flags."""
    try:
        gpu_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if gpu_available else "CPU Execution Core"
    except Exception:
        gpu_available = False
        device_name = "CPU Core"
        
    loaded_engines = ["GCP_Anchor_Engine", "Raster_Metadata_Inspector", "UTM_Discrepancy_Engine", "Vegetation_Canopy_Auditor"]
    if HAS_DIFFUSERS and gpu_available:
        loaded_engines.append("Stable_Diffusion_ControlNet_Depth")
    else:
        loaded_engines.append("Procedural_Visual_Synthesis_Fallback")

    return SystemHealthResponse(
        status="healthy",
        gpu_available=gpu_available,
        device_name=device_name,
        loaded_engines=loaded_engines
    )

# -------------------------------------------------------------------------
# 2. Main Audit Pipeline Route
# -------------------------------------------------------------------------
@app.post("/api/audit/run", response_model=AuditResponse)
def run_compliance_audit():
    """Executes boundary audits using Kanpur/Rajamahendravaram coordinate boundaries."""
    if not os.path.exists(ortho_path):
        raise HTTPException(status_code=404, detail="Real-world GeoTIFF orthomosaic missing. Run download_real_data.py first.")
    if not os.path.exists(row_path):
        raise HTTPException(status_code=404, detail="OSM corridor boundary missing. Run download_real_data.py first.")

    try:
        # Segment footprints from orthomosaic
        real_struct_out = str(PROCESSED_DIR / "real_detected_structures.geojson")
        segmenter = GeospatialSegmentationEngine()
        structures_gdf = segmenter.extract_footprints_from_raster(ortho_path, real_struct_out)

        # Audit against road Right-of-Way in UTM EPSG:32644
        real_flags_out = str(PROCESSED_DIR / "discrepancy_flags.geojson")
        auditor = CorridorDiscrepancyAuditor(row_path)
        audit_results = auditor.audit_structures(
            structures_gdf,
            target_utm_crs="EPSG:32644",
            output_flags_path=real_flags_out
        )

        # Calculate clearance index grade
        total_encroached_m2 = audit_results.get("total_encroachment_area_m2", 0.0)
        if total_encroached_m2 == 0:
            grade = "A+"
        elif total_encroached_m2 < 30:
            grade = "A"
        elif total_encroached_m2 < 100:
            grade = "B"
        elif total_encroached_m2 < 300:
            grade = "C"
        else:
            grade = "F"

        # Load generated GeoJSON payload
        geojson_data = {}
        if os.path.exists(real_flags_out):
            with open(real_flags_out, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

        return AuditResponse(
            status="success",
            flags_count=audit_results["total_violations"],
            total_encroachment_m2=total_encroached_m2,
            compliance_grade=grade,
            geojson=geojson_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance audit pipeline error: {str(e)}")

# -------------------------------------------------------------------------
# 3. Visual Texture Synthesizer Route
# -------------------------------------------------------------------------
@app.post("/api/render/generate", response_model=RenderResponse)
def generate_visual_render(request: Optional[RenderRequest] = None):
    """Synthesizes high-fidelity contextual views bound to the spatial DEM elevation maps."""
    if not os.path.exists(depth_path):
        raise HTTPException(status_code=404, detail="CAD DEM depth buffer missing. Run download_real_data.py first.")

    try:
        from PIL import Image
        import io
        import base64

        prompt = request.prompt if request else None
        style = request.style if request else "Realistic Daylight"
        
        # Format prompts based on selected style preset
        style_lower = style.lower()
        if "night" in style_lower:
            pos_prompt = "night view of city highway corridor, glowing streetlights, dark asphalt, headlights, 8k resolution"
        elif "rain" in style_lower or "monsoon" in style_lower:
            pos_prompt = "wet asphalt highway corridor, rainstorm, reflections on wet road surface, overcast sky, 8k resolution"
        elif "green" in style_lower or "eco" in style_lower:
            pos_prompt = "modern highway bridge corridor with vertical gardens, green walls, potted plants, daylight, 8k resolution"
        else:
            pos_prompt = "photorealistic modern asphalt 4-lane highway corridor, crisp white lane markings, curbs, trees, sunny day, 8k resolution"

        neg_prompt = "blurry, warped lanes, distorted geometry, cartoon, low quality"

        # Load depth buffer
        depth_img = Image.open(depth_path)
        
        start_time = time.time()
        synthesized = visualizer.synthesize_contextual_view(
            depth_image=depth_img,
            prompt=pos_prompt,
            negative_prompt=neg_prompt,
            controlnet_conditioning_scale=1.0,
            num_steps=20
        )
        render_time = time.time() - start_time

        # Save to disk
        out_img_path = PROCESSED_DIR / "sanctioned_future_render.png"
        os.makedirs(os.path.dirname(out_img_path), exist_ok=True)
        synthesized.save(out_img_path, format="PNG")

        # Encode to Base64
        buffered = io.BytesIO()
        synthesized.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_data = f"data:image/png;base64,{img_base64}"

        message = "Procedural CPU fallback" if visualizer.use_fallback else "Stable Diffusion GPU acceleration"

        return RenderResponse(
            status="success",
            render_time_sec=round(render_time, 3),
            image_base64=base64_data,
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Texture synthesis pipeline error: {str(e)}")

# -------------------------------------------------------------------------
# 4. Tree Canopy Addons Route
# -------------------------------------------------------------------------
@app.post("/api/addons/trees")
def run_tree_canopy_audit():
    """Extracts vegetation cover and calculates forest canopy clearing areas."""
    if not os.path.exists(ortho_path) or not os.path.exists(row_path):
        raise HTTPException(status_code=404, detail="Required geospatial layers missing. Ingest datasets first.")

    try:
        canopy_out = str(PROCESSED_DIR / "canopy_loss.geojson")
        results = TreeCanopyAuditor.audit_canopy_loss(
            orthomosaic_path=ortho_path,
            row_path=row_path,
            output_geojson_path=canopy_out
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Canopy auditor pipeline error: {str(e)}")

# -------------------------------------------------------------------------
# 5. Executive PDF Report Download Route
# -------------------------------------------------------------------------
@app.get("/api/reports/download-pdf")
def download_compliance_pdf():
    """Generates and streams the formal municipal compliance report PDF."""
    try:
        # 1. Run audit calculations to gather data
        real_struct_out = str(PROCESSED_DIR / "real_detected_structures.geojson")
        segmenter = GeospatialSegmentationEngine()
        structures_gdf = segmenter.extract_footprints_from_raster(ortho_path, real_struct_out)

        auditor = CorridorDiscrepancyAuditor(row_path)
        real_flags_out = str(PROCESSED_DIR / "discrepancy_flags.geojson")
        audit_results = auditor.audit_structures(
            structures_gdf,
            target_utm_crs="EPSG:32644",
            output_flags_path=real_flags_out
        )

        # 2. Run canopy loss indicators
        canopy_out = str(PROCESSED_DIR / "canopy_loss.geojson")
        canopy_results = TreeCanopyAuditor.audit_canopy_loss(
            orthomosaic_path=ortho_path,
            row_path=row_path,
            output_geojson_path=canopy_out
        )

        # 3. Generate ReportLab PDF
        pdf_out = str(PROCESSED_DIR / "compliance_audit_report.pdf")
        pdf_path = CompliancePDFGenerator.generate_report(
            audit_results=audit_results,
            canopy_results=canopy_results,
            project_name="Rajamahendravaram Godavari Bund widening",
            output_pdf_path=pdf_out
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="Municipal_Corridor_Compliance_Report.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF report generation failed: {str(e)}")

# -------------------------------------------------------------------------
# 6. Serving Static Frontend Viewport
# -------------------------------------------------------------------------
frontend_path = BASE_DIR / "frontend"
index_html_path = frontend_path / "index.html"

@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Serves the main frontend viewport HTML page."""
    if not index_html_path.exists():
        raise HTTPException(status_code=404, detail="Index.html not found.")
    return FileResponse(str(index_html_path))

# Mount static asset directory to serve CSS and JS
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
print(f"Mounted static folder: {frontend_path.resolve()}")
