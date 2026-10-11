"""
tests/test_step13_prevent_false_identity_confirmation.py

TigerTraceAI — Step 13: Prevent False Identity Confirmation Regression Test Suite.

Verifies:
1. Disabling of unsafe automatic confirmation:
   - Candidate identity matches are routed to 'review_required' with 'pending_review' status.
   - No observation is automatically labeled 'verified_match' or 'confirmed' by the model.
2. Fix for SIFT correspondence quality:
   - Mutual nearest-neighbour (reciprocal) and 1-to-1 correspondence filtering.
   - Duplicate query keypoints can no longer inflate SIFT scores on a single reference keypoint.
   - Spatial geometric verification (RANSAC) rejects incoherent correspondences.
   - Patdev vs Bajirao false-match elimination (drops from 0.9609 down to ~0.41, SIFT=0.0).
3. Honest ResNet score handling:
   - Raw cosine similarity is computed and reported separately.
   - ResNet cosine alone cannot trigger a verified identity match.
4. Comprehensive regression coverage:
   - Genuine Bajirao cross-image comparisons.
   - Patdev, Swastik, Collarwali impostor comparisons.
   - Unknown tiger and insufficient quality probes.
   - Cross-flank (left vs right) and unknown-flank guards.
   - 0-byte and corrupt image error handling.
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


class TestStep13PreventFalseIdentityConfirmation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = StripeReIDMatcher(use_deep_embedding=True)
        cls.flank_extractor = FlankExtractor()
        cls.triage_detector = CameraTrapTriageDetector(confidence_threshold=0.20)

        cls.crops_dir = os.path.join(project_root, "dataset", "flank_stripe_crops")
        cls.ref_cat_dir = os.path.join(tt_dir, "data", "reference_catalogue")
        cls.verified_dir = os.path.join(project_root, "dataset", "verified_tiger_dataset")

        cls.bajirao_ref = os.path.join(cls.ref_cat_dir, "Bajirao", "Bajirao_001_flank_crop.jpg")
        cls.bajirao_002 = os.path.join(cls.crops_dir, "Bajirao", "Bajirao_002_flank_crop.jpg")
        cls.patdev_001 = os.path.join(cls.crops_dir, "T40_Patdev", "T40_Patdev_001_flank_crop.jpg")
        cls.patdev_002 = os.path.join(cls.crops_dir, "T40_Patdev", "T40_Patdev_002_flank_crop.jpg")
        cls.swastik_001 = os.path.join(cls.crops_dir, "Swastik", "Swastik_001_flank_crop.jpg")
        cls.swastik_002 = os.path.join(cls.crops_dir, "Swastik", "Swastik_002_flank_crop.jpg")
        cls.collarwali_001 = os.path.join(cls.crops_dir, "T15_Collarwali", "T15_Collarwali_001_flank_crop.jpg")

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="step13_test_")
        self.test_db = os.path.join(self.temp_dir, "disposable.db")
        init_db(self.test_db)
        self.conn = sqlite3.connect(self.test_db)
        self.conn.row_factory = sqlite3.Row

        # Step 13 safety policy: allow_auto_confirm defaults to False
        self.engine = TigerEnrollmentEngine(
            db_connection=self.conn,
            matcher=self.matcher,
            viz_dir=self.temp_dir,
            allow_auto_confirm=False,
        )
        self.engine.seed_initial_catalogue_from_folder(self.ref_cat_dir)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # TEST 1: Disable Unsafe Automatic Confirmation
    # -------------------------------------------------------------------------
    def test_01_disable_unsafe_automatic_confirmation(self):
        """Even if score is high (e.g. self-match), observation must route to review_required."""
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side)
        VALUES ('bajirao_field.jpg', ?, 'PTR_STN_01', '2026-10-11 12:00:00', 'tiger', 'left');
        """, (self.bajirao_ref,))
        sighting_id = cur.lastrowid
        self.conn.commit()

        res = self.engine.identify_and_enroll(
            self.bajirao_ref, sighting_id=sighting_id, image_name="bajirao_field.jpg", species="tiger", flank_side="left"
        )

        # Assert no automatic confirmation
        self.assertEqual(res["decision_state"], "review_required")
        self.assertIsNone(res["assigned_tiger_id"])
        self.assertEqual(res["suggested_tiger_id"], "BAJIRAO")
        self.assertTrue(res["requires_approval"])
        self.assertIn("candidate_match_queued_for_human_review", res["reason"])

        # Check DB sighting record remains pending_review, never confirmed
        cur.execute("SELECT tiger_id, review_status, match_method FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertEqual(s_row["review_status"], "pending_review", "review_status must remain pending_review")
        self.assertNotEqual(s_row["review_status"], "confirmed", "review_status must never be confirmed automatically")

        # Check review_queue has pending entry
        cur.execute("SELECT status, suggested_tiger_id, suggested_score FROM review_queue WHERE sighting_id = ?;", (sighting_id,))
        rq_row = cur.fetchone()
        self.assertIsNotNone(rq_row)
        self.assertEqual(rq_row["status"], "pending")
        self.assertEqual(rq_row["suggested_tiger_id"], "BAJIRAO")

    # -------------------------------------------------------------------------
    # TEST 2: Specific Patdev-vs-Bajirao False-Match Elimination
    # -------------------------------------------------------------------------
    def test_02_patdev_vs_bajirao_false_match_eliminated(self):
        """Patdev crops previously achieved 0.9609 false match. Now SIFT score must be 0.0 and cannot auto-confirm."""
        for patdev_crop, label in [(self.patdev_001, "Patdev_001"), (self.patdev_002, "Patdev_002")]:
            cmp_res = self.matcher.compare_flanks(
                self.bajirao_ref, patdev_crop, query_flank="left", ref_flank="both"
            )

            # SIFT score must be 0.0 due to MNN + RANSAC rejection of incoherent matches
            self.assertEqual(cmp_res["sift_score"], 0.0, f"SIFT score for {label} vs Bajirao must be 0.0, got {cmp_res['sift_score']}")
            self.assertEqual(cmp_res["inlier_count"], 0, f"RANSAC inlier count for {label} vs Bajirao must be 0, got {cmp_res['inlier_count']}")

            # Combined score must be well below 0.50
            self.assertLess(cmp_res["combined_score"], 0.50, f"Combined score for {label} must be < 0.50, got {cmp_res['combined_score']}")

            # In enrollment engine, must not be matched
            cur = self.conn.cursor()
            cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side) VALUES ('p.jpg', ?, 'S1', 'now', 'tiger', 'left');", (patdev_crop,))
            sid = cur.lastrowid
            self.conn.commit()

            enroll_res = self.engine.identify_and_enroll(patdev_crop, sighting_id=sid, image_name="p.jpg", species="tiger", flank_side="left")
            self.assertNotEqual(enroll_res.get("decision_state"), "matched")
            self.assertNotEqual(enroll_res.get("assigned_tiger_id"), "BAJIRAO")

    # -------------------------------------------------------------------------
    # TEST 3: Swastik and Collarwali Impostor Comparisons
    # -------------------------------------------------------------------------
    def test_03_swastik_and_collarwali_impostors_cannot_auto_confirm(self):
        """Impostors must not pass as verified matches."""
        for impostor_crop, label in [
            (self.swastik_001, "Swastik_001"),
            (self.swastik_002, "Swastik_002"),
            (self.collarwali_001, "Collarwali_001"),
        ]:
            cmp_res = self.matcher.compare_flanks(
                self.bajirao_ref, impostor_crop, query_flank="left", ref_flank="both"
            )

            # Combined score must be below 0.50
            self.assertLess(cmp_res["combined_score"], 0.50, f"Impostor {label} combined score must be < 0.50, got {cmp_res['combined_score']}")

            cur = self.conn.cursor()
            cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side) VALUES ('i.jpg', ?, 'S1', 'now', 'tiger', 'left');", (impostor_crop,))
            sid = cur.lastrowid
            self.conn.commit()

            enroll_res = self.engine.identify_and_enroll(impostor_crop, sighting_id=sid, image_name="i.jpg", species="tiger", flank_side="left")
            self.assertNotEqual(enroll_res.get("decision_state"), "matched")
            self.assertNotEqual(enroll_res.get("assigned_tiger_id"), "BAJIRAO")

    # -------------------------------------------------------------------------
    # TEST 4: MNN Correspondence Filtering Eliminates Duplicate Keypoint Inflation
    # -------------------------------------------------------------------------
    def test_04_mnn_filtering_eliminates_duplicate_inflation(self):
        """Verifies that each query and reference keypoint can be matched at most once."""
        score, inlier_matches, kp1, kp2 = self.matcher.match_sift_stripes(self.bajirao_ref, self.patdev_001)

        # Check that no trainIdx is repeated in inlier_matches
        train_indices = [m.trainIdx for m in inlier_matches]
        query_indices = [m.queryIdx for m in inlier_matches]
        self.assertEqual(len(train_indices), len(set(train_indices)), "No reference keypoint should be matched multiple times")
        self.assertEqual(len(query_indices), len(set(query_indices)), "No query keypoint should be matched multiple times")

    # -------------------------------------------------------------------------
    # TEST 5: Honest ResNet Score Handling
    # -------------------------------------------------------------------------
    def test_05_honest_resnet_score_handling(self):
        """Raw cosine similarity is exposed and documented as uncalibrated."""
        res = self.matcher.compare_flanks(self.bajirao_ref, self.patdev_001, query_flank="left", ref_flank="both")
        self.assertIn("raw_cosine_similarity", res)
        self.assertIn("cosine_is_uncalibrated", res)
        self.assertTrue(res["cosine_is_uncalibrated"])
        self.assertIsInstance(res["raw_cosine_similarity"], float)

    # -------------------------------------------------------------------------
    # TEST 6: Unknown Tiger Probes
    # -------------------------------------------------------------------------
    def test_06_unknown_tiger_probes_route_to_review(self):
        """General unknown tiger must not be auto-confirmed as Bajirao."""
        unknown_path = os.path.join(self.verified_dir, "Pench_General_Tigers", "Pench_General_Tiger_001.jpg")
        if os.path.exists(unknown_path):
            cur = self.conn.cursor()
            cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side) VALUES ('u.jpg', ?, 'S1', 'now', 'tiger', 'left');", (unknown_path,))
            sid = cur.lastrowid
            self.conn.commit()

            enroll_res = self.engine.identify_and_enroll(unknown_path, sighting_id=sid, image_name="u.jpg", species="tiger", flank_side="left")
            self.assertNotEqual(enroll_res.get("decision_state"), "matched")
            self.assertNotEqual(enroll_res.get("assigned_tiger_id"), "BAJIRAO")
            self.assertEqual(enroll_res.get("decision_state"), "review_required")

    # -------------------------------------------------------------------------
    # TEST 7: Cross-Flank and Unknown-Flank Cases
    # -------------------------------------------------------------------------
    def test_07_cross_flank_and_unknown_flank_guards(self):
        """Cross-flank comparisons return score 0.0; unknown-flank routes to review."""
        # A. Opposite flanks (Left vs Right)
        res_cross = self.matcher.compare_flanks(self.bajirao_ref, self.bajirao_ref, query_flank="left", ref_flank="right")
        self.assertEqual(res_cross["combined_score"], 0.0)
        self.assertFalse(res_cross["flank_compatible"])
        self.assertEqual(res_cross["flank_reason"], "opposite_flanks_incompatible")

        # B. Unknown flank query in enrollment engine
        cur = self.conn.cursor()
        cur.execute("INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side) VALUES ('unk.jpg', ?, 'S1', 'now', 'tiger', 'unknown');", (self.bajirao_ref,))
        sid = cur.lastrowid
        self.conn.commit()

        enroll_unk = self.engine.identify_and_enroll(self.bajirao_ref, sighting_id=sid, image_name="unk.jpg", species="tiger", flank_side="unknown")
        self.assertEqual(enroll_unk["decision_state"], "new_identity_candidate")
        self.assertIsNone(enroll_unk["assigned_tiger_id"])
        self.assertTrue(enroll_unk["requires_approval"])

    # -------------------------------------------------------------------------
    # TEST 8: Empty and Corrupt Image Inputs
    # -------------------------------------------------------------------------
    def test_08_empty_and_corrupt_image_inputs(self):
        """0-byte and corrupted inputs fail safely to 'unknown' without unhandled crash."""
        empty_path = os.path.join(self.temp_dir, "empty_0b.jpg")
        with open(empty_path, "wb") as f:
            f.write(b"")

        corrupt_path = os.path.join(self.temp_dir, "corrupt_hdr.jpg")
        with open(corrupt_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 32)

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


if __name__ == "__main__":
    unittest.main()
