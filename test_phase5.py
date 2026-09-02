import os
import unittest
from fastapi.testclient import TestClient

from backend.app import app
import download_real_data

class TestCityTwinPhase5(unittest.TestCase):
    """Integration test suite for Phase 5 (Real-World Geospatial Dataset routing)."""

    @classmethod
    def setUpClass(cls):
        """Ensures real-world Kanpur datasets are fetched/generated before testing endpoints."""
        download_real_data.main()
        cls.client = TestClient(app)

    def test_01_real_audit_endpoint(self):
        """Assert POST /api/audit/real segments real GeoTIFF and runs overlay checks on OSM boundaries."""
        response = self.client.post("/api/audit/real")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("flags_count", data)
        self.assertIn("total_encroachment_m2", data)
        self.assertIn("compliance_grade", data)
        self.assertIn("geojson", data)
        
        # Verify GeoJSON payload properties and coordinates match WGS84 Kanpur zone (80°E, 26°N)
        geojson = data["geojson"]
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertTrue(len(geojson["features"]) > 0, "Should identify at least 1 encroachment violation in the Kanpur GT Road corridor")
        
        feature = geojson["features"][0]
        self.assertEqual(feature["type"], "Feature")
        self.assertIn("geometry", feature)
        self.assertIn("properties", feature)
        
        # Check coordinates range
        coords = feature["geometry"]["coordinates"][0]
        for pt in coords:
            # Point is (lon, lat)
            self.assertTrue(80.320 <= pt[0] <= 80.330, f"Longitude {pt[0]} should align with Kanpur GT Road 80.325E range")
            self.assertTrue(26.465 <= pt[1] <= 26.475, f"Latitude {pt[1]} should align with Kanpur GT Road 26.472N range")

    def test_02_real_render_endpoint(self):
        """Assert POST /api/render/real normalizes real terrain depth buffers and outputs base64 images."""
        response = self.client.post("/api/render/real", json={
            "style": "Eco-Green Corridor",
            "prompt": "flyover green gardens"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("render_time_sec", data)
        self.assertIn("image_base64", data)
        self.assertIn("message", data)
        self.assertTrue(data["image_base64"].startswith("data:image/png;base64,"))

if __name__ == "__main__":
    unittest.main()
