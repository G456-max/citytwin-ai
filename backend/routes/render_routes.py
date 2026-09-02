import os
from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.schemas import RenderRequest, RenderResponse
from backend.config import RAW_DIR
from backend.visualizer.render_manager import CorridorRenderManager

router = APIRouter(prefix="/api/render", tags=["Generative Visualization"])

@router.post("/generate", response_model=RenderResponse)
def generate_render(request: Optional[RenderRequest] = None):
    """
    Ingests CAD depth buffers, applies styling context,
    and returns a base64-encoded photorealistic future render.
    """
    try:
        depth_path = (request.depth_image_path if request and request.depth_image_path 
                      else str(RAW_DIR / "cad_depth.png"))
        
        if not os.path.exists(depth_path):
            raise HTTPException(status_code=404, detail=f"CAD depth buffer not found: {depth_path}")

        prompt = request.prompt if request else None
        style = request.style if request else "Realistic Daylight"

        manager = CorridorRenderManager()
        render_results = manager.render_and_encode(
            depth_path=depth_path,
            custom_prompt=prompt,
            style=style
        )
        
        # Check if the pipeline used fallback mode
        is_fallback = manager.pipeline.use_fallback
        message = "Procedural rendering engine (CPU fallback)" if is_fallback else "Stable Diffusion ControlNet engine (GPU accelerated)"

        return RenderResponse(
            status="success",
            render_time_sec=render_results["render_time_sec"],
            image_base64=render_results["image_base64"],
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generative visualization failed: {str(e)}")
