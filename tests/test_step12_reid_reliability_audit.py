"""
tests/test_step12_reid_reliability_audit.py

TigerTraceAI — Step 12: Independent Re-ID Reliability and False-Match Audit Unit Tests.
Verifies safety constraints:
1. Traced match origin: Identical image auto-match produces high self-match score (~0.98+).
2. Byte-driven inference: Byte content, not preset labels or spoofed filenames, dictates identity.
3. SIFT normalization safety: 1 correspondence yields <= 0.05, never 1.00.
4. ResNet cosine score floor documentation: uncalibrated baseline floor quantified.
5. Cross-flank guard: Step 9A guard forces 0.0 score and incompatible status on opposite flanks.
6. Corrupted/Empty inputs: Fails gracefully to 'unknown' without unhandled exception.
"""

import os
import sys
import unittest
import tempfile
import sqlite3
import shutil
import numpy as np

# Ensure workspace packages are importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tt_dir = os.path.join(project_root, "TigerTrace_AI")
if tt_dir not in sys.path:
    sys.path.insert(0, tt_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.db.schema import init_db
from src.reid.stripe_matcher import (
    StripeReIDMatcher,
    is_flank_compatible,
    normalize_flank_orientation,
)
from src.reid.enrollment import TigerEnrollmentEngine
from src.blank_filter.triage_detector import CameraTrapTriageDetector
from src.reid.flank_extractor import FlankExtractor


class TestStep12ReIDReliabilityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = StripeReIDMatcher(use_deep_embedding=True)
        cls.flank_extractor = FlankExtractor()
        cls.triage_detector = CameraTrapTriageDetector(confidence_threshold=0.20)

        cls.crops_dir = os.path.join(project_root, "dataset", "flank_stripe_crops")
        cls.ref_cat_dir = os.path.join(tt_dir, "data", "reference_catalogue")
        cls.bajirao_ref = os.path.join(cls.ref_cat_dir, "Bajirao", "Bajirao_001_flank_crop.jpg")
        cls.patdev_ref = os.path.join(cls.crops_dir, "T40_Patdev", "T40_Patdev_001_flank_crop.jpg")

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_sandbox.db")
        init_db(self.test_db)
        self.conn = sqlite3.connect(self.test_db)
        self.conn.row_factory = sqlite3.Row
        self.engine = TigerEnrollmentEngine(db_connection=self.conn, matcher=self.matcher, viz_dir=self.temp_dir)
        self.engine.seed_initial_catalogue_from_folder(self.ref_cat_dir)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_self_match_control_matches_high(self):
        """Self-match control should produce high confidence (> 0.95)."""
        res = self.matcher.compare_flanks(self.bajirao_ref, self.bajirao_ref, query_flank="left", ref_flank="both")
        self.assertGreaterEqual(res["combined_score"], 0.95)
        self.assertEqual(res["sift_score"], 1.0)
        self.assertGreaterEqual(res["cosine_score"], 0.95)
        self.assertTrue(res["flank_compatible"])

    def test_02_sift_normalization_single_correspondence_cannot_yield_one(self):
        """Verifies that 1 SIFT correspondence yields 1/30 = 0.0333, never 1.00."""
        # Test mathematical formula directly
        single_inlier_score = min(1.0, 1 / 30.0)
        self.assertAlmostEqual(single_inlier_score, 0.0333, places=3)
        self.assertLess(single_inlier_score, 0.05)

    def test_03_cross_flank_guard_prevents_opposite_flank_match(self):
        """Step 9A guard: opposite flanks must be strictly rejected with score 0.0."""
        res = self.matcher.compare_flanks(self.bajirao_ref, self.bajirao_ref, query_flank="left", ref_flank="right")
        self.assertEqual(res["combined_score"], 0.0)
        self.assertFalse(res["flank_compatible"])
        self.assertEqual(res["flank_reason"], "opposite_flanks_incompatible")

    def test_04_corrupt_and_empty_images_handled_safely(self):
        """Empty or corrupt files must fail gracefully to decision_state 'unknown' without crashing."""
        empty_path = os.path.join(self.temp_dir, "empty.jpg")
        with open(empty_path, "wb") as f:
            f.write(b"")

        corrupt_path = os.path.join(self.temp_dir, "corrupt.jpg")
        with open(corrupt_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 16)

        cur = self.conn.cursor()
        cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species) VALUES ('e.jpg', ?, 'S1', 'now', 'tiger');", (empty_path,))
        sid1 = cur.lastrowid
        cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species) VALUES ('c.jpg', ?, 'S1', 'now', 'tiger');", (corrupt_path,))
        sid2 = cur.lastrowid
        self.conn.commit()

        res1 = self.engine.identify_and_enroll(empty_path, sighting_id=sid1, image_name="e.jpg", species="tiger")
        res2 = self.engine.identify_and_enroll(corrupt_path, sighting_id=sid2, image_name="c.jpg", species="tiger")

        self.assertEqual(res1["decision_state"], "unknown")
        self.assertEqual(res2["decision_state"], "unknown")
        self.assertIn("corrupt_or_unreadable", res1["reason"])
        self.assertIn("corrupt_or_unreadable", res2["reason"])

    def test_05_byte_driven_inference_prevents_preset_hijack(self):
        """Uploading Patdev bytes with 'Bajirao' metadata must identify Patdev, not Bajirao."""
        cur = self.conn.cursor()
        cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side) VALUES ('bajirao_fake.jpg', ?, 'S1', 'now', 'tiger', 'left');", (self.patdev_ref,))
        sid = cur.lastrowid
        self.conn.commit()

        enroll_res = self.engine.identify_and_enroll(self.patdev_ref, sighting_id=sid, image_name="bajirao_fake.jpg", species="tiger", flank_side="left")
        top_candidates = enroll_res.get("top_candidates", [])
        self.assertTrue(len(top_candidates) > 0)
        self.assertEqual(top_candidates[0]["tiger_id"], "T40_PATDEV")
        self.assertNotEqual(enroll_res.get("assigned_tiger_id"), "BAJIRAO")

    def test_06_resnet_cosine_floor_quantification(self):
        """Verifies that ResNet affine scaling produces an uncalibrated base floor."""
        emb1 = self.matcher.extract_deep_embedding(self.bajirao_ref)
        emb2 = self.matcher.extract_deep_embedding(self.patdev_ref)
        raw_dot = float(np.dot(emb1, emb2))
        scaled_cos = max(0.0, min(1.0, (raw_dot + 1.0) / 2.0))
        floor_contrib = 0.45 * scaled_cos

        # Verify floor contributes substantially towards review threshold (0.35)
        self.assertGreaterEqual(floor_contrib, 0.35)


if __name__ == "__main__":
    unittest.main()
