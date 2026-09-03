from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AuditRequest(BaseModel):
    orthomosaic_path: Optional[str] = None
    sanctioned_row_path: Optional[str] = None

class AuditResponse(BaseModel):
    status: str
    flags_count: int
    total_encroachment_m2: float
    compliance_grade: str
    geojson: Dict[str, Any]
    all_structures_geojson: Optional[Dict[str, Any]] = None
    row_geojson: Optional[Dict[str, Any]] = None

class RenderRequest(BaseModel):
    depth_image_path: Optional[str] = None
    prompt: Optional[str] = None
    style: Optional[str] = "Realistic Daylight"
    num_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5

class RenderResponse(BaseModel):
    status: str
    render_time_sec: float
    image_base64: str
    message: Optional[str] = None

class SystemHealthResponse(BaseModel):
    status: str
    gpu_available: bool
    device_name: str
    loaded_engines: List[str]
