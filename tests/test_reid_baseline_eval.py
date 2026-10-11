"""
tests/test_reid_baseline_eval.py

Standard library unittest test suite for the reproducible Step 10 baseline Re-ID evaluation harness.
Verifies that:
1. Baseline evaluation JSON artifact exists and contains valid schema keys.
2. Dataset counts match the approved ATRW pilot manifest (13 crops, 4 identities).
3. All 78 pairwise comparisons are partitioned correctly across genuine, burst, impostor, and cross-flank sets.
4. Burst tracklet inflation is detected and quantified.
5. Biological cross-flank guard enforcement achieves 100% rejection.
6. Unknown individual rejection metrics are correctly calculated.
"""

import os
import sys
import json
import unittest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.evaluate_reid_baseline import run_reid_evaluation


class TestBaselineReIDEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output_path = os.path.join(REPO_ROOT, "data", "staging", "atrw_pilot", "baseline_reid_evaluation.json")
        if not os.path.exists(cls.output_path):
            cls.report = run_reid_evaluation(output_json_path=cls.output_path)
        else:
            with open(cls.output_path, "r", encoding="utf-8") as f:
                cls.report = json.load(f)

    def test_baseline_eval_schema(self):
        """Verify that all core schema keys exist in the evaluation report."""
        report = self.report
        self.assertIn("evaluation_name", report)
        self.assertIn("timestamp_utc", report)
        self.assertIn("model_architecture", report)
        self.assertIn("dataset", report)
        self.assertIn("pairwise_verification", report)
        self.assertIn("identification_retrieval", report)
        self.assertIn("unknown_individual_rejection", report)
        self.assertIn("cross_flank_guard_validation", report)
        self.assertIn("key_limitations", report)

    def test_dataset_counts(self):
        """Verify dataset counts align with approved ATRW pilot manifest."""
        ds = self.report["dataset"]
        self.assertEqual(ds["approved_images_count"], 13)
        self.assertEqual(ds["approved_identities_count"], 4)
        self.assertEqual(set(ds["identities"]), {"tiger_001", "tiger_002", "tiger_003", "tiger_005"})

    def test_pairwise_partitions(self):
        """Verify all 78 pairwise comparisons are partitioned correctly."""
        pv = self.report["pairwise_verification"]
        self.assertEqual(pv["total_pairs_evaluated"], 78)

        partitions = pv["partitions"]
        self.assertIn("genuine_cross_encounter", partitions)
        self.assertIn("genuine_burst", partitions)
        self.assertIn("impostor_same_flank", partitions)
        self.assertIn("cross_flank_incompatible", partitions)

        # 12 cross-encounter + 4 burst + 20 impostor + 42 cross-flank = 78
        self.assertEqual(partitions["genuine_cross_encounter"]["count"], 12)
        self.assertEqual(partitions["genuine_burst"]["count"], 4)
        self.assertEqual(partitions["impostor_same_flank"]["count"], 20)
        self.assertEqual(partitions["cross_flank_incompatible"]["count"], 42)

    def test_burst_inflation_detected(self):
        """Verify that burst tracklet correlation inflates similarity scores."""
        pv = self.report["pairwise_verification"]
        sep = pv["separation_metrics"]

        # Burst genuine mean should be significantly higher than cross-encounter genuine mean
        mu_burst = pv["partitions"]["genuine_burst"]["combined_score"]["mean"]
        mu_cross = pv["partitions"]["genuine_cross_encounter"]["combined_score"]["mean"]
        self.assertGreater(mu_burst, 0.90)
        self.assertLess(mu_cross, 0.60)
        self.assertGreater(sep["burst_inflation_effect"], 0.40)

    def test_cross_flank_guard_enforced(self):
        """Verify that the Step 9A biological flank guard achieves 100% rejection."""
        cfg = self.report["cross_flank_guard_validation"]
        self.assertEqual(cfg["guard_enforcement_rate_pct"], 100.0)
        self.assertEqual(cfg["verdict"], "PASS")

        # Also check the 42 cross-flank pairwise comparisons
        cf_part = self.report["pairwise_verification"]["partitions"]["cross_flank_incompatible"]
        self.assertEqual(cf_part["combined_score"]["max"], 0.0)
        self.assertEqual(cf_part["decision_bands"]["pct_new_identity_candidate"], 100.0)

    def test_unknown_rejection_metrics(self):
        """Verify that open-set rejection metrics are measured on unenrolled tiger_004."""
        uir = self.report["unknown_individual_rejection"]
        self.assertEqual(uir["unenrolled_identity"], "tiger_004")
        self.assertEqual(uir["probe_count"], 3)
        self.assertEqual(len(uir["details"]), 3)


if __name__ == "__main__":
    unittest.main()
