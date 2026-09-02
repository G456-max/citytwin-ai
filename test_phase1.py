import os
import unittest
import numpy as np
import shutil
from pathlib import Path

# Import Phase 1 Core Modules
from backend.ingestion.frame_extractor import DroneVideoExtractor
from backend.ingestion.spatial_anchor import GCPAnchorEngine
from backend.ingestion.raster_handler import OrthomosaicHandler
import generate_mock_data

class TestCityTwinPhase1(unittest.TestCase):
    """Integration test suite for Phase 1 (Data Ingestion & Spatial Anchoring)."""

    @classmethod
    def setUpClass(cls):
        """Generates mock data video assets if they do not exist already."""
        cls.test_dir = Path("data_test_p1")
        cls.frames_out = cls.test_dir / "extracted_frames"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Make sure mock data generator has run to create raw/corridor_flight.mp4
        generate_mock_data.main()
        
        cls.video_path = "data/raw/corridor_flight.mp4"
        cls.ortho_path = "data/real_corridor/corridor_orthomosaic.tif"

    def test_01_video_frame_extraction(self):
        """Assert DroneVideoExtractor filters blurry frames and extracts keyframes."""
        self.assertTrue(os.path.exists(self.video_path), "Mock drone video flight feed must exist")
        
        # Extract frames with a low blur threshold for testing
        extracted_files = DroneVideoExtractor.extract_keyframes(
            video_path=self.video_path,
            output_dir=str(self.frames_out),
            frame_interval=10,
            blur_threshold=10.0
        )
        
        self.assertIsInstance(extracted_files, list)
        self.assertTrue(len(extracted_files) > 0, "Should extract at least one sharp frame from video")
        
        # Verify physical file existence
        for f in extracted_files:
            self.assertTrue(os.path.exists(f), f"Extracted file {f} must exist on disk")

    def test_02_gcp_affine_anchoring(self):
        """Assert GCPAnchorEngine calculates correct 3-point affine snaps with no datum drift."""
        # 3 local CAD/camera points
        source_gcps = [(100.0, 100.0), (200.0, 100.0), (100.0, 200.0)]
        # 3 target real-world GPS points (representing scale shift, translation, and rotation)
        target_gcps = [(81.7825, 16.9810), (81.7835, 16.9810), (81.7825, 16.9820)]
        
        matrix = GCPAnchorEngine.calculate_affine_transform(source_gcps, target_gcps)
        
        self.assertEqual(matrix.shape, (3, 3), "Transformation matrix must be 3x3")
        self.assertEqual(matrix[2, 0], 0.0)
        self.assertEqual(matrix[2, 1], 0.0)
        self.assertEqual(matrix[2, 2], 1.0)
        
        # Transform a point and assert that it maps to the exact matching coordinate
        transformed = GCPAnchorEngine.transform_points([(150.0, 150.0)], matrix)
        self.assertEqual(len(transformed), 1)
        
        # Expect midpoint coordinate (81.7830, 16.9815)
        self.assertAlmostEqual(transformed[0][0], 81.7830, places=5)
        self.assertAlmostEqual(transformed[0][1], 16.9815, places=5)

    def test_03_raster_metadata_handler(self):
        """Assert OrthomosaicHandler correctly reads spatial reference layers and bounds."""
        self.assertTrue(os.path.exists(self.ortho_path), "Real orthomosaic GeoTIFF must exist")
        
        info = OrthomosaicHandler.get_raster_info(self.ortho_path)
        
        self.assertIn("crs", info)
        self.assertIn("bounds", info)
        self.assertIn("width", info)
        self.assertIn("height", info)
        self.assertIn("gsd", info)
        
        self.assertEqual(info["crs"], "EPSG:4326")
        self.assertTrue(info["width"] > 0)
        self.assertTrue(info["height"] > 0)
        self.assertTrue(info["gsd"] > 0)

    @classmethod
    def tearDownClass(cls):
        """Clean up test folders."""
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

if __name__ == "__main__":
    unittest.main()
