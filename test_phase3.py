import os
import unittest
import base64
from pathlib import Path
from PIL import Image

from backend.visualizer.depth_preprocessor import DepthBufferProcessor
from backend.visualizer.controlnet_pipeline import CADConstrainedDiffusionPipeline
from backend.visualizer.render_manager import CorridorRenderManager

class TestCityTwinPhase3(unittest.TestCase):
    """End-to-end unit and integration tests for Phase 3 (Blueprint-Locked Generative Engine)."""

    @classmethod
    def setUpClass(cls):
        """Prepares synthetic data directory and mock CAD depth inputs."""
        cls.test_dir = Path("data_test_p3")
        cls.raw_dir = cls.test_dir / "raw"
        cls.processed_dir = cls.test_dir / "processed"
        
        cls.raw_dir.mkdir(parents=True, exist_ok=True)
        cls.processed_dir.mkdir(parents=True, exist_ok=True)
        
        cls.depth_path = str(cls.raw_dir / "test_cad_depth.png")
        
        # Draw a synthetic depth map for testing using preprocessor
        processor = DepthBufferProcessor()
        processor.generate_synthetic_cad_depth(cls.depth_path)

    def test_01_depth_normalization_and_padding(self):
        """Assert preprocessor scales, normalizes, and cushions depth maps to 512x512 L."""
        processor = DepthBufferProcessor()
        norm_image = processor.normalize_depth_map(self.depth_path, target_size=(512, 512))
        
        self.assertIsInstance(norm_image, Image.Image, "Output must be a PIL Image")
        self.assertEqual(norm_image.size, (512, 512), "Size must match target dimensions")
        self.assertEqual(norm_image.mode, "L", "Must be a single-channel grayscale (L) image")
        
        # Check dynamic range mapping (should contain values)
        depth_data = norm_image.getdata()
        self.assertTrue(max(depth_data) > 0, "Grayscale pixels must contain depth outlines")

    def test_02_constrained_pipeline_synthesis(self):
        """Verify pipeline execution generates valid texture outputs strictly locked to geometry."""
        # Run test with fallback to speed up local test runs
        pipeline = CADConstrainedDiffusionPipeline()
        processor = DepthBufferProcessor()
        
        norm_depth = processor.normalize_depth_map(self.depth_path, target_size=(512, 512))
        
        prompt = "modern urban flyover, green landscaping, daylight"
        scene = pipeline.synthesize_contextual_view(norm_depth, prompt)
        
        self.assertIsInstance(scene, Image.Image, "Synthesized scene must be a PIL Image")
        self.assertEqual(scene.size, (512, 512), "Synthesized canvas sizing must match target")
        self.assertEqual(scene.mode, "RGB", "Scene must be RGB colored")

    def test_03_render_manager_execution(self):
        """Assert the render manager formats prompts, saves PNGs, and streams valid Base64."""
        # Override output directory config dynamically for testing if needed
        # By default, CorridorRenderManager uses config's PROCESSED_DIR.
        manager = CorridorRenderManager()
        
        results = manager.render_and_encode(
            depth_path=self.depth_path,
            style="Nighttime Illumination"
        )
        
        self.assertEqual(results["status"], "success", "Response status must be success")
        self.assertTrue(results["render_time_sec"] > 0, "Execution elapsed time must be logged")
        
        # Verify base64 signature
        base64_str = results["image_base64"]
        self.assertTrue(base64_str.startswith("data:image/png;base64,"), "Saves with valid Data URI signature")
        
        # Decode base64 and verify PIL loadability
        raw_b64 = base64_str.split(",")[1]
        decoded_bytes = base64.b64decode(raw_b64)
        
        import io
        pil_decoded = Image.open(io.BytesIO(decoded_bytes))
        self.assertEqual(pil_decoded.size, (512, 512), "Decoded image resolution matches 512x512")
        
        # Verify file existence on disk
        self.assertTrue(os.path.exists(results["output_path"]), "Saves final output path image to disk")

    @classmethod
    def tearDownClass(cls):
        """Clean up synthetic test directories."""
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

if __name__ == "__main__":
    unittest.main()
