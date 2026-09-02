import os
import unittest
from fastapi.testclient import TestClient

# Initialize dependencies and target modules
from backend.app import app
from backend.config import RAW_DIR
import generate_mock_data

class TestCityTwinPhase4(unittest.TestCase):
    """Integration test suite for FastAPI routers and static asset mounting."""

    @classmethod
    def setUpClass(cls):
        """Ensures raw data inputs are generated before running API client requests."""
        generate_mock_data.main()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Assert GET /api/health returns computational readiness metadata."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gpu_available", data)
        self.assertIn("device_name", data)
        self.assertIn("loaded_engines", data)
        self.assertIsInstance(data["loaded_engines"], list)

    def test_02_audit_run_endpoint(self):
        """Assert POST /api/audit/run segments maps, runs overlay math, and outputs valid GeoJSON."""
        response = self.client.post("/api/audit/run", json={})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("flags_count", data)
        self.assertIn("total_encroachment_m2", data)
        self.assertIn("compliance_grade", data)
        self.assertIn("geojson", data)
        
        # Verify GeoJSON payload structure
        geojson = data["geojson"]
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertIsInstance(geojson["features"], list)
        if len(geojson["features"]) > 0:
            feature = geojson["features"][0]
            self.assertEqual(feature["type"], "Feature")
            self.assertIn("geometry", feature)
            self.assertIn("properties", feature)

    def test_03_render_generate_endpoint(self):
        """Assert POST /api/render/generate loads depth buffers and outputs Base64 images."""
        response = self.client.post("/api/render/generate", json={
            "style": "Nighttime Illumination",
            "prompt": "city bridge at night"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("render_time_sec", data)
        self.assertIn("image_base64", data)
        self.assertIn("message", data)
        
        # Verify base64 prefix
        self.assertTrue(data["image_base64"].startswith("data:image/png;base64,"))

    def test_04_static_assets_loading(self):
        """Assert frontend landing page and static resources (CSS, JS) load successfully."""
        # 1. Main index
        index_res = self.client.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn("text/html", index_res.headers["content-type"])
        self.assertIn("CityTwin AI", index_res.text)

        # 2. Stylesheet
        css_res = self.client.get("/static/css/styles.css")
        self.assertEqual(css_res.status_code, 200)

        # 3. JavaScript assets
        js_files = ["split_slider.js", "map_controller.js", "app.js"]
        for js_file in js_files:
            js_res = self.client.get(f"/static/js/{js_file}")
            self.assertEqual(js_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
