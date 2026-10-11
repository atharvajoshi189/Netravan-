import os
import sys
import unittest
import io
import cv2
import numpy as np

# Ensure workspace TigerTrace_AI package is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pkg_dir = os.path.join(repo_root, "TigerTrace_AI")
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from fastapi.testclient import TestClient
from ui.app import app


class TestSharedAnalysisApi(unittest.TestCase):
    """
    Step 10: Shared AI Backend Analysis & Mobile Sync API Test Suite.
    Validates:
    1. GET /api/health returns operational status and model versions.
    2. POST /api/analyze validates image payload (rejects non-images, bad files).
    3. POST /api/analyze handles blank / no-animal image gracefully (not_applicable identity status).
    4. POST /api/analyze performs full end-to-end detection, flank crop, Re-ID, and behavior forecast.
    5. POST /api/analyze handles missing GPS or timestamp metadata with safe fallbacks.
    6. GET /api/mobile/observations retrieves paginated field observations.
    7. GET /api/mobile/catalogue retrieves resident tiger biometrics.
    8. POST /api/mobile/sync_batch acknowledges offline observation logs.
    9. Step 9A flank guard and Step 9B bbox scaling remain preserved in API inference.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.ref_crop_path = os.path.join(
            pkg_dir, "data", "reference_catalogue", "Bajirao", "Bajirao_001_flank_crop.jpg"
        )
        if not os.path.exists(cls.ref_crop_path):
            # Fallback search for any available reference crop
            cat_dir = os.path.join(pkg_dir, "data", "reference_catalogue")
            for root, _, files in os.walk(cat_dir):
                for f in files:
                    if f.lower().endswith(".jpg"):
                        cls.ref_crop_path = os.path.join(root, f)
                        break

    def test_01_api_health(self):
        """Verify GET /api/health endpoint returns expected schema and models."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data.get("status"), ["ok", "operational"])
        self.assertIn("models", data)
        self.assertIn("step_9a_guard", data["models"])
        self.assertIn("step_9b_resolver", data["models"])
        self.assertEqual(data["models"]["step_9a_guard"], "active")

    def test_02_invalid_file_upload(self):
        """Verify POST /api/analyze rejects corrupted / non-image files."""
        # Non-image plain text file
        text_content = io.BytesIO(b"This is not a valid image file")
        response = self.client.post(
            "/api/analyze",
            files={"file": ("corrupt.txt", text_content, "text/plain")},
            data={"flank_hint": "unknown"}
        )
        self.assertIn(response.status_code, [400, 422])

    def test_03_blank_detection_image(self):
        """Verify POST /api/analyze detects no-animal blank frames correctly."""
        # Uniform green test frame
        blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
        blank_img[:] = (34, 139, 34)
        _, buf = cv2.imencode(".jpg", blank_img)
        img_bytes = io.BytesIO(buf.tobytes())

        response = self.client.post(
            "/api/analyze",
            files={"file": ("blank_test.jpg", img_bytes, "image/jpeg")},
            data={"flank_hint": "unknown", "station_id": "STATION-01"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("identity_status"), "not_applicable")
        self.assertIn(data.get("species"), ["blank", "unknown"])
        self.assertEqual(len(data.get("candidate_identities", [])), 0)

    def test_04_tiger_image_full_analysis(self):
        """Verify POST /api/analyze identifies known tiger and produces candidate match."""
        self.assertTrue(os.path.exists(self.ref_crop_path), f"Reference crop not found: {self.ref_crop_path}")

        with open(self.ref_crop_path, "rb") as f:
            img_bytes = io.BytesIO(f.read())

        response = self.client.post(
            "/api/analyze",
            files={"file": ("bajirao_test.jpg", img_bytes, "image/jpeg")},
            data={
                "flank_hint": "left",
                "station_id": "STATION-01",
                "latitude": "21.65",
                "longitude": "79.25"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("species"), "tiger")
        self.assertIn("candidate_identities", data)
        self.assertGreater(len(data["candidate_identities"]), 0)
        top_cand = data["candidate_identities"][0]
        self.assertEqual(top_cand.get("tiger_id"), "BAJIRAO")
        self.assertIn(data.get("identity_status"), ["review_required", "candidate_match", "verified_match"])
        self.assertEqual(data.get("identity_status"), "review_required")
        self.assertEqual(data.get("review_status"), "pending_review")
        self.assertIn("model_versions", data)
        self.assertIn("flank_guard", data["model_versions"])
        self.assertIn("bbox_resolver", data["model_versions"])

    def test_05_missing_gps_and_timestamp_fallbacks(self):
        """Verify POST /api/analyze handles missing GPS and timestamp gracefully."""
        self.assertTrue(os.path.exists(self.ref_crop_path), f"Reference crop not found: {self.ref_crop_path}")

        with open(self.ref_crop_path, "rb") as f:
            img_bytes = io.BytesIO(f.read())

        response = self.client.post(
            "/api/analyze",
            files={"file": ("bajirao_no_gps.jpg", img_bytes, "image/jpeg")},
            data={"flank_hint": "unknown"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data.get("timestamp"))
        self.assertIsNotNone(data.get("location"))

    def test_06_mobile_observations_endpoint(self):
        """Verify GET /api/mobile/observations retrieves sighting records."""
        response = self.client.get("/api/mobile/observations?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("observations", data)
        self.assertIsInstance(data["observations"], list)

    def test_07_mobile_catalogue_endpoint(self):
        """Verify GET /api/mobile/catalogue returns resident tiger catalogue."""
        response = self.client.get("/api/mobile/catalogue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        tiger_ids = [t.get("tiger_id") for t in data]
        self.assertIn("BAJIRAO", tiger_ids)

    def test_08_mobile_sync_batch_endpoint(self):
        """Verify POST /api/mobile/sync_batch acknowledges offline batches."""
        payload = {
            "items": [
                {"local_id": "LOC-001", "timestamp": "2026-10-10T12:00:00Z"},
                {"local_id": "LOC-002", "timestamp": "2026-10-10T12:05:00Z"}
            ]
        }
        response = self.client.post("/api/mobile/sync_batch", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("acknowledged_count"), 2)


if __name__ == "__main__":
    unittest.main()
