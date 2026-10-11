"""
tests/test_step14_human_in_the_loop_review.py

TigerTraceAI — Step 14: Human-in-the-Loop Identity Review Regression Test Suite.
Validates:
1. Complete Biometric Evidence in Queue: submitted image, proposed candidate, reference crop,
   flanks, SIFT inliers, geometric status, raw ResNet cosine, uncalibrated warning.
2. Acceptance Flow: Authorized reviewer accepts candidate -> updates sighting to confirmed,
   records reviewer ID, timestamp, reason, and preserves audit log.
3. Rejection Flow: Authorized reviewer rejects candidate -> clears identity, marks sighting rejected.
4. Inconclusive Flow: Authorized reviewer marks observation inconclusive -> clears identity.
5. Invalid Request Guards: Rejects invalid actions, missing reviewer ID, empty reason with 400.
6. Duplicate Submission Protection: Resolving an already-resolved item is rejected with 409 Conflict.
7. Concurrent Review Protection: Conflicting concurrent reviews safely resolve exactly once.
8. Unreviewed Safety Invariant: Candidate score alone never establishes confirmed identity.
"""

import os
import sys
import unittest
import tempfile
import sqlite3
import shutil
import json
import concurrent.futures
import numpy as np
import cv2
from fastapi.testclient import TestClient

# Ensure workspace packages are importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tt_dir = os.path.join(project_root, "TigerTrace_AI")
if tt_dir not in sys.path:
    sys.path.insert(0, tt_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.db.schema import init_db
from src.reid.stripe_matcher import StripeReIDMatcher
from src.reid.enrollment import TigerEnrollmentEngine
from ui.app import app, get_connection


class DeterministicStep14MockMatcher(StripeReIDMatcher):
    def __init__(self, score: float = 0.42, inliers: int = 6, cosine: float = 0.82):
        super().__init__(use_deep_embedding=False)
        self.mock_score = score
        self.mock_inliers = inliers
        self.mock_cosine = cosine

    def extract_deep_embedding(self, *args, **kwargs):
        return np.ones(128, dtype=np.float32)

    def compare_flanks(self, *args, **kwargs):
        return {
            "combined_score": self.mock_score,
            "sift_score": 0.45 if self.mock_inliers >= 4 else 0.0,
            "cosine_score": 0.90,
            "raw_cosine_similarity": self.mock_cosine,
            "good_matches_count": self.mock_inliers,
            "inlier_count": self.mock_inliers,
            "geometric_verification": "verified" if self.mock_inliers >= 4 else "insufficient_evidence",
            "flank_compatible": True,
        }

    def generate_sift_match_visualization(self, query_img_path, ref_img_path, output_path, **kwargs):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, np.zeros((60, 120, 3), dtype=np.uint8))
        return output_path


class TestStep14HumanInTheLoopReview(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "step14_review_test.db")
        init_db(self.test_db)

        # Override app's database connection
        app.dependency_overrides = {}
        self.orig_get_conn = get_connection
        self.conn = sqlite3.connect(self.test_db, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        import ui.app as app_module
        def _get_test_conn():
            c = sqlite3.connect(self.test_db, check_same_thread=False)
            c.row_factory = sqlite3.Row
            return c
        app_module.get_connection = _get_test_conn

        self.client = TestClient(app)

        # Create mock images
        self.query_img = os.path.join(self.temp_dir, "query_tiger.jpg")
        self.ref_img = os.path.join(self.temp_dir, "bajirao_ref.jpg")
        cv2.imwrite(self.query_img, np.zeros((100, 100, 3), dtype=np.uint8))
        cv2.imwrite(self.ref_img, np.zeros((100, 100, 3), dtype=np.uint8))

        # Enroll reference tiger
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, reference_crop_path, status)
        VALUES ('BAJIRAO', 'Bajirao', 'M', 'right', ?, 'resident');
        """, (self.ref_img,))
        self.conn.commit()

        # Engine with mock matcher
        self.matcher = DeterministicStep14MockMatcher(score=0.44, inliers=6, cosine=0.825)
        self.engine = TigerEnrollmentEngine(
            db_connection=self.conn,
            matcher=self.matcher,
            viz_dir=self.temp_dir,
            allow_auto_confirm=False,
        )

    def tearDown(self):
        self.conn.close()
        import ui.app as app_module
        app_module.get_connection = self.orig_get_conn
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_pending_review_item(self, flank_side="right"):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_crop_path, flank_side)
        VALUES ('probe.jpg', ?, 'PTR_STN_02', '2026-10-11 01:00:00', 'tiger', ?, ?);
        """, (self.query_img, self.query_img, flank_side))
        sighting_id = cur.lastrowid
        self.conn.commit()

        # Stage through enrollment engine (under Step 13 safety policy)
        res = self.engine.identify_and_enroll(
            query_crop_path=self.query_img,
            sighting_id=sighting_id,
            image_name="probe.jpg",
            flank_side=flank_side,
        )
        self.assertEqual(res["decision_state"], "review_required")

        cur.execute("SELECT review_id FROM review_queue WHERE sighting_id = ?;", (sighting_id,))
        review_id = cur.fetchone()["review_id"]
        return sighting_id, review_id

    # -------------------------------------------------------------------------
    # TEST 1: Queue item contains complete biometric evidence and uncalibrated warning
    # -------------------------------------------------------------------------
    def test_01_queue_item_contains_complete_evidence(self):
        sighting_id, review_id = self._create_pending_review_item(flank_side="right")

        resp = self.client.get("/api/review_queue")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertGreaterEqual(len(items), 1)

        item = next(it for it in items if it["review_id"] == review_id)
        self.assertEqual(item["sighting_id"], sighting_id)
        self.assertEqual(item["candidate_tiger_id"], "BAJIRAO")
        self.assertEqual(item["candidate_name"], "Bajirao")
        self.assertEqual(item["query_flank"], "right")
        self.assertEqual(item["ref_flank"], "right")
        self.assertEqual(item["sift_inliers"], 6)
        self.assertEqual(item["geometric_status"], "verified")
        self.assertAlmostEqual(item["raw_cosine_sim"], 0.825, places=3)
        self.assertIn("⚠️ CAUTION: Machine similarity scores are heuristic and uncalibrated", item["uncalibrated_warning"])
        self.assertTrue(item["submitted_image_url"].startswith("/api/image?path="))

    # -------------------------------------------------------------------------
    # TEST 2: Authorized reviewer accepts candidate
    # -------------------------------------------------------------------------
    def test_02_authorized_reviewer_accepts_candidate(self):
        sighting_id, review_id = self._create_pending_review_item()

        payload = {
            "action": "accept",
            "reviewer_id": "officer_sharma",
            "reason": "Verified right flank bifurcations match Bajirao catalogue reference",
            "tiger_id": "BAJIRAO"
        }
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "accept")
        self.assertEqual(res["assigned_tiger_id"], "BAJIRAO")

        # Verify sighting state
        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, review_status, match_method FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertEqual(s_row["tiger_id"], "BAJIRAO")
        self.assertEqual(s_row["review_status"], "confirmed")
        self.assertEqual(s_row["match_method"], "manual")

        # Verify review queue state
        cur.execute("SELECT status, decision, reviewer_id, reviewer_notes FROM review_queue WHERE review_id = ?;", (review_id,))
        rq_row = cur.fetchone()
        self.assertEqual(rq_row["status"], "accepted")
        self.assertEqual(rq_row["decision"], "accepted")
        self.assertEqual(rq_row["reviewer_id"], "officer_sharma")
        self.assertIn("Verified right flank", rq_row["reviewer_notes"])

        # Verify audit log entry
        cur.execute("SELECT * FROM review_audit_log WHERE review_id = ?;", (review_id,))
        audit_row = cur.fetchone()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["action"], "accept")
        self.assertEqual(audit_row["assigned_tiger_id"], "BAJIRAO")
        self.assertEqual(audit_row["reviewer_id"], "officer_sharma")
        self.assertEqual(audit_row["machine_suggested_id"], "BAJIRAO")

    # -------------------------------------------------------------------------
    # TEST 3: Authorized reviewer rejects candidate
    # -------------------------------------------------------------------------
    def test_03_authorized_reviewer_rejects_candidate(self):
        sighting_id, review_id = self._create_pending_review_item()

        payload = {
            "action": "reject",
            "reviewer_id": "officer_verma",
            "reason": "Distinct stripe spacing, impostor probe",
        }
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json=payload)
        self.assertEqual(resp.status_code, 200)

        # Verify sighting identity is cleared and marked rejected
        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertIsNone(s_row["tiger_id"])
        self.assertEqual(s_row["review_status"], "rejected")

        # Verify review queue item
        cur.execute("SELECT status, decision, reviewer_id FROM review_queue WHERE review_id = ?;", (review_id,))
        rq_row = cur.fetchone()
        self.assertEqual(rq_row["status"], "rejected")
        self.assertEqual(rq_row["reviewer_id"], "officer_verma")

    # -------------------------------------------------------------------------
    # TEST 4: Authorized reviewer marks observation inconclusive / unknown
    # -------------------------------------------------------------------------
    def test_04_authorized_reviewer_marks_inconclusive(self):
        sighting_id, review_id = self._create_pending_review_item()

        payload = {
            "action": "inconclusive",
            "reviewer_id": "officer_singh",
            "reason": "Severe motion blur and foliage occlusion",
        }
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json=payload)
        self.assertEqual(resp.status_code, 200)

        # Verify sighting identity is cleared and marked inconclusive
        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()
        self.assertIsNone(s_row["tiger_id"])
        self.assertEqual(s_row["review_status"], "inconclusive")

        cur.execute("SELECT status, decision FROM review_queue WHERE review_id = ?;", (review_id,))
        rq_row = cur.fetchone()
        self.assertEqual(rq_row["status"], "inconclusive")
        self.assertEqual(rq_row["decision"], "inconclusive")

    # -------------------------------------------------------------------------
    # TEST 5: Invalid review requests rejected
    # -------------------------------------------------------------------------
    def test_05_invalid_review_requests_rejected(self):
        sighting_id, review_id = self._create_pending_review_item()

        # Invalid action
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json={
            "action": "unsupported_action",
            "reviewer_id": "officer_sharma",
            "reason": "Valid reason"
        })
        self.assertEqual(resp.status_code, 400)

        # Empty reviewer ID
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json={
            "action": "accept",
            "reviewer_id": "   ",
            "reason": "Valid reason"
        })
        self.assertEqual(resp.status_code, 400)

        # Empty reason
        resp = self.client.post(f"/api/review_queue/{review_id}/action", json={
            "action": "accept",
            "reviewer_id": "officer_sharma",
            "reason": "   "
        })
        self.assertEqual(resp.status_code, 400)

        # Nonexistent review_id
        resp = self.client.post("/api/review_queue/999999/action", json={
            "action": "accept",
            "reviewer_id": "officer_sharma",
            "reason": "Valid reason"
        })
        self.assertEqual(resp.status_code, 404)

    # -------------------------------------------------------------------------
    # TEST 6: Repeated submission on resolved item rejected with 409 Conflict
    # -------------------------------------------------------------------------
    def test_06_repeated_submission_rejected_with_conflict_409(self):
        sighting_id, review_id = self._create_pending_review_item()

        # First decision succeeds
        resp1 = self.client.post(f"/api/review_queue/{review_id}/action", json={
            "action": "accept",
            "reviewer_id": "officer_sharma",
            "reason": "Accepted initial review",
            "tiger_id": "BAJIRAO"
        })
        self.assertEqual(resp1.status_code, 200)

        # Second decision on same item MUST fail with 409 Conflict
        resp2 = self.client.post(f"/api/review_queue/{review_id}/action", json={
            "action": "reject",
            "reviewer_id": "officer_verma",
            "reason": "Conflicting attempt to reject already-accepted review"
        })
        self.assertEqual(resp2.status_code, 409)
        self.assertIn("already been resolved", resp2.json()["detail"])

    # -------------------------------------------------------------------------
    # TEST 7: Concurrent conflicting review attempts handled safely
    # -------------------------------------------------------------------------
    def test_07_concurrent_conflicting_reviews_handled_safely(self):
        sighting_id, review_id = self._create_pending_review_item()

        actions = [
            {"action": "accept", "reviewer_id": "reviewer_A", "reason": "Officer A says Match", "tiger_id": "BAJIRAO"},
            {"action": "reject", "reviewer_id": "reviewer_B", "reason": "Officer B says Impostor"},
        ]

        results = []
        def send_action(payload):
            return self.client.post(f"/api/review_queue/{review_id}/action", json=payload)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(send_action, act) for act in actions]
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result().status_code)

        # Exactly one request must succeed (200), and the other must be rejected (409 Conflict)
        self.assertIn(200, results, "One review action must succeed")
        self.assertIn(409, results, "Conflicting review action must be rejected with 409 Conflict")

    # -------------------------------------------------------------------------
    # TEST 8: Unreviewed candidates never establish confirmed identity
    # -------------------------------------------------------------------------
    def test_08_unreviewed_candidates_never_silently_verified(self):
        sighting_id, review_id = self._create_pending_review_item()

        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, review_status FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        s_row = cur.fetchone()

        # Must NOT be confirmed
        self.assertNotEqual(s_row["review_status"], "confirmed")
        self.assertEqual(s_row["review_status"], "pending_review")

        # Must appear in pending review queue
        cur.execute("SELECT status FROM review_queue WHERE review_id = ?;", (review_id,))
        self.assertEqual(cur.fetchone()["status"], "pending")


if __name__ == "__main__":
    unittest.main()
