import os
import unittest
from fastapi.testclient import TestClient

from backend.app import app
import download_real_data

class TestCityTwinProductionSuite(unittest.TestCase):
    """Integration test suite for the complete production-ready CityTwin AI platform."""

    @classmethod
    def setUpClass(cls):
        """Generates baseline georeferenced datasets and sets up TestClient."""
        download_real_data.main()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Assert system health signals computational accelerators and core engines."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gpu_available", data)
        self.assertIn("device_name", data)
        self.assertIn("loaded_engines", data)

    def test_02_audit_run_endpoint(self):
        """Assert POST /api/audit/run segments maps and runs boundary checks."""
        response = self.client.post("/api/audit/run")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("flags_count", data)
        self.assertIn("total_encroachment_m2", data)
        self.assertIn("compliance_grade", data)
        self.assertIn("geojson", data)
        self.assertEqual(data["geojson"]["type"], "FeatureCollection")

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
        self.assertIn("sensing_telemetry", data)

    def test_05_dynamic_location_audit(self):
        """Assert POST /api/audit/dynamic audits any GPS coordinate dynamically."""
        response = self.client.post("/api/audit/dynamic", json={
            "lat": 17.0890,
            "lon": 82.0667,
            "location_name": "Surampalem ADB Road Smart Corridor",
            "road_width_m": 30.0
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["location_name"], "Surampalem ADB Road Smart Corridor")
        self.assertIn("flags_count", data)
        self.assertIn("total_encroachment_m2", data)
        self.assertIn("geojson", data)

    def test_06_simulate_custom_encroachment(self):
        """Assert POST /api/audit/simulate_encroachment allows clicking anywhere to place illegal structures."""
        response = self.client.post("/api/audit/simulate_encroachment", json={
            "lat": 17.0895,
            "lon": 82.0669,
            "structure_name": "Illegal Commercial Shed",
            "structure_type": "Commercial",
            "width_m": 25.0,
            "depth_m": 16.0
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ENC_SIM", data["encroachment_id"])
        self.assertTrue(data["encroached_area_m2"] > 0)
        self.assertIn("feature", data)

    def test_07_dynamic_pdf_report(self):
        """Assert GET and POST PDF endpoints generate location-named certificates."""
        # Test GET
        get_res = self.client.get("/api/reports/download-pdf?location_name=Surampalem_ADB_Road")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.headers["content-type"], "application/pdf")
        self.assertTrue(len(get_res.content) > 1000)

        # Test POST
        post_res = self.client.post("/api/reports/generate-dynamic-pdf", json={
            "location_name": "Surampalem ADB Road Smart Corridor",
            "gps_coords": "17.08900° N, 82.06670° E",
            "utm_zone": "EPSG:32644 (UTM Zone 44N)",
            "compliance_grade": "F",
            "flags_count": 4,
            "total_encroachment_m2": 1261.22
        })
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.headers["content-type"], "application/pdf")
        self.assertTrue(len(post_res.content) > 1000)

    def test_08_static_cockpit_assets(self):
        """Assert frontend landing page, CSS, and JS bundle load cleanly."""
        index_res = self.client.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn("CityTwin AI", index_res.text)

        css_res = self.client.get("/styles.css")
        self.assertEqual(css_res.status_code, 200)

        js_res = self.client.get("/app.js")
        self.assertEqual(js_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
