import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path

class DepthBufferProcessor:
    """Handles depth map scaling, padding, normalization, and synthetic CAD depth maps generation."""

    def normalize_depth_map(
        self, 
        input_image_path: str, 
        target_size: tuple[int, int] = (512, 512)
    ) -> Image.Image:
        """
        Loads an 8-bit or 16-bit depth map image, normalizes dynamic range to [0, 255],
        and resizes it using letterbox padding to standard square diffusion dimensions.

        Args:
            input_image_path: Path to the raw depth image.
            target_size: Tuple representing desired dimensions (width, height).

        Returns:
            Normalized and padded PIL Image (Grayscale L mode).
        """
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"Input depth map not found: {input_image_path}")

        # Read unchanged (supports 16-bit grayscale or multi-channel)
        img = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
        
        # Convert multi-channel (RGB/RGBA) to grayscale
        if len(img.shape) >= 3:
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Normalize dynamic range to [0, 255] grayscale
        normalized = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        # Letterbox scaling (resizes preserving aspect ratio with black padding)
        h, w = normalized.shape
        tw, th = target_size
        
        # Determine scale factor
        scale = min(tw / w, th / h)
        nw, nh = int(w * scale), int(h * scale)
        
        # Resize
        resized = cv2.resize(normalized, (nw, nh), interpolation=cv2.INTER_AREA)
        
        # Create black canvas and center the resized depth map
        padded = np.zeros((th, tw), dtype=np.uint8)
        x_offset = (tw - nw) // 2
        y_offset = (th - nh) // 2
        padded[y_offset:y_offset+nh, x_offset:x_offset+nw] = resized
        
        # Convert to PIL Image
        pil_img = Image.fromarray(padded).convert("L")
        return pil_img

    def generate_synthetic_cad_depth(self, output_path: str = "data/cad_depth.png") -> str:
        """
        Draws a high-quality synthetic 16-bit (represented in CV_8U scale) depth map
        of a curved, elevated 4-lane highway flyover deck for verification.

        Args:
            output_path: Path where the generated depth map will be saved.

        Returns:
            Absolute path to the generated depth map file.
        """
        h, w = 512, 512
        depth_canvas = np.zeros((h, w), dtype=np.uint8)

        # Draw a curved perspective flyover deck
        # Left and right lanes of an elevated structure
        points = np.array([
            [120, 512],
            [180, 380],
            [250, 260],
            [290, 140],
            [300, 0]
        ], dtype=np.int32)

        # Draw segmented polygon bands with gradient depth values
        for i in range(len(points) - 1):
            pt1, pt2 = points[i], points[i+1]
            
            # Perspective narrowing width
            w1 = int(80 - (512 - pt1[1]) * 0.08)
            w2 = int(80 - (512 - pt2[1]) * 0.08)
            
            dx, dy = pt2[0] - pt1[0], pt2[1] - pt1[1]
            length = np.hypot(dx, dy)
            nx, ny = -dy / length, dx / length
            
            l1 = pt1 + nx * w1
            r1 = pt1 - nx * w1
            l2 = pt2 + nx * w2
            r2 = pt2 - nx * w2
            
            poly = np.array([l1, r1, r2, l2], dtype=np.int32)
            
            # Grayscale depth value represents elevation profile
            # Near boundary: depth = 40. Far boundary (elevated peak): depth = 190.
            mid_y = (pt1[1] + pt2[1]) / 2
            depth_val = int(50 + (512 - mid_y) * 0.3)
            
            cv2.fillPoly(depth_canvas, [poly], depth_val)

        # Apply a soft Gaussian blur to smooth depth mapping transitions
        blurred_depth = cv2.GaussianBlur(depth_canvas, (11, 11), 0)

        # Ensure directory structure exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(output_path_obj), blurred_depth)
        return str(output_path_obj.resolve())
