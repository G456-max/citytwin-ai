import os
from typing import Optional
from fastapi import APIRouter, HTTPException

from backend.schemas import RenderResponse, RenderRequest
from backend.config import RAW_DIR
from backend.visualizer.render_manager import CorridorRenderManager

router = APIRouter(prefix="/api/render", tags=["Real Generative Visualization"])

@router.post("/real", response_model=RenderResponse)
def generate_real_render(request: Optional[RenderRequest] = None):
    """
    Performs blueprint-locked texture rendering utilizing real-world depth buffers
    retrieved from photogrammetric reconstruction maps.
    """
    depth_path = str(RAW_DIR.parent / "real_corridor" / "cad_depth.png")
    
    if not os.path.exists(depth_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Real CAD depth buffer not found at {depth_path}. Please run download_real_data.py first."
        )

    try:
        prompt = request.prompt if request else None
        style = request.style if request else "Realistic Daylight"

        manager = CorridorRenderManager()
        render_results = manager.render_and_encode(
            depth_path=depth_path,
            custom_prompt=prompt,
            style=style
        )
        
        is_fallback = manager.pipeline.use_fallback
        message = "Procedural rendering engine (CPU fallback)" if is_fallback else "Stable Diffusion ControlNet engine (GPU accelerated)"

        return RenderResponse(
            status="success",
            render_time_sec=render_results["render_time_sec"],
            image_base64=render_results["image_base64"],
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real data generative visualization failed: {str(e)}")
