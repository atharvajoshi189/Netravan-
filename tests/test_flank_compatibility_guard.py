import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
import tempfile
import shutil

# Ensure workspace TigerTrace_AI package is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pkg_dir = os.path.join(repo_root, "TigerTrace_AI")
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.reid.stripe_matcher import StripeReIDMatcher, is_flank_compatible, normalize_flank_orientation
from src.reid.enrollment import TigerEnrollmentEngine
from src.db.schema import init_db, seed_sample_stations, get_connection


class TestFlankCompatibilityGuard(unittest.TestCase):
    """
    Step 9A: Flank Compatibility Guard Regression Test Suite.
    Validates:
    1. Left versus left: compatible comparison reaches the feature matcher.
    2. Right versus right: compatible comparison reaches the feature matcher.
    3. Left versus right: rejected before SIFT or deep-feature matching.
    4. Right versus left: rejected before SIFT or deep-feature matching.
    5. Unknown query orientation: safe rejection without feature calculation.
    6. Unknown reference orientation: safe rejection without feature calculation.
    7. Existing matcher callers and return-value contract remain compatible.
    8. Enrollment engine does not select an incompatible reference.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.img1_path = os.path.join(self.temp_dir, "tiger_left_01.jpg")
        self.img2_path = os.path.join(self.temp_dir, "tiger_right_01.jpg")

        # Create valid synthetic test images
        np.random.seed(42)
        im1 = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        im2 = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        cv2.imwrite(self.img1_path, im1)
        cv2.imwrite(self.img2_path, im2)

        # Matcher instance without deep embedding for fast isolated unit testing
        self.matcher = StripeReIDMatcher(use_deep_embedding=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Left versus left: compatible comparison reaches the matcher
    # -------------------------------------------------------------------------
    def test_01_left_vs_left_reaches_matcher(self):
        with patch.object(self.matcher, 'match_sift_stripes', wraps=self.matcher.match_sift_stripes) as spy_sift:
            res = self.matcher.compare_flanks(
                self.img1_path, self.img2_path,
                query_flank="left", ref_flank="left"
            )
            self.assertTrue(res["flank_compatible"])
            self.assertEqual(res["flank_reason"], "compatible")
            self.assertTrue(spy_sift.called, "SIFT matching MUST execute for compatible left-left comparison")

    # -------------------------------------------------------------------------
    # 2. Right versus right: compatible comparison reaches the matcher
    # -------------------------------------------------------------------------
    def test_02_right_vs_right_reaches_matcher(self):
        with patch.object(self.matcher, 'match_sift_stripes', wraps=self.matcher.match_sift_stripes) as spy_sift:
            res = self.matcher.compare_flanks(
                self.img1_path, self.img2_path,
                query_flank="right", ref_flank="right"
            )
            self.assertTrue(res["flank_compatible"])
            self.assertEqual(res["flank_reason"], "compatible")
            self.assertTrue(spy_sift.called, "SIFT matching MUST execute for compatible right-right comparison")

    # -------------------------------------------------------------------------
    # 3. Left versus right: rejected before feature matching
    # -------------------------------------------------------------------------
    def test_03_left_vs_right_rejected_before_feature_matching(self):
        with patch.object(self.matcher, 'match_sift_stripes') as mock_sift, \
             patch.object(self.matcher, 'extract_deep_embedding') as mock_deep:
            res = self.matcher.compare_flanks(
                self.img1_path, self.img2_path,
                query_flank="left", ref_flank="right"
            )
            self.assertFalse(res["flank_compatible"])
            self.assertEqual(res["flank_reason"], "opposite_flanks_incompatible")
            self.assertEqual(res["combined_score"], 0.0)
            self.assertEqual(res["sift_score"], 0.0)
            self.assertEqual(res["cosine_score"], 0.0)
            self.assertEqual(res["good_matches_count"], 0)
            self.assertFalse(mock_sift.called, "SIFT matching MUST NOT execute for opposite flanks (left vs right)")
            self.assertFalse(mock_deep.called, "Deep embedding MUST NOT execute for opposite flanks (left vs right)")

    # -------------------------------------------------------------------------
    # 4. Right versus left: rejected before feature matching
    # -------------------------------------------------------------------------
    def test_04_right_vs_left_rejected_before_feature_matching(self):
        with patch.object(self.matcher, 'match_sift_stripes') as mock_sift, \
             patch.object(self.matcher, 'extract_deep_embedding') as mock_deep:
            res = self.matcher.compare_flanks(
                self.img1_path, self.img2_path,
                query_flank="right", ref_flank="left"
            )
            self.assertFalse(res["flank_compatible"])
            self.assertEqual(res["flank_reason"], "opposite_flanks_incompatible")
            self.assertEqual(res["combined_score"], 0.0)
            self.assertEqual(res["sift_score"], 0.0)
            self.assertEqual(res["cosine_score"], 0.0)
            self.assertEqual(res["good_matches_count"], 0)
            self.assertFalse(mock_sift.called, "SIFT matching MUST NOT execute for opposite flanks (right vs left)")
            self.assertFalse(mock_deep.called, "Deep embedding MUST NOT execute for opposite flanks (right vs left)")

    # -------------------------------------------------------------------------
    # 5. Unknown query orientation: safe rejection
    # -------------------------------------------------------------------------
    def test_05_unknown_query_orientation_safe_rejection(self):
        for unknown_val in ["unknown", "ambiguous", None, ""]:
            with patch.object(self.matcher, 'match_sift_stripes') as mock_sift, \
                 patch.object(self.matcher, 'extract_deep_embedding') as mock_deep:
                res = self.matcher.compare_flanks(
                    self.img1_path, self.img2_path,
                    query_flank=unknown_val, ref_flank="left"
                )
                self.assertFalse(res["flank_compatible"])
                self.assertIn("unknown", res["flank_reason"])
                self.assertEqual(res["combined_score"], 0.0)
                self.assertFalse(mock_sift.called, f"SIFT MUST NOT execute when query_flank={unknown_val}")
                self.assertFalse(mock_deep.called, f"Deep embedding MUST NOT execute when query_flank={unknown_val}")

    # -------------------------------------------------------------------------
    # 6. Unknown reference orientation: safe rejection
    # -------------------------------------------------------------------------
    def test_06_unknown_reference_orientation_safe_rejection(self):
        for unknown_val in ["unknown", "ambiguous", None, ""]:
            with patch.object(self.matcher, 'match_sift_stripes') as mock_sift, \
                 patch.object(self.matcher, 'extract_deep_embedding') as mock_deep:
                res = self.matcher.compare_flanks(
                    self.img1_path, self.img2_path,
                    query_flank="left", ref_flank=unknown_val
                )
                self.assertFalse(res["flank_compatible"])
                self.assertIn("unknown", res["flank_reason"])
                self.assertEqual(res["combined_score"], 0.0)
                self.assertFalse(mock_sift.called, f"SIFT MUST NOT execute when ref_flank={unknown_val}")
                self.assertFalse(mock_deep.called, f"Deep embedding MUST NOT execute when ref_flank={unknown_val}")

    # -------------------------------------------------------------------------
    # 7. Existing matcher callers and return-value contract remain compatible
    # -------------------------------------------------------------------------
    def test_07_existing_callers_and_return_contract(self):
        # Compatible comparison contract
        res_comp = self.matcher.compare_flanks(
            self.img1_path, self.img2_path,
            query_flank="left", ref_flank="left"
        )
        expected_keys = {
            "combined_score", "sift_score", "cosine_score", "good_matches_count",
            "kp_query", "kp_ref", "matches", "flank_compatible", "flank_reason", "reason"
        }
        self.assertTrue(expected_keys.issubset(res_comp.keys()), "Missing expected return keys in compatible comparison")

        # Incompatible comparison contract
        res_incomp = self.matcher.compare_flanks(
            self.img1_path, self.img2_path,
            query_flank="left", ref_flank="right"
        )
        self.assertTrue(expected_keys.issubset(res_incomp.keys()), "Missing expected return keys in incompatible comparison")
        self.assertEqual(res_incomp["combined_score"], 0.0)
        self.assertEqual(res_incomp["kp_query"], [])
        self.assertEqual(res_incomp["matches"], [])

        # SIFT visualization guard: skipped when flanks are incompatible
        viz_out = os.path.join(self.temp_dir, "viz_test.jpg")
        viz_result = self.matcher.generate_sift_match_visualization(
            self.img1_path, self.img2_path, viz_out,
            query_flank="left", ref_flank="right"
        )
        self.assertIsNone(viz_result, "Visualization generation must return None for incompatible flanks")
        self.assertFalse(os.path.exists(viz_out), "Visualization image must not be written for incompatible flanks")

        # Flank normalization aliases
        self.assertEqual(normalize_flank_orientation("left_flank"), "left")
        self.assertEqual(normalize_flank_orientation("L"), "left")
        self.assertEqual(normalize_flank_orientation("right_flank"), "right")
        self.assertEqual(normalize_flank_orientation("R"), "right")
        self.assertEqual(normalize_flank_orientation("both_flanks"), "both")
        self.assertEqual(normalize_flank_orientation("bilateral"), "both")
        self.assertEqual(normalize_flank_orientation("frontal"), "unknown")

    # -------------------------------------------------------------------------
    # 8. Enrollment does not select an incompatible reference
    # -------------------------------------------------------------------------
    def test_08_enrollment_does_not_select_incompatible_reference(self):
        db_path = os.path.join(self.temp_dir, "sandbox_enrollment.db")
        init_db(db_path)
        seed_sample_stations(db_path)
        conn = get_connection(db_path)
        cur = conn.cursor()

        try:
            # Seed Reference Tigers:
            # TIGER_R has right flank (incompatible with left query)
            # TIGER_L has left flank (compatible with left query)
            ref_r = os.path.join(self.temp_dir, "ref_r.jpg")
            ref_l = os.path.join(self.temp_dir, "ref_l.jpg")
            cv2.imwrite(ref_r, np.zeros((50, 50, 3), dtype=np.uint8))
            cv2.imwrite(ref_l, np.zeros((50, 50, 3), dtype=np.uint8))

            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, status)
            VALUES ('TIGER_R', 'Right Flank Tiger', 'M', 'right', '2026-01-01', ?, 'resident');
            """, (ref_r,))

            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, status)
            VALUES ('TIGER_L', 'Left Flank Tiger', 'F', 'left', '2026-01-01', ?, 'resident');
            """, (ref_l,))
            conn.commit()

            # Controlled Mock Matcher:
            # If opposite flank were mistakenly evaluated, it would return impostor score 0.99.
            # Compatible left-flank returns 0.75.
            class FlankAuditMockMatcher:
                def __init__(self):
                    self.compared_pairs = []

                def extract_deep_embedding(self, p):
                    return np.ones(64, dtype=np.float32)

                def compare_flanks(self, query_path, ref_path, query_emb=None, ref_emb=None, query_flank=None, ref_flank=None, *args, **kwargs):
                    self.compared_pairs.append({
                        "query_path": query_path,
                        "ref_path": ref_path,
                        "query_flank": query_flank,
                        "ref_flank": ref_flank,
                    })
                    if "ref_r.jpg" in ref_path:
                        # Incompatible tiger - if called, return high score to trap leakage
                        return {
                            "combined_score": 0.99,
                            "sift_score": 0.99,
                            "cosine_score": 0.99,
                            "good_matches_count": 30,
                            "flank_compatible": False,
                        }
                    else:
                        # Compatible tiger
                        return {
                            "combined_score": 0.75,
                            "sift_score": 0.75,
                            "cosine_score": 0.75,
                            "good_matches_count": 25,
                            "flank_compatible": True,
                        }

                def generate_sift_match_visualization(self, *args, **kwargs):
                    return None

            mock_matcher = FlankAuditMockMatcher()
            engine = TigerEnrollmentEngine(db_connection=conn, matcher=mock_matcher, viz_dir=self.temp_dir, allow_auto_confirm=True)

            # Insert Left Flank Sighting
            query_crop = os.path.join(self.temp_dir, "sighting_query_left.jpg")
            cv2.imwrite(query_crop, np.zeros((50, 50, 3), dtype=np.uint8))
            cur.execute("""
            INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_crop_path, flank_side)
            VALUES ('query.jpg', ?, 'PTR_STN_01', '2026-10-10 10:00:00', 'tiger', ?, 'left');
            """, (query_crop, query_crop))
            sighting_id = cur.lastrowid
            conn.commit()

            # Execute Re-ID and Enrollment
            res = engine.identify_and_enroll(query_crop, sighting_id, "query.jpg", species="tiger", flank_side="left")

            # Must match TIGER_L, NOT TIGER_R
            self.assertEqual(res["decision_state"], "matched")
            self.assertEqual(res["assigned_tiger_id"], "TIGER_L")
            self.assertEqual(res["confidence"], 0.75)

            # Assert TIGER_R was completely excluded from comparison candidates
            compared_ref_paths = [p["ref_path"] for p in mock_matcher.compared_pairs]
            self.assertNotIn(ref_r, compared_ref_paths, "Incompatible reference TIGER_R MUST NOT reach compare_flanks")
            self.assertIn(ref_l, compared_ref_paths, "Compatible reference TIGER_L MUST reach compare_flanks")

            # Test Unknown Sighting Guard:
            # Query sighting with unknown flank orientation MUST NOT match any candidate
            cur.execute("""
            INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_crop_path, flank_side)
            VALUES ('query_unk.jpg', ?, 'PTR_STN_01', '2026-10-10 10:00:00', 'tiger', ?, 'unknown');
            """, (query_crop, query_crop))
            unk_sighting_id = cur.lastrowid
            conn.commit()

            mock_matcher.compared_pairs.clear()
            res_unk = engine.identify_and_enroll(query_crop, unk_sighting_id, "query_unk.jpg", species="tiger", flank_side="unknown")

            self.assertEqual(res_unk["decision_state"], "new_identity_candidate")
            self.assertEqual(res_unk["confidence"], 0.0)
            self.assertFalse(res_unk["flank_compatible"])
            self.assertEqual(len(mock_matcher.compared_pairs), 0, "No candidate must reach compare_flanks when query flank is unknown")

        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
