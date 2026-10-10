import unittest
import os
import tempfile
import sqlite3
import json
import numpy as np
import cv2

from src.db.schema import init_db, seed_sample_stations, get_connection
from src.reid.enrollment import TigerEnrollmentEngine


class DeterministicMockMatcher:
    """Mock matcher providing controlled similarity scores and synthetic embeddings."""
    def __init__(self, score_map=None, default_score=0.0):
        self.score_map = score_map or {}
        self.default_score = default_score

    def extract_deep_embedding(self, img_path):
        if not os.path.exists(img_path):
            return None
        return np.ones(128, dtype=np.float32) / np.sqrt(128)

    def compare_flanks(self, query_path, ref_path, query_emb=None, ref_emb=None):
        pair_key = (os.path.basename(query_path), os.path.basename(ref_path))
        score = self.score_map.get(pair_key, self.default_score)
        return {
            "combined_score": round(score, 4),
            "sift_score": round(score, 4),
            "cosine_score": round(score, 4),
            "good_matches_count": int(score * 30),
        }

    def generate_sift_match_visualization(self, query_path, ref_path, output_path, max_draw=25):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Write valid minimal dummy JPEG
        dummy = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.imwrite(output_path, dummy)
        return output_path


class TestTigerEnrollmentAuditedLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_audit.db")
        init_db(self.db_path)
        seed_sample_stations(self.db_path)
        self.conn = get_connection(self.db_path)

        # Create valid dummy test images
        self.img1_path = os.path.join(self.temp_dir, "query_01.jpg")
        self.ref1_path = os.path.join(self.temp_dir, "ref_bajirao.jpg")
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(self.img1_path, dummy_img)
        cv2.imwrite(self.ref1_path, dummy_img)

        self.viz_dir = os.path.join(self.temp_dir, "viz")
        os.makedirs(self.viz_dir, exist_ok=True)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sighting(self, image_path, species="tiger"):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_crop_path)
        VALUES (?, ?, 'PTR_STN_01', '2026-10-10 10:00:00', ?, ?);
        """, (os.path.basename(image_path), image_path, species, image_path))
        self.conn.commit()
        return cur.lastrowid

    def _enroll_reference_tiger(self, tiger_id="BAJIRAO", name="Bajirao", ref_path=None, species=None):
        cur = self.conn.cursor()
        path = ref_path or self.ref1_path
        emb = [1.0] * 128
        cols = [r[1] for r in cur.execute("PRAGMA table_info(tigers);").fetchall()]
        if "species" in cols:
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, reference_crop_path, stripe_features_json, status, species)
            VALUES (?, ?, 'M', ?, ?, 'resident', ?);
            """, (tiger_id, name, path, json.dumps(emb), species or "tiger"))
        else:
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, reference_crop_path, stripe_features_json, status)
            VALUES (?, ?, 'M', ?, ?, 'resident');
            """, (tiger_id, name, path, json.dumps(emb)))
        self.conn.commit()

    # -------------------------------------------------------------------------
    # TEST 1: Empty catalogue must not produce a falsely certain identity
    # -------------------------------------------------------------------------
    def test_01_empty_catalogue_safety(self):
        matcher = DeterministicMockMatcher(default_score=0.0)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        # Must not claim 1.0 confidence on empty catalogue
        self.assertNotEqual(res["confidence"], 1.0, "Empty catalogue must not produce confidence 1.0")
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["decision_state"], "new_identity_candidate")
        self.assertIsNone(res["assigned_tiger_id"])
        self.assertEqual(res["suggested_tiger_id"], "PTR_T_001")
        self.assertTrue(res.get("requires_approval", False))

        # Must NOT auto-insert permanent tiger into DB
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tigers;")
        self.assertEqual(cur.fetchone()[0], 0, "No tiger should be permanently enrolled into tigers table")

        # Sighting review status must remain pending_review
        cur.execute("SELECT tiger_id, review_status, reid_score FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertIsNone(s_row["tiger_id"])
        self.assertEqual(s_row["review_status"], "pending_review")
        self.assertEqual(s_row["reid_score"], 0.0)

    # -------------------------------------------------------------------------
    # TEST 2: A strong valid match returns 'matched'
    # -------------------------------------------------------------------------
    def test_02_strong_match_returns_matched(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        matcher = DeterministicMockMatcher(default_score=0.88)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        self.assertEqual(res["decision_state"], "matched")
        self.assertEqual(res["decision"], "matched")
        self.assertEqual(res["assigned_tiger_id"], "BAJIRAO")
        self.assertEqual(res["confidence"], 0.88)

        # Check DB updated as confirmed
        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertEqual(s_row["tiger_id"], "BAJIRAO")
        self.assertEqual(s_row["review_status"], "confirmed")

    # -------------------------------------------------------------------------
    # TEST 3: Low-similarity observation does not create permanent identity
    # -------------------------------------------------------------------------
    def test_03_low_similarity_no_automatic_enrollment(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        matcher = DeterministicMockMatcher(default_score=0.15)  # < 0.35
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        self.assertEqual(res["decision_state"], "new_identity_candidate")
        self.assertIsNone(res["assigned_tiger_id"])
        self.assertTrue(res["requires_approval"])

        # Tigers table count must remain 1
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tigers;")
        self.assertEqual(cur.fetchone()[0], 1, "Tigers table count must remain unchanged")

        # Staged in review queue
        cur.execute("SELECT status, suggested_tiger_id FROM review_queue WHERE sighting_id = ?;", (sighting_id,))
        rq_row = cur.fetchone()
        self.assertIsNotNone(rq_row)
        self.assertEqual(rq_row["status"], "pending")

    # -------------------------------------------------------------------------
    # TEST 4: An ambiguous match returns 'review_required'
    # -------------------------------------------------------------------------
    def test_04_ambiguous_match_returns_review_required(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        matcher = DeterministicMockMatcher(default_score=0.42)  # Between 0.35 and 0.50
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        self.assertEqual(res["decision_state"], "review_required")
        self.assertEqual(res["suggested_tiger_id"], "BAJIRAO")
        self.assertEqual(res["confidence"], 0.42)
        self.assertTrue(res["requires_approval"])
        self.assertIsNotNone(res.get("viz_path"))

        cur = self.conn.cursor()
        cur.execute("SELECT review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        self.assertEqual(cur.fetchone()["review_status"], "pending_review")

    # -------------------------------------------------------------------------
    # TEST 5: Possible duplicate is flagged before new identity approval
    # -------------------------------------------------------------------------
    def test_05_duplicate_flagged_before_approval(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        # Duplicate matcher detects high similarity (0.65 >= duplicate_threshold 0.30)
        matcher = DeterministicMockMatcher(default_score=0.65)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, duplicate_threshold=0.30, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)

        # Attempt to approve without force -> must be blocked
        approval_res = engine.approve_new_identity(sighting_id, candidate_id="PTR_T_099", force=False)
        self.assertEqual(approval_res["status"], "possible_duplicate_flagged")
        self.assertTrue(approval_res["duplicate_flagged"])
        self.assertEqual(approval_res["top_match_id"], "BAJIRAO")

        # Verify not enrolled
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tigers WHERE tiger_id = 'PTR_T_099';")
        self.assertEqual(cur.fetchone()[0], 0)

        # Attempt with force=True -> approval succeeds
        forced_res = engine.approve_new_identity(sighting_id, candidate_id="PTR_T_099", force=True)
        self.assertEqual(forced_res["status"], "enrolled")
        cur.execute("SELECT COUNT(*) FROM tigers WHERE tiger_id = 'PTR_T_099';")
        self.assertEqual(cur.fetchone()[0], 1)

    # -------------------------------------------------------------------------
    # TEST 6: Missing or invalid image features are handled safely
    # -------------------------------------------------------------------------
    def test_06_missing_or_invalid_image_handled_safely(self):
        matcher = DeterministicMockMatcher(default_score=0.90)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        # Call with nonexistent path
        res = engine.identify_and_enroll("nonexistent/invalid_file.jpg", sighting_id, "invalid.jpg")

        self.assertEqual(res["decision_state"], "unknown")
        self.assertIsNone(res["assigned_tiger_id"])
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["reason"], "invalid_or_missing_image_features")

    # -------------------------------------------------------------------------
    # TEST 7: Existing callers continue to work with updated return structure
    # -------------------------------------------------------------------------
    def test_07_backward_compatibility_with_existing_callers(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        matcher = DeterministicMockMatcher(default_score=0.92)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        # Existing callers expect: "decision", "assigned_tiger_id" or "suggested_tiger_id", "confidence", "top_candidates"
        self.assertIn("decision", res)
        self.assertIn("confidence", res)
        self.assertIn("top_candidates", res)
        assigned = res.get("assigned_tiger_id") or res.get("suggested_tiger_id")
        self.assertIsNotNone(assigned)
        self.assertIsInstance(res["confidence"], (float, int))
        self.assertIsInstance(res["top_candidates"], list)

    # -------------------------------------------------------------------------
    # TEST 8: Species mismatch is handled correctly when species metadata is available
    # -------------------------------------------------------------------------
    def test_08_species_mismatch_filtering(self):
        # Add 'species' column to tigers table if not exists for multi-species test
        cur = self.conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(tigers);").fetchall()]
        if "species" not in cols:
            cur.execute("ALTER TABLE tigers ADD COLUMN species TEXT DEFAULT 'tiger';")
            self.conn.commit()

        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path, species="tiger")
        matcher = DeterministicMockMatcher(default_score=0.95)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)

        # Sighting of a leopard
        sighting_id = self._create_sighting(self.img1_path, species="leopard")
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg", species="leopard")

        # Should not match tiger Bajirao because species is leopard and catalogue only has tigers
        self.assertNotEqual(res["decision_state"], "matched")
        self.assertIsNone(res["assigned_tiger_id"])
        self.assertEqual(len(res["top_candidates"]), 0, "No tiger should be matched for a leopard observation")

    # -------------------------------------------------------------------------
    # TEST 9: Similarity thresholds are configurable
    # -------------------------------------------------------------------------
    def test_09_configurable_thresholds(self):
        self._enroll_reference_tiger("BAJIRAO", "Bajirao", self.ref1_path)
        matcher = DeterministicMockMatcher(default_score=0.70)

        # With default high_thresh (0.50), score 0.70 is 'matched'
        engine_default = TigerEnrollmentEngine(self.conn, matcher=matcher, viz_dir=self.viz_dir)
        s1 = self._create_sighting(self.img1_path)
        res1 = engine_default.identify_and_enroll(self.img1_path, s1, "query_01.jpg")
        self.assertEqual(res1["decision_state"], "matched")

        # With strict high_thresh (0.85), score 0.70 becomes 'review_required'
        engine_strict = TigerEnrollmentEngine(
            self.conn, high_confidence_threshold=0.85, low_confidence_threshold=0.60, matcher=matcher, viz_dir=self.viz_dir
        )
        s2 = self._create_sighting(self.img1_path)
        res2 = engine_strict.identify_and_enroll(self.img1_path, s2, "query_01.jpg")
        self.assertEqual(res2["decision_state"], "review_required")

    # -------------------------------------------------------------------------
    # TEST 10: Permanent enrollment occurs only through intended approval flow
    # -------------------------------------------------------------------------
    def test_10_permanent_enrollment_only_on_approval(self):
        matcher = DeterministicMockMatcher(default_score=0.10)
        engine = TigerEnrollmentEngine(self.conn, matcher=matcher, duplicate_threshold=0.30, viz_dir=self.viz_dir)

        sighting_id = self._create_sighting(self.img1_path)
        res = engine.identify_and_enroll(self.img1_path, sighting_id, "query_01.jpg")

        # Step A: Observation is a candidate, not permanently enrolled
        self.assertEqual(res["decision_state"], "new_identity_candidate")
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tigers;")
        self.assertEqual(cur.fetchone()[0], 0)

        # Step B: Explicit human approval is executed
        approval = engine.approve_new_identity(
            sighting_id, candidate_id="PTR_T_100", name="New Resident 100", gender="M", force=False
        )
        self.assertEqual(approval["status"], "enrolled")
        self.assertEqual(approval["tiger_id"], "PTR_T_100")

        # Step C: Now permanently present in database with confirmed status
        cur.execute("SELECT name, gender, reference_crop_path FROM tigers WHERE tiger_id = 'PTR_T_100';")
        t_row = cur.fetchone()
        self.assertIsNotNone(t_row)
        self.assertEqual(t_row["name"], "New Resident 100")

        cur.execute("SELECT tiger_id, review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertEqual(s_row["tiger_id"], "PTR_T_100")
        self.assertEqual(s_row["review_status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
