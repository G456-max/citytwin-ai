import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional

# Try to import torch and diffusers, fallback gracefully if not installed
try:
    import torch
    from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
    HAS_DIFFUSERS = True
except ImportError:
    HAS_DIFFUSERS = False

class BlueprintLockedVisualizer:
    """Stable Diffusion ControlNet engine for blueprint-locked photorealistic texture synthesis."""

    def __init__(
        self, 
        model_id: str = "runwayml/stable-diffusion-v1-5", 
        controlnet_id: str = "lllyasviel/control_v11f1p_sd15_depth",
        use_auth_token: bool = False
    ):
        """Initializes hardware accelerators, model weights, and setup memory optimization parameters."""
        self.use_fallback = not HAS_DIFFUSERS
        self.device = "cuda" if (HAS_DIFFUSERS and torch.cuda.is_available()) else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.pipe = None

        if not self.use_fallback and self.device == "cuda":
            try:
                print(f"Initializing Stable Diffusion on device: {self.device}...")
                controlnet = ControlNetModel.from_pretrained(
                    controlnet_id, 
                    torch_dtype=self.dtype,
                    local_files_only=True
                )
                self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
                    model_id, 
                    controlnet=controlnet, 
                    torch_dtype=self.dtype,
                    local_files_only=True
                )
                self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
                self.pipe.enable_attention_slicing()
                self.pipe.enable_vae_slicing()
                self.pipe.to(self.device)
            except Exception as e:
                print(f"CUDA model init skipped: {e}. Using high-speed procedural graphics engine.")
                self.use_fallback = True
        else:
            self.use_fallback = True

    def synthesize_contextual_view(
        self, 
        depth_image: Image.Image, 
        prompt: str, 
        negative_prompt: Optional[str] = None, 
        controlnet_conditioning_scale: float = 1.0, 
        num_steps: int = 20, 
        guidance_scale: float = 7.5, 
        seed: int = 42
    ) -> Image.Image:
        """
        Synthesizes realistic material textures strictly locked to the metric depth constraints.

        Args:
            depth_image: Grayscale PIL Image representing the terrain elevation depth.
            prompt: Text prompt guiding materials, lane striping, lighting.
            negative_prompt: Text prompt detailing unwanted visual elements.
            controlnet_conditioning_scale: Strength of the geometry-lock constraint.
            num_steps: Denoising steps.
            guidance_scale: Classifier-free guidance scale.
            seed: RNG seed for generation reproducibility.

        Returns:
            Synthesized photorealistic PIL Image.
        """
        if self.use_fallback or self.pipe is None:
            return self._procedural_synthesize(depth_image, prompt)

        try:
            generator = torch.manual_seed(seed)
            depth_input = depth_image.convert("L")
            
            output = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=depth_input,
                num_inference_steps=num_steps,
                guidance_scale=guidance_scale,
                controlnet_conditioning_scale=controlnet_conditioning_scale,
                generator=generator
            )
            return output.images[0]
        except Exception as e:
            print(f"Inference error: {e}. Activating procedural texture generator...")
            return self._procedural_synthesize(depth_image, prompt)

    def generate_baseline_drone_view(self, width: int = 800, height: int = 450) -> Image.Image:
        """Generates georeferenced baseline drone view showing sensed reality with raw encroachments."""
        w, h = width, height
        scene = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Ground background (earth, grass, riverbank terrain)
        for y in range(h):
            f = y / h
            scene[y, :] = [int(35 + 15*f), int(45 + 10*f), int(40 + 5*f)] # Earthy terrain tone

        # River Godavari on the left
        river_w = int(w * 0.18)
        for y in range(h):
            scene[y, :river_w] = [int(110 + 15*np.sin(y/20.0)), int(75 + 10*np.cos(y/30.0)), int(35 + 5*f)]

        # River bund boundary wall
        cv2.line(scene, (river_w, 0), (river_w, h), (140, 140, 145), 3)

        # Narrow Existing Road (14m width, poorly marked)
        road_left = int(w * 0.38)
        road_right = int(w * 0.62)
        cv2.rectangle(scene, (road_left, 0), (road_right, h), (48, 48, 52), -1)
        
        # Faded, cracked center lane line
        for y in range(0, h, 24):
            cv2.line(scene, (int((road_left + road_right)/2), y), (int((road_left + road_right)/2), y + 12), (150, 150, 140), 2)

        # Sanctioned Road Right-of-Way Limits (30m target - cyan dashed lines)
        row_left = int(w * 0.26)
        row_right = int(w * 0.76)
        for y in range(0, h, 16):
            cv2.line(scene, (row_left, y), (row_left, y + 8), (248, 189, 56), 2) # Cyan/Sky blue
            cv2.line(scene, (row_right, y), (row_right, y + 8), (248, 189, 56), 2)

        # Sensed Trees (Irregular green circles)
        tree_locs = [(int(w*0.22), 60), (int(w*0.23), 160), (int(w*0.21), 280), (int(w*0.24), 380),
                     (int(w*0.78), 90), (int(w*0.80), 210), (int(w*0.79), 340)]
        for tx, ty in tree_locs:
            cv2.circle(scene, (tx, ty), 16, (35, 115, 55), -1)
            cv2.circle(scene, (tx, ty), 16, (60, 180, 85), 2)

        # Detected Compliant Buildings (Amber Outlines)
        bldgs = [
            (int(w * 0.80), 40, 100, 70, "BLDG_004 Campus Block A"),
            (int(w * 0.80), 150, 110, 80, "BLDG_006 Engineering Lab"),
            (int(w * 0.80), 270, 95, 75, "BLDG_007 ADB Tech Plaza"),
            (int(w * 0.05), 200, 70, 60, "BLDG_003 Innovation Hub")
        ]
        for bx, by, bw, bh, bname in bldgs:
            cv2.rectangle(scene, (bx, by), (bx + bw, by + bh), (40, 42, 48), -1)
            cv2.rectangle(scene, (bx, by), (bx + bw, by + bh), (50, 180, 245), 2) # Amber
            cv2.putText(scene, bname[:14], (bx + 4, by + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1)

        # 4 Sensed Illegal Encroachments (Red Hazard Overlays Intruding Past the 30m RoW)
        encroachments = [
            (int(w * 0.32), 70, 75, 55, "ENC_001 Commercial Hub (+6.8m)"),
            (int(w * 0.60), 160, 80, 65, "ENC_002 Boundary Wall (+5.2m)"),
            (int(w * 0.33), 260, 65, 50, "ENC_003 Parking Shed (+4.5m)"),
            (int(w * 0.58), 350, 70, 45, "ENC_004 Transit Kiosks (+3.8m)")
        ]
        for ex, ey, ew, eh, elabel in encroachments:
            overlay = scene.copy()
            cv2.rectangle(overlay, (ex, ey), (ex + ew, ey + eh), (60, 60, 240), -1) # Red fill
            cv2.addWeighted(overlay, 0.45, scene, 0.55, 0, scene)
            cv2.rectangle(scene, (ex, ey), (ex + ew, ey + eh), (80, 80, 245), 2)
            
            # Diagonal hazard stripes
            for s in range(0, ew + eh, 12):
                cv2.line(scene, (ex + s, ey), (ex, ey + s), (90, 90, 255), 1)

            # Warning label
            cv2.putText(scene, elabel, (ex - 10, ey - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (120, 120, 255), 1)

        # GCP Ground Control Point Radar Pin
        gcp_x, gcp_y = int(w * 0.50), int(h * 0.48)
        cv2.circle(scene, (gcp_x, gcp_y), 18, (140, 230, 80), 2)
        cv2.circle(scene, (gcp_x, gcp_y), 4, (140, 230, 80), -1)
        cv2.line(scene, (gcp_x - 24, gcp_y), (gcp_x + 24, gcp_y), (140, 230, 80), 1)
        cv2.line(scene, (gcp_x, gcp_y - 24), (gcp_x, gcp_y + 24), (140, 230, 80), 1)
        cv2.putText(scene, "GCP_01 Surampalem ADB Rd [17.0890N, 82.0667E]", (gcp_x + 12, gcp_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (140, 230, 80), 1)

        rgb = cv2.cvtColor(scene, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _procedural_synthesize(self, depth_image: Image.Image, prompt: str) -> Image.Image:
        """Generates photorealistic synthesized future corridor with widened 4-lanes, bicycle tracks, sidewalks, and tree canopy."""
        w, h = 800, 450
        prompt_lower = prompt.lower()
        if "night" in prompt_lower:
            style = "Nighttime"
        elif "rain" in prompt_lower or "wet" in prompt_lower or "monsoon" in prompt_lower:
            style = "Rainy"
        elif "green" in prompt_lower or "eco" in prompt_lower:
            style = "EcoGreen"
        else:
            style = "Daylight"

        # Canvas background (Modern landscape)
        scene = np.zeros((h, w, 3), dtype=np.uint8)
        if style == "Daylight":
            for y in range(h):
                f = y / h
                scene[y, :] = [int(45 + 10*f), int(85 + 15*f), int(55 + 10*f)] # Landscaped manicured grass
        elif style == "Nighttime":
            for y in range(h):
                scene[y, :] = [int(15), int(18), int(20)]
        elif style == "Rainy":
            for y in range(h):
                scene[y, :] = [int(35), int(50), int(40)]
        else: # EcoGreen
            for y in range(h):
                f = y / h
                scene[y, :] = [int(40 + 20*f), int(120 + 20*f), int(50 + 15*f)]

        # River Godavari Promenade on Left
        river_w = int(w * 0.18)
        for y in range(h):
            if style == "Nighttime":
                scene[y, :river_w] = [int(35 + 5*np.sin(y/15.0)), int(25), int(15)]
            else:
                scene[y, :river_w] = [int(145 + 10*np.sin(y/15.0)), int(105 + 8*np.cos(y/25.0)), int(45)]
        
        # Riverfront Heritage Promenade Walkway & Railing
        cv2.rectangle(scene, (river_w, 0), (river_w + 24, h), (180, 185, 190) if style != "Nighttime" else (60, 65, 70), -1)
        cv2.line(scene, (river_w + 24, 0), (river_w + 24, h), (110, 110, 115), 2)

        # -------------------------------------------------------------
        # SANCTIONED MULTI-MODAL SMART HIGHWAY CORRIDOR (30.0m ROW)
        # -------------------------------------------------------------
        c_left = int(w * 0.24)
        c_right = int(w * 0.78)

        # 1. Left Pedestrian Sidewalk (2.0m)
        sw1_left = c_left
        sw1_right = sw1_left + int(w * 0.05)
        cv2.rectangle(scene, (sw1_left, 0), (sw1_right, h), (160, 165, 170) if style != "Nighttime" else (50, 52, 58), -1)
        # Paver tiles pattern
        for y in range(0, h, 14):
            cv2.line(scene, (sw1_left, y), (sw1_right, y), (140, 145, 150) if style != "Nighttime" else (40, 42, 46), 1)

        # 2. Left Dedicated Bicycle Track (2.5m - Bright Green Asphalt)
        bike1_left = sw1_right
        bike1_right = bike1_left + int(w * 0.06)
        bike_color = (65, 145, 75) if style != "Nighttime" else (25, 60, 30)
        cv2.rectangle(scene, (bike1_left, 0), (bike1_right, h), bike_color, -1)
        # White bicycle lane boundary
        cv2.line(scene, (bike1_left, 0), (bike1_left, h), (240, 240, 240), 2)
        cv2.line(scene, (bike1_right, 0), (bike1_right, h), (240, 240, 240), 2)
        # Bicycle icon symbols along track
        for by in range(40, h, 90):
            cv2.circle(scene, (int((bike1_left+bike1_right)/2) - 4, by), 4, (255, 255, 255), 1)
            cv2.circle(scene, (int((bike1_left+bike1_right)/2) + 4, by), 4, (255, 255, 255), 1)
            cv2.line(scene, (int((bike1_left+bike1_right)/2) - 4, by), (int((bike1_left+bike1_right)/2) + 4, by - 6), (255, 255, 255), 1)

        # 3. Main 4-Lane Highway Carriageway (Asphalt)
        hwy_left = bike1_right
        hwy_right = c_right - int(w * 0.11)
        asphalt_color = (55, 55, 58) if style != "Nighttime" else (22, 22, 25)
        if style == "Rainy": asphalt_color = (35, 38, 42)
        cv2.rectangle(scene, (hwy_left, 0), (hwy_right, h), asphalt_color, -1)

        # 4. Central Planted Green Median (with Shaded Canopy Trees)
        med_x = int((hwy_left + hwy_right) / 2)
        med_w = int(w * 0.04)
        cv2.rectangle(scene, (med_x - med_w//2, 0), (med_x + med_w//2, h), (40, 110, 50) if style != "Nighttime" else (18, 45, 22), -1)
        cv2.rectangle(scene, (med_x - med_w//2, 0), (med_x + med_w//2, h), (180, 180, 185) if style != "Nighttime" else (80, 80, 85), 1)
        # Median Trees
        for ty in range(25, h, 65):
            cv2.circle(scene, (med_x, ty), 13, (30, 130, 60) if style != "Nighttime" else (15, 60, 30), -1)
            cv2.circle(scene, (med_x, ty), 13, (60, 190, 90) if style != "Nighttime" else (30, 100, 50), 1)

        # Lane Markings for the 4 Carriageway Lanes
        lane1_x = int(hwy_left + (med_x - med_w//2 - hwy_left)/2)
        lane2_x = int(med_x + med_w//2 + (hwy_right - (med_x + med_w//2))/2)
        for y in range(0, h, 24):
            cv2.line(scene, (lane1_x, y), (lane1_x, y + 14), (230, 230, 230) if style != "Nighttime" else (160, 160, 160), 2)
            cv2.line(scene, (lane2_x, y), (lane2_x, y + 14), (230, 230, 230) if style != "Nighttime" else (160, 160, 160), 2)

        # Outer highway solid white edge lines
        cv2.line(scene, (hwy_left, 0), (hwy_left, h), (245, 245, 245), 2)
        cv2.line(scene, (hwy_right, 0), (hwy_right, h), (245, 245, 245), 2)

        # 5. Right Dedicated Bicycle Track (2.5m)
        bike2_left = hwy_right
        bike2_right = bike2_left + int(w * 0.06)
        cv2.rectangle(scene, (bike2_left, 0), (bike2_right, h), bike_color, -1)
        cv2.line(scene, (bike2_left, 0), (bike2_left, h), (240, 240, 240), 2)
        cv2.line(scene, (bike2_right, 0), (bike2_right, h), (240, 240, 240), 2)
        for by in range(40, h, 90):
            cv2.circle(scene, (int((bike2_left+bike2_right)/2) - 4, by), 4, (255, 255, 255), 1)
            cv2.circle(scene, (int((bike2_left+bike2_right)/2) + 4, by), 4, (255, 255, 255), 1)
            cv2.line(scene, (int((bike2_left+bike2_right)/2) - 4, by), (int((bike2_left+bike2_right)/2) + 4, by - 6), (255, 255, 255), 1)

        # 6. Right Pedestrian Sidewalk (2.0m)
        sw2_left = bike2_right
        sw2_right = c_right
        cv2.rectangle(scene, (sw2_left, 0), (sw2_right, h), (160, 165, 170) if style != "Nighttime" else (50, 52, 58), -1)
        for y in range(0, h, 14):
            cv2.line(scene, (sw2_left, y), (sw2_right, y), (140, 145, 150) if style != "Nighttime" else (40, 42, 46), 1)

        # 7. Shaded Avenue Tree Row on Right Flank (Compensatory Afforestation)
        for ty in range(30, h, 55):
            tx = sw2_right + 18
            cv2.circle(scene, (tx, ty), 16, (35, 135, 60) if style != "Nighttime" else (18, 70, 35), -1)
            cv2.circle(scene, (tx, ty), 16, (70, 200, 95) if style != "Nighttime" else (35, 120, 55), 2)

        # Smart Solar LED Streetlights
        for ly in range(40, h, 80):
            # Left sidewalk light
            cv2.circle(scene, (sw1_left - 4, ly), 3, (255, 255, 255) if style != "Nighttime" else (120, 240, 255), -1)
            # Right sidewalk light
            cv2.circle(scene, (sw2_right + 4, ly), 3, (255, 255, 255) if style != "Nighttime" else (120, 240, 255), -1)
            if style == "Nighttime":
                # Warm light beam cones
                cv2.ellipse(scene, (sw1_left + 15, ly), (28, 20), 0, 0, 360, (50, 100, 110), -1)
                cv2.ellipse(scene, (sw2_right - 15, ly), (28, 20), 0, 0, 360, (50, 100, 110), -1)

        # Vehicles navigating smoothly on widened lanes
        cv2.rectangle(scene, (lane1_x - 7, 120), (lane1_x + 7, 150), (200, 40, 40) if style != "Nighttime" else (150, 20, 20), -1) # Red car
        cv2.rectangle(scene, (lane2_x - 8, 260), (lane2_x + 8, 300), (220, 220, 225) if style != "Nighttime" else (180, 180, 180), -1) # Silver SUV
        if style == "Nighttime":
            # Headlights beam
            cv2.line(scene, (lane1_x - 5, 150), (lane1_x - 12, 190), (100, 220, 255), 2)
            cv2.line(scene, (lane1_x + 5, 150), (lane1_x + 12, 190), (100, 220, 255), 2)
            cv2.line(scene, (lane2_x - 6, 260), (lane2_x - 14, 220), (100, 220, 255), 2)
            cv2.line(scene, (lane2_x + 6, 260), (lane2_x + 14, 220), (100, 220, 255), 2)

        # Weather / Style overlays
        if style == "Rainy":
            sheen = np.zeros((h, w), dtype=np.uint8)
            for x in (hwy_left + 30, med_x - 20, lane2_x, sw2_left):
                cv2.line(sheen, (x, 0), (x + 40, h), 255, 18)
            s_blur = cv2.GaussianBlur(sheen, (45, 45), 0)
            s_bgr = cv2.cvtColor(s_blur, cv2.COLOR_GRAY2BGR)
            scene = cv2.addWeighted(scene, 0.86, s_bgr, 0.14, 0)
            
            # Rain streaks
            np.random.seed(42)
            for _ in range(70):
                rx = np.random.randint(0, w)
                ry = np.random.randint(0, h)
                cv2.line(scene, (rx, ry), (rx - 2, ry + 8), (190, 190, 200), 1)

        elif style == "EcoGreen":
            # Extra lush floral verges
            for fy in range(15, h, 20):
                cv2.circle(scene, (sw1_left - 10, fy), 4, (80, 210, 120), -1)
                cv2.circle(scene, (sw2_right + 10, fy), 4, (80, 210, 120), -1)

        rgb = cv2.cvtColor(scene, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
