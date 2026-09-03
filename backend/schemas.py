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
    baseline_drone_base64: Optional[str] = None
    sensing_telemetry: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class SystemHealthResponse(BaseModel):
    status: str
    gpu_available: bool
    device_name: str
    loaded_engines: List[str]

class DynamicAuditRequest(BaseModel):
    lat: float
    lon: float
    zoom: Optional[int] = 16
    bbox: Optional[List[float]] = None # [min_lat, min_lon, max_lat, max_lon]
    location_name: Optional[str] = None
    road_width_m: Optional[float] = 30.0

class DynamicAuditResponse(BaseModel):
    status: str
    location_name: str
    lat: float
    lon: float
    utm_zone: str
    flags_count: int
    total_encroachment_m2: float
    compliance_grade: str
    geojson: Dict[str, Any]
    all_structures_geojson: Optional[Dict[str, Any]] = None
    row_geojson: Optional[Dict[str, Any]] = None
    canopy_geojson: Optional[Dict[str, Any]] = None
    canopy_loss_m2: float
    trees_mandated_count: int

class SimulateEncroachmentRequest(BaseModel):
    lat: float
    lon: float
    structure_name: Optional[str] = "Simulated Roadside Structure"
    structure_type: Optional[str] = "Commercial Encroachment"
    width_m: Optional[float] = 25.0
    depth_m: Optional[float] = 18.0

class SimulateEncroachmentResponse(BaseModel):
    status: str
    encroachment_id: str
    structure_name: str
    encroached_area_m2: float
    max_penetration_m: float
    infringement_percentage: float
    compliance_grade: str
    feature: Dict[str, Any]
