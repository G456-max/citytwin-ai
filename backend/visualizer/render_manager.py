import os
import time
import io
import base64
from PIL import Image
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from backend.visualizer.depth_preprocessor import DepthBufferProcessor
from backend.visualizer.controlnet_pipeline import CADConstrainedDiffusionPipeline
from backend.config import PROCESSED_DIR

class CorridorRenderManager:
    """Orchestrates CAD depth buffer ingestion, prompt structuring, texture rendering, and base64 streaming."""

    def __init__(self, pipeline: Optional[CADConstrainedDiffusionPipeline] = None):
        """Initializes dependencies (preprocessor, ControlNet pipeline)."""
        self.processor = DepthBufferProcessor()
        self.pipeline = pipeline or CADConstrainedDiffusionPipeline()

    def build_curated_prompt(
        self, 
        base_prompt: Optional[str] = None, 
        time_of_day: str = "day", 
        infrastructure_type: str = "flyover"
    ) -> Tuple[str, str]:
        """
        Formulates optimized prompt templates for Stable Diffusion + ControlNet.

        Args:
            base_prompt: Overriding prompt if provided.
            time_of_day: Rendering context ("day", "night", "rain", "green").
            infrastructure_type: Category ("flyover", "road", "rail").

        Returns:
            Tuple containing (positive_prompt, negative_prompt).
        """
        if base_prompt:
            positive = base_prompt
        else:
            if time_of_day == "night":
                positive = (
                    f"night view of modern city {infrastructure_type}, glowing streetlights, "
                    f"dark asphalt pavement, headlight trails, neon city backdrop, high-end 3D visualization, "
                    f"8k resolution, cinematic lighting"
                )
            elif time_of_day == "rain":
                positive = (
                    f"wet asphalt highway {infrastructure_type}, heavy rainstorm, photorealistic "
                    f"reflections on wet road surface, overcast dark sky, cinematic moody lighting, "
                    f"realistic water puddles, 8k resolution"
                )
            elif time_of_day == "green":
                positive = (
                    f"modern eco-friendly {infrastructure_type} bridge corridor with lush vertical gardens, "
                    f"dense green walls, flower pots along safety barriers, solar panels, clean daylight, "
                    f"vibrant street trees, 8k resolution"
                )
            else:  # day
                positive = (
                    f"photorealistic modern asphalt 4-lane elevated highway {infrastructure_type}, "
                    f"crisp white lane markings, clean concrete curbs, vibrant street trees, "
                    f"realistic sunny daylight, 8k resolution, cinematic urban infrastructure"
                )

        negative = (
            "blurry, warped lanes, distorted road geometry, floating objects, low quality, "
            "cartoon, drawing, bad perspective, unrealistic lane widths, altered bridge curves, "
            "deformed structures, extra roads"
        )
        
        return positive, negative

    def render_and_encode(
        self, 
        depth_path: str, 
        custom_prompt: Optional[str] = None, 
        style: str = "Realistic Daylight"
    ) -> Dict[str, Any]:
        """
        Preprocesses depth maps, triggers ControlNet, saves output, and returns Base64.

        Args:
            depth_path: Path to raw depth map image.
            custom_prompt: Optional prompt modifier.
            style: Selected visual theme style.

        Returns:
            Dictionary containing compliance metadata, Base64 image, and metrics.
        """
        start_time = time.time()

        # 1. Normalize depth map
        norm_depth = self.processor.normalize_depth_map(depth_path, target_size=(512, 512))

        # 2. Build prompt templates based on style
        style_lower = style.lower()
        if "night" in style_lower:
            time_of_day = "night"
        elif "rain" in style_lower or "monsoon" in style_lower or "wet" in style_lower:
            time_of_day = "rain"
        elif "green" in style_lower or "eco" in style_lower:
            time_of_day = "green"
        else:
            time_of_day = "day"

        pos_prompt, neg_prompt = self.build_curated_prompt(
            base_prompt=custom_prompt,
            time_of_day=time_of_day,
            infrastructure_type="flyover"
        )

        # 3. Execute geometry-locked neural synthesis
        synthesized_image = self.pipeline.synthesize_contextual_view(
            depth_image=norm_depth,
            prompt=pos_prompt,
            negative_prompt=neg_prompt,
            controlnet_conditioning_scale=1.0,
            num_steps=20
        )

        # 4. Save processed output to disk
        output_name = "sanctioned_future_render.png"
        output_path = PROCESSED_DIR / output_name
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        synthesized_image.save(output_path, format="PNG")

        # 5. Base64 encode for web dashboard consumption
        buffered = io.BytesIO()
        synthesized_image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        base64_data = f"data:image/png;base64,{img_base64}"

        render_time = time.time() - start_time

        return {
            "status": "success",
            "render_time_sec": round(render_time, 3),
            "output_path": str(output_path.resolve()),
            "image_base64": base64_data
        }
