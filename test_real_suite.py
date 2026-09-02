import os
import unittest
from fastapi.testclient import TestClient

from backend.app import app
import download_real_data

class TestCityTwinProductionSuite(unittest.TestCase):
    """Integration test suite for the production-ready CityTwin AI platform."""

    @classmethod
    def setUpClass(cls):
        """Generates real-world Rajamahendravaram datasets and sets up TestClient."""
        download_real_data.main()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Assert system health signals GPU accelerators and core engines."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gpu_available", data)
        self.assertIn("device_name", data)

    def test_02_audit_run_endpoint(self):
        """Assert POST /api/audit/run segments maps and runs boundary checks in Rajamahendravaram coords."""
        response = self.client.post("/api/audit/run")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("flags_count", data)
        self.assertIn("total_encroachment_m2", data)
        self.assertIn("compliance_grade", data)
        self.assertIn("geojson", data)

        # Check coordinates lie in Rajamahendravaram (81.77E to 81.79E, 16.98N to 16.99N)
        geojson = data["geojson"]
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertTrue(len(geojson["features"]) > 0, "Should identify at least 1 encroachment")
        
        feature = geojson["features"][0]
        coords = feature["geometry"]["coordinates"][0]
        for pt in coords:
            self.assertTrue(81.770 <= pt[0] <= 81.795, f"Longitude {pt[0]} should align with Rajamahendravaram bounds")
            self.assertTrue(16.975 <= pt[1] <= 16.995, f"Latitude {pt[1]} should align with Rajamahendravaram bounds")

    def test_03_tree_canopy_endpoint(self):
        """Assert POST /api/addons/trees detects vegetation and calculates clearing area."""
        response = self.client.post("/api/addons/trees")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("total_canopy_loss_area_m2", data)
        self.assertIn("tree_clearance_count", data)
        self.assertTrue(data["total_canopy_loss_area_m2"] > 0, "Should estimate non-zero canopy loss")

    def test_04_render_generate_endpoint(self):
        """Assert POST /api/render/generate normalizes real depth maps and outputs Base64 images."""
        response = self.client.post("/api/render/generate", json={
            "style": "Nighttime Illumination",
            "prompt": "city flyover lights"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["image_base64"].startswith("data:image/png;base64,"))

    def test_05_pdf_report_endpoint(self):
        """Assert GET /api/reports/download-pdf streams a valid binary ReportLab PDF file."""
        response = self.client.get("/api/reports/download-pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(len(response.content) > 1000, "Should return non-empty PDF binary payload")

if __name__ == "__main__":
    unittest.main()
