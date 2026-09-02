import os
import unittest
import json
import geopandas as gpd
from shapely.geometry import LineString, Polygon
import rasterio
from rasterio.transform import from_bounds
import numpy as np
import cv2
from pathlib import Path

from backend.audit.segmentation_engine import GeospatialSegmentationEngine
from backend.audit.discrepancy_engine import CorridorDiscrepancyAuditor
from backend.audit.report_generator import AuditReportGenerator

class TestCityTwinPhase2(unittest.TestCase):
    """End-to-end integration and unit tests for CityTwin AI Phase 2."""

    @classmethod
    def setUpClass(cls):
        """Set up directories and generate synthetic georeferenced data fixtures."""
        cls.test_dir = Path("data_test")
        cls.raw_dir = cls.test_dir / "raw"
        cls.processed_dir = cls.test_dir / "processed"
        
        cls.raw_dir.mkdir(parents=True, exist_ok=True)
        cls.processed_dir.mkdir(parents=True, exist_ok=True)

        cls.row_path = str(cls.raw_dir / "test_road_boundary.geojson")
        cls.structs_path = str(cls.raw_dir / "test_detected_structures.geojson")
        cls.tif_path = str(cls.raw_dir / "test_orthomosaic.tif")
        cls.flags_path = str(cls.processed_dir / "test_discrepancy_flags.geojson")

        # 1. Create a 12m corridor road boundary centered at 80.3250 longitude
        # Centerline path in WGS84
        centerline = LineString([(80.3250, 26.4710), (80.3250, 26.4730)])
        gdf_center = gpd.GeoDataFrame(geometry=[centerline], crs="EPSG:4326")
        
        # Project to local metric UTM Zone 44N (EPSG:32644)
        gdf_center_m = gdf_center.to_crs("EPSG:32644")
        
        # Buffer by 6m (creates a 12m Right-of-Way)
        gdf_row_m = gdf_center_m.copy()
        gdf_row_m.geometry = gdf_center_m.geometry.buffer(6.0)
        
        # Convert back to WGS84 and save
        gdf_row_wgs84 = gdf_row_m.to_crs("EPSG:4326")
        gdf_row_wgs84.to_file(cls.row_path, driver="GeoJSON")

        # 2. Define 3 structures in metric UTM Coordinates (so overlay math is exact)
        # Centerline is at X = 432719.0. Boundary is at X_min = 432713.0, X_max = 432725.0.
        # Structure 1: Compliant (X_min = 432730, X_max = 432740) -> 0m encroachment
        poly1 = Polygon([(432730, 2928100), (432740, 2928100), (432740, 2928110), (432730, 2928110)])
        
        # Structure 2: Minor Encroachment (X_min = 432723.0, X_max = 432733.0) -> Overlaps [432723.0, 432725.0]
        # Overlap width = 2.0m, height = 10m -> Encroach area = 20m2, depth = 2.0m. Severity: Medium
        poly2 = Polygon([(432723.0, 2928120), (432733.0, 2928120), (432733.0, 2928130), (432723.0, 2928130)])
        
        # Structure 3: Major Encroachment (X_min = 432709.0, X_max = 432721.0) -> Overlaps [432713.0, 432721.0]
        # Overlap width = 8.0m, height = 10m -> Encroach area = 80m2, depth = 8.0m. Severity: Critical
        poly3 = Polygon([(432709.0, 2928150), (432721.0, 2928150), (432721.0, 2928160), (432709.0, 2928160)])

        structs_gdf_m = gpd.GeoDataFrame(
            [
                {"id": "STRUCT_001", "name": "Compliant Commercial", "geometry": poly1},
                {"id": "STRUCT_002", "name": "Encroaching Shop", "geometry": poly2},
                {"id": "STRUCT_003", "name": "Encroaching Residence", "geometry": poly3}
            ],
            crs="EPSG:32644"
        )
        
        # Reproject structures to WGS84 and save
        cls.structs_gdf_wgs84 = structs_gdf_m.to_crs("EPSG:4326")
        cls.structs_gdf_wgs84.to_file(cls.structs_path, driver="GeoJSON")

        # 3. Create a synthetic georeferenced GeoTIFF orthomosaic image
        # Sized to cover the coordinates of our study area
        width, height = 400, 400
        minx, miny = 80.3245, 26.4705
        maxx, maxy = 80.3255, 26.4735
        
        image = np.zeros((height, width, 3), dtype=np.uint8)
        # Fill ground grass
        image[:, :] = [35, 120, 45]
        
        # Draw a road centerline visually matching our coordinates
        cv2.line(image, (200, 0), (200, 400), (70, 70, 70), 30)
        
        # Draw our buildings as bright white rectangles to be detected by thresholding
        # Compliant structure (drawn to the right of centerline)
        cv2.rectangle(image, (250, 100), (280, 130), (255, 255, 255), -1)
        # Minor encroaching structure
        cv2.rectangle(image, (180, 220), (210, 250), (255, 255, 255), -1)
        # Major encroaching structure
        cv2.rectangle(image, (100, 320), (140, 360), (255, 255, 255), -1)

        transform = from_bounds(minx, miny, maxx, maxy, width, height)
        with rasterio.open(
            cls.tif_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=3,
            dtype='uint8',
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(image[:, :, 0], 1)
            dst.write(image[:, :, 1], 2)
            dst.write(image[:, :, 2], 3)

    def test_01_segmentation_engine(self):
        """Verify the segmentation engine loads and polygonizes the mock TIFF."""
        engine = GeospatialSegmentationEngine()
        # Extract footprints
        output_path = str(self.processed_dir / "test_detected_footprints.geojson")
        gdf = engine.extract_footprints_from_raster(self.tif_path, output_path)
        
        self.assertFalse(gdf.empty, "Segmented GeoDataFrame should not be empty")
        self.assertEqual(gdf.crs, "EPSG:4326", "CRS should be EPSG:4326 (WGS84)")
        self.assertTrue(os.path.exists(output_path), "Segmented GeoJSON file must exist on disk")

    def test_02_discrepancy_auditor_math(self):
        """Assert compliance calculations are correct for areas, depth, and severities."""
        auditor = CorridorDiscrepancyAuditor(self.row_path)
        
        # Run audit on the exact coordinates we designed
        results = auditor.audit_structures(
            self.structs_gdf_wgs84, 
            target_utm_crs="EPSG:32644", 
            output_flags_path=self.flags_path
        )
        
        # Verify output structure
        self.assertEqual(results["total_violations"], 2, "Should identify exactly 2 boundary violations")
        
        violations = results["violations"]
        
        # Sort by encroachment ID/area to make check deterministic
        violations.sort(key=lambda x: x["area_m2"])
        
        v_minor = violations[0]
        v_major = violations[1]
        
        # Validate minor encroachment metrics (Designed for Area ≈ 18m2, Depth ≈ 1.8m)
        self.assertEqual(v_minor["structure_id"], "STRUCT_002")
        self.assertAlmostEqual(v_minor["area_m2"], 18.2, delta=1.5)
        self.assertAlmostEqual(v_minor["max_intrusion_depth_m"], 1.8, delta=0.3)
        self.assertEqual(v_minor["severity"], "Medium")
        
        # Validate major encroachment metrics (Designed for Area=80m2, Depth ≈ 4.0m)
        self.assertEqual(v_major["structure_id"], "STRUCT_003")
        self.assertAlmostEqual(v_major["area_m2"], 80.0, delta=1.0)
        self.assertAlmostEqual(v_major["max_intrusion_depth_m"], 4.0, delta=0.5)
        self.assertEqual(v_major["severity"], "Critical")
        
        # Verify output GeoJSON was written and validates
        self.assertTrue(os.path.exists(self.flags_path), "Flags GeoJSON file must exist on disk")
        gdf_flags = gpd.read_file(self.flags_path)
        self.assertEqual(len(gdf_flags), 2, "Flags GeoJSON should contain exactly 2 violating polygons")

    def test_03_report_generator(self):
        """Assert the report generator formats summary indices and risk breakdown correctly."""
        auditor = CorridorDiscrepancyAuditor(self.row_path)
        audit_results = auditor.audit_structures(self.structs_gdf_wgs84, target_utm_crs="EPSG:32644", output_flags_path=self.flags_path)
        
        # Generate summary
        report = AuditReportGenerator.generate_json_summary(audit_results, project_name="Corridor test")
        
        # Verify compliance status and high risk
        summary = report["compliance_summary"]
        self.assertEqual(summary["status"], "NON-COMPLIANT - ACTION REQUIRED")
        self.assertEqual(summary["total_violations_count"], 2)
        self.assertEqual(summary["high_risk_violations_count"], 2) # Critical + Medium
        
        breakdown = report["violations_breakdown"]
        self.assertEqual(breakdown["critical_risk"], 1)
        self.assertEqual(breakdown["medium_risk"], 1)
        self.assertEqual(breakdown["low_risk"], 0)

    @classmethod
    def tearDownClass(cls):
        """Cleanup synthetic test directories."""
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

if __name__ == "__main__":
    unittest.main()
