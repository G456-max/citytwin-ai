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

class CADConstrainedDiffusionPipeline:
    """Stable Diffusion ControlNet pipeline for geometry-locked photorealistic texture synthesis."""

    def __init__(
        self, 
        model_id: str = "runwayml/stable-diffusion-v1-5", 
        controlnet_id: str = "lllyasviel/control_v11f1p_sd15_depth",
        use_auth_token: bool = False
    ):
        """Initializes device, model components, and configures memory optimizations."""
        self.use_fallback = not HAS_DIFFUSERS
        self.device = "cuda" if (HAS_DIFFUSERS and torch.cuda.is_available()) else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.pipe = None

        if not self.use_fallback:
            try:
                print(f"Initializing neural pipelines on device: {self.device}...")
                controlnet = ControlNetModel.from_pretrained(
                    controlnet_id, 
                    torch_dtype=self.dtype,
                    local_files_only=True
                )
                self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
                    model_id, 
                    controlnet=controlnet, 
                    torch_dtype=self.dtype,
                    use_auth_token=use_auth_token,
                    local_files_only=True
                )
                
                # Setup scheduler
                self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
                
                # Apply memory efficiency features
                self.pipe.enable_attention_slicing()
                self.pipe.enable_vae_slicing()
                if self.device == "cuda":
                    # Try xformers or model CPU offload if needed
                    try:
                        self.pipe.enable_xformers_memory_efficient_attention()
                    except Exception:
                        pass
                
                self.pipe.to(self.device)
            except Exception as e:
                print(f"ControlNet model initialization failed: {str(e)}. Fallback engine active.")
                self.use_fallback = True

    def synthesize_contextual_view(
        self, 
        depth_image: Image.Image, 
        prompt: str, 
        negative_prompt: Optional[str] = None, 
        controlnet_conditioning_scale: float = 1.0, 
        num_steps: int = 25, 
        guidance_scale: float = 7.5, 
        seed: int = 42
    ) -> Image.Image:
        """
        Synthesizes texture over the depth image, strictly locking the geometric output.

        Args:
            depth_image: Normalized grayscale PIL Image of the CAD depth map.
            prompt: Text prompt guiding materials, light, and context.
            negative_prompt: Text prompt specifying unwanted visual traits.
            controlnet_conditioning_scale: Rigidness factor of depth map constraint.
            num_steps: Denoising inference steps.
            guidance_scale: Classifier-free guidance scale.
            seed: RNG seed for reproducible generation.

        Returns:
            Synthesized photorealistic PIL Image.
        """
        if self.use_fallback or self.pipe is None:
            # Execute high-fidelity math-locked procedural fallback
            return self._procedural_synthesize(depth_image, prompt)

        try:
            generator = torch.manual_seed(seed)
            # Ensure input image is a single-channel grayscale L image for depth conditioning
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
            print(f"Diffusion generation error: {str(e)}. Triggering procedural fallback...")
            return self._procedural_synthesize(depth_image, prompt)

    def _procedural_synthesize(self, depth_image: Image.Image, prompt: str) -> Image.Image:
        """Generates high-fidelity textured views using deterministic CV graphics engines."""
        # Convert PIL to grayscale numpy array
        depth_img = np.array(depth_image.convert("L"))
        h, w = depth_img.shape
        
        # Classify style based on prompt keywords
        prompt_lower = prompt.lower()
        if "night" in prompt_lower or "dark" in prompt_lower:
            style = "Nighttime"
        elif "rain" in prompt_lower or "wet" in prompt_lower or "monsoon" in prompt_lower:
            style = "Rainy"
        elif "green" in prompt_lower or "eco" in prompt_lower or "foliage" in prompt_lower:
            style = "EcoGreen"
        else:
            style = "Daylight"

        # Create atmospheric background
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        if style == "Daylight":
            for y in range(h):
                factor = y / h
                bg[y, :] = [int(165 + 40*factor), int(205 + 30*factor), int(225 + 20*factor)]
        elif style == "Nighttime":
            for y in range(h):
                factor = y / h
                bg[y, :] = [int(35 - 15*factor), int(20 - 10*factor), int(15 - 5*factor)]
        elif style == "Rainy":
            for y in range(h):
                factor = y / h
                bg[y, :] = [int(95 + 15*factor), int(100 + 10*factor), int(105 + 10*factor)]
        else: # EcoGreen
            for y in range(h):
                factor = y / h
                bg[y, :] = [int(175 + 25*factor), int(215 + 15*factor), int(195 + 30*factor)]

        # Add background shapes (e.g. urban buildings)
        cv2.rectangle(bg, (40, int(h*0.35)), (140, int(h*0.85)), (75, 75, 75) if style != "Nighttime" else (25, 25, 35), -1)
        cv2.rectangle(bg, (390, int(h*0.4)), (470, int(h*0.9)), (85, 90, 90) if style != "Nighttime" else (30, 30, 40), -1)
        
        if style == "Nighttime":
            # Add glowing building windows
            for wy in range(int(h*0.4), int(h*0.8), 35):
                cv2.rectangle(bg, (60, wy), (80, wy+12), (120, 240, 255), -1)
                cv2.rectangle(bg, (420, wy+15), (440, wy+27), (255, 220, 130), -1)

        # Segment road region (depth values represent flyover deck)
        _, road_mask = cv2.threshold(depth_img, 10, 255, cv2.THRESH_BINARY)

        # Create structured asphalt texture
        asphalt = np.zeros((h, w, 3), dtype=np.uint8)
        if style == "Daylight":
            asphalt[:] = [60, 60, 65]
        elif style == "Nighttime":
            asphalt[:] = [18, 18, 22]
        elif style == "Rainy":
            asphalt[:] = [40, 40, 44]
        else: # EcoGreen
            asphalt[:] = [65, 65, 70]

        # Add noise grain to simulate asphalt texture
        asphalt_noise = np.random.normal(0, 3.5, (h, w, 3)).astype(np.int16)
        asphalt = np.clip(asphalt.astype(np.int16) + asphalt_noise, 0, 255).astype(np.uint8)

        # Draw structural lanes and indicators locked to depth slices
        # Retrieve coordinate centers across depth slices
        centers = []
        lefts = []
        rights = []
        for d in range(15, 250, 6):
            ys, xs = np.where((depth_img >= d - 3) & (depth_img <= d + 3))
            if len(xs) > 0:
                min_x, max_x = np.min(xs), np.max(xs)
                y_c = int(np.mean(ys))
                x_c = int((min_x + max_x) / 2)
                centers.append((x_c, y_c))
                lefts.append((int(min_x + (max_x - min_x)*0.15), y_c))
                rights.append((int(min_x + (max_x - min_x)*0.85), y_c))

        if len(centers) > 1:
            center_pts = np.array(centers, dtype=np.int32).reshape((-1, 1, 2))
            left_pts = np.array(lefts, dtype=np.int32).reshape((-1, 1, 2))
            right_pts = np.array(rights, dtype=np.int32).reshape((-1, 1, 2))

            # Outer boundary curbs
            cv2.polylines(asphalt, [left_pts], False, (235, 235, 235), 3)
            cv2.polylines(asphalt, [right_pts], False, (235, 235, 235), 3)

            # Center double yellow separators
            yellow = (0, 180, 255) if style != "Nighttime" else (0, 200, 255)
            left_center = center_pts.copy()
            left_center[:, 0, 0] -= 4
            right_center = center_pts.copy()
            right_center[:, 0, 0] += 4
            cv2.polylines(asphalt, [left_center], False, yellow, 2)
            cv2.polylines(asphalt, [right_center], False, yellow, 2)

            # Dashed lane divider lines
            for i in range(len(centers) - 1):
                if i % 4 in (0, 1):
                    # Draw dashes in between center and borders
                    pt_l1 = (int((lefts[i][0] + centers[i][0]) / 2), centers[i][1])
                    pt_l2 = (int((lefts[i+1][0] + centers[i+1][0]) / 2), centers[i+1][1])
                    pt_r1 = (int((rights[i][0] + centers[i][0]) / 2), centers[i][1])
                    pt_r2 = (int((rights[i+1][0] + centers[i+1][0]) / 2), centers[i+1][1])
                    cv2.line(asphalt, pt_l1, pt_l2, (220, 220, 220), 2)
                    cv2.line(asphalt, pt_r1, pt_r2, (220, 220, 220), 2)

        # Crop road layer using road mask
        road_img = cv2.bitwise_and(asphalt, asphalt, mask=road_mask)
        bg_masked = cv2.bitwise_and(bg, bg, mask=cv2.bitwise_not(road_mask))
        final_scene = cv2.add(bg_masked, road_img)

        # --- Draw Future Infrastructure: Elevated Metro Link & Columns ---
        col_y_top = int(h * 0.32)
        col_y_bottom = int(h * 0.70)
        col_w = 14
        p1_x = int(w * 0.30)
        p2_x = int(w * 0.70)
        
        # Draw columns (supporting concrete piers)
        cv2.rectangle(final_scene, (p1_x - col_w, col_y_top), (p1_x + col_w, col_y_bottom), (95, 95, 100), -1)
        cv2.rectangle(final_scene, (p1_x - col_w - 4, col_y_top), (p1_x + col_w + 4, col_y_top + 8), (120, 120, 125), -1)
        cv2.rectangle(final_scene, (p2_x - col_w, col_y_top), (p2_x + col_w, col_y_bottom), (95, 95, 100), -1)
        cv2.rectangle(final_scene, (p2_x - col_w - 4, col_y_top), (p2_x + col_w + 4, col_y_top + 8), (120, 120, 125), -1)

        # Draw elevated deck slab & bridge girder
        cv2.rectangle(final_scene, (0, int(h * 0.22)), (w, int(h * 0.31)), (115, 115, 120), -1)
        cv2.rectangle(final_scene, (0, int(h * 0.20)), (w, int(h * 0.22)), (140, 140, 145), -1)
        
        # Draw steel rails
        cv2.line(final_scene, (0, int(h * 0.21)), (w, int(h * 0.21)), (70, 70, 70), 2)
        cv2.line(final_scene, (0, int(h * 0.215)), (w, int(h * 0.215)), (70, 70, 70), 2)

        # Draw futuristic metro train body & front windshield glass
        cv2.rectangle(final_scene, (int(w * 0.30), int(h * 0.14)), (int(w * 0.75), int(h * 0.20)), (190, 195, 205), -1)
        cv2.rectangle(final_scene, (int(w * 0.72), int(h * 0.15)), (int(w * 0.75), int(h * 0.19)), (40, 40, 40), -1)
        
        # Draw window glass panes on the train
        for wx in range(int(w * 0.33), int(w * 0.70), 25):
            cv2.rectangle(final_scene, (wx, int(h * 0.165)), (wx + 14, int(h * 0.185)), (100, 160, 220), -1)

        # Style enhancements
        if style == "Nighttime":
            # Apply headlight beams and glowing neon effects
            glow = final_scene.copy()
            if len(lefts) > 5:
                # Red taillights on left lane
                for i in range(1, len(lefts) - 1):
                    p1 = (lefts[i][0] + 12, lefts[i][1])
                    p2 = (lefts[i+1][0] + 12, lefts[i+1][1])
                    cv2.line(glow, p1, p2, (0, 0, 255), 6)
                # Cyan/white headlights on right lane
                for i in range(1, len(rights) - 1):
                    p1 = (rights[i][0] - 12, rights[i][1])
                    p2 = (rights[i+1][0] - 12, rights[i+1][1])
                    cv2.line(glow, p1, p2, (255, 235, 210), 6)
            final_scene = cv2.addWeighted(final_scene, 0.75, glow, 0.25, 0)

        elif style == "EcoGreen":
            # Draw foliage along outer borders
            contours, _ = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            foliage = np.zeros((h, w, 3), dtype=np.uint8)
            foliage[:] = [42, 135, 58]
            foliage_noise = np.random.normal(0, 10, (h, w, 3)).astype(np.int16)
            foliage = np.clip(foliage.astype(np.int16) + foliage_noise, 0, 255).astype(np.uint8)
            
            foliage_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(foliage_mask, contours, -1, 255, 10)
            foliage_mask = cv2.bitwise_and(foliage_mask, cv2.bitwise_not(road_mask))
            
            # Blend
            foliage_pixels = cv2.bitwise_and(foliage, foliage, mask=foliage_mask)
            bg_clean = cv2.bitwise_and(final_scene, final_scene, mask=cv2.bitwise_not(foliage_mask))
            final_scene = cv2.add(bg_clean, foliage_pixels)

            # Draw green climbing ivy on concrete pillars
            cv2.rectangle(final_scene, (p1_x - col_w - 2, col_y_top + 10), (p1_x + col_w + 2, col_y_bottom - 20), (35, 110, 50), -1)
            cv2.rectangle(final_scene, (p2_x - col_w - 2, col_y_top + 20), (p2_x + col_w + 2, col_y_bottom - 10), (35, 110, 50), -1)

        elif style == "Rainy":
            # Wet asphalt sheen and vertical rain streaks
            sheen = np.zeros((h, w), dtype=np.uint8)
            for x in (120, 200, 280, 360):
                cv2.line(sheen, (x, 0), (x + 80, h), 255, 25)
            sheen_blur = cv2.GaussianBlur(sheen, (45, 45), 0)
            sheen_bgr = cv2.cvtColor(sheen_blur, cv2.COLOR_GRAY2BGR)
            final_scene = cv2.addWeighted(final_scene, 0.82, sheen_bgr, 0.18, 0)
            
            # Draw rain streaks
            np.random.seed(42)
            rain = np.zeros((h, w, 3), dtype=np.uint8)
            for _ in range(100):
                rx = np.random.randint(0, w)
                ry = np.random.randint(0, h)
                cv2.line(rain, (rx, ry), (rx - 4, ry + 12), (180, 180, 185), 1)
            final_scene = cv2.addWeighted(final_scene, 0.92, rain, 0.08, 0)

        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_scene = cv2.cvtColor(final_scene, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_scene)
