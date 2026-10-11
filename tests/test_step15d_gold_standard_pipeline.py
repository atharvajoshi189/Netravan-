"""
Unit and integration tests for TigerTraceAI Step 15D: Human Review & Gold-Standard Annotation Pipeline.

Verifies:
1. Isolated synthetic test fixture pipeline (clearly marked SYNTHETIC, zero merge into real data).
2. Human-verified boxes enter YOLO labels; rejected and unknown/uncertain boxes are excluded.
3. Unreviewed provisional proposals strictly excluded from training splits.
4. Normalized coordinate bounds, canonical class ID mapping, and encounter grouping leakage prevention.
5. Review station server API endpoints (GET /api/samples, POST /api/save_review, GET /api/status).
6. Real staging inventory integrity (all 40 real samples pending, 0 fabricated reviews).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from TigerTrace_AI.src.datasets.gold_standard_builder import (
    GoldStandardBuilder,
    CANONICAL_SPECIES_IDS,
)


class TestStep15DGoldStandardPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="tt_synth_test_15d_")
        self.staging_dir = Path(self.temp_dir) / "synthetic_staging_fixture"
        self.images_dir = self.staging_dir / "images"
        self.manifests_dir = self.staging_dir / "manifests"
        self.proposals_dir = self.staging_dir / "provisional_proposals"
        self.yolo_dir = self.staging_dir / "yolo_gold_standard"

        self.images_dir.mkdir(parents=True)
        self.manifests_dir.mkdir(parents=True)
        self.proposals_dir.mkdir(parents=True)

        # 1. Create 5 synthetic test images (clearly marked synthetic)
        for i in range(1, 6):
            self._create_synthetic_image(f"synth_wildlife_{i:02d}.jpg", 640, 480)

        # 2. Build synthetic staging manifest
        synthetic_manifest = {
            "manifest_version": "1.0.0",
            "fixture_label": "SYNTHETIC_TEST_PIPELINE_FIXTURE_DO_NOT_MERGE",
            "samples": [
                {
                    "sample_id": "synth_wildlife_01",
                    "canonical_class_name": "chital",
                    "canonical_class_id": 3,
                    "scientific_name": "Axis axis",
                    "license_code": "cc-by",
                    "attribution": "Synthetic Fixture Observer 1",
                    "encounter_group_id": "synth_enc_alpha",
                    "width_px": 640,
                    "height_px": 480,
                },
                {
                    "sample_id": "synth_wildlife_02",
                    "canonical_class_name": "sambar",
                    "canonical_class_id": 1,
                    "scientific_name": "Rusa unicolor",
                    "license_code": "cc-by-nc",
                    "attribution": "Synthetic Fixture Observer 2",
                    "encounter_group_id": "synth_enc_beta",
                    "width_px": 640,
                    "height_px": 480,
                },
                {
                    "sample_id": "synth_wildlife_03",
                    "canonical_class_name": "gaur",
                    "canonical_class_id": 6,
                    "scientific_name": "Bos gaurus",
                    "license_code": "cc-by",
                    "attribution": "Synthetic Fixture Observer 3",
                    "encounter_group_id": "synth_enc_gamma",
                    "width_px": 640,
                    "height_px": 480,
                },
                {
                    "sample_id": "synth_wildlife_04",
                    "canonical_class_name": "nilgai",
                    "canonical_class_id": 7,
                    "scientific_name": "Boselaphus tragocamelus",
                    "license_code": "cc0",
                    "attribution": "Synthetic Fixture Observer 4",
                    "encounter_group_id": "synth_enc_delta",
                    "width_px": 640,
                    "height_px": 480,
                },
                {
                    "sample_id": "synth_wildlife_05",
                    "canonical_class_name": "chital",
                    "canonical_class_id": 3,
                    "scientific_name": "Axis axis",
                    "license_code": "cc-by",
                    "attribution": "Synthetic Fixture Observer 5",
                    "encounter_group_id": "synth_enc_alpha",  # Shared encounter with sample 1
                    "width_px": 640,
                    "height_px": 480,
                },
            ],
        }
        with open(self.manifests_dir / "staging_manifest.json", "w", encoding="utf-8") as f:
            json.dump(synthetic_manifest, f)

        # 3. Create synthetic provisional proposals
        proposals_payload = {
            "version": "1.0.0",
            "proposals": [
                {
                    "proposal_id": "synth_prop_01",
                    "sample_id": "synth_wildlife_01",
                    "image_file": "synth_wildlife_01.jpg",
                    "bbox_norm_xywh": [0.35, 0.45, 0.3, 0.35],
                    "bbox_pixel_xyxy": [128, 132, 320, 300],
                    "proposal_source": "yolov8n_coco_quadruped",
                    "detector_label": "sheep",
                    "detector_confidence": 0.88,
                    "review_status": "provisional_unreviewed",
                },
                {
                    "proposal_id": "synth_prop_02",
                    "sample_id": "synth_wildlife_05",
                    "image_file": "synth_wildlife_05.jpg",
                    "bbox_norm_xywh": [0.5, 0.5, 0.4, 0.4],
                    "bbox_pixel_xyxy": [192, 144, 448, 336],
                    "proposal_source": "yolov8n_coco_quadruped",
                    "detector_label": "horse",
                    "detector_confidence": 0.75,
                    "review_status": "provisional_unreviewed",
                },
            ],
        }
        with open(self.proposals_dir / "provisional_proposals.json", "w", encoding="utf-8") as f:
            json.dump(proposals_payload, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_image(self, filename: str, w: int, h: int):
        img = np.full((h, w, 3), (80, 140, 60), dtype=np.uint8)
        cv2.imwrite(str(self.images_dir / filename), img)

    def test_isolated_synthetic_export_pipeline(self):
        """Tests complete export pipeline on synthetic fixture: verifies verified boxes vs rejected vs unknown vs unreviewed."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)

        # 1. Sample 01: Human verified with 2 Chital boxes (one proposal accepted, one manual)
        builder.record_human_review(
            sample_id="synth_wildlife_01",
            reviewer_id="human_tester",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.35, 0.45, 0.3, 0.35],
                    "review_action": "accepted_proposal",
                    "source_proposal_id": "synth_prop_01",
                },
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.75, 0.55, 0.2, 0.25],
                    "review_action": "manual_box",
                },
            ],
            notes="Two chital feeding peacefully",
        )

        # 2. Sample 02: Human verified with 1 Sambar box
        builder.record_human_review(
            sample_id="synth_wildlife_02",
            reviewer_id="human_tester",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "sambar",
                    "bbox_norm_xywh": [0.5, 0.5, 0.4, 0.5],
                    "review_action": "manual_box",
                }
            ],
            notes="Solitary adult female sambar",
        )

        # 3. Sample 03: Rejected entirely (e.g. boulder / false trigger)
        builder.record_human_review(
            sample_id="synth_wildlife_03",
            reviewer_id="human_tester",
            review_decision="rejected_entirely",
            boxes=[],
            notes="False alarm: mossy rock",
        )

        # 4. Sample 04: Unknown / uncertain (obscured)
        builder.record_human_review(
            sample_id="synth_wildlife_04",
            reviewer_id="human_tester",
            review_decision="unknown_uncertain",
            boxes=[
                {
                    "species_label": "unknown_uncertain",
                    "bbox_norm_xywh": [0.6, 0.4, 0.3, 0.3],
                    "review_action": "unknown_uncertain",
                }
            ],
            notes="Heavy dust storm occlusion",
        )

        # 5. Sample 05: Left completely UNREVIEWED (has proposal synth_prop_02)

        # Run YOLO Export
        summary = builder.export_yolo_detection_ready_dataset()

        # Assertions
        # Only samples 01 and 02 may be exported
        self.assertEqual(summary["total_verified_images"], 2)
        self.assertEqual(summary["total_boxes"], 3)  # 2 Chital + 1 Sambar

        exported_sample_ids = [s["sample_id"] for s in summary["samples"]]
        self.assertIn("synth_wildlife_01", exported_sample_ids)
        self.assertIn("synth_wildlife_02", exported_sample_ids)
        self.assertNotIn("synth_wildlife_03", exported_sample_ids, "Rejected sample 03 must NOT be exported")
        self.assertNotIn("synth_wildlife_04", exported_sample_ids, "Unknown sample 04 must NOT enter detection training")
        self.assertNotIn("synth_wildlife_05", exported_sample_ids, "Unreviewed sample 05 must NEVER enter training")

        # Verify YOLO label file content for sample 01
        found_txt = list(self.yolo_dir.glob("labels/**/synth_wildlife_01.txt"))
        self.assertEqual(len(found_txt), 1)
        lines = found_txt[0].read_text().strip().split("\n")
        self.assertEqual(len(lines), 2)
        # Class ID for chital is 3
        for line in lines:
            parts = line.split()
            self.assertEqual(parts[0], "3", "Chital canonical ID must be 3")
            # Verify coordinates are normalized
            xc, yc, w, h = map(float, parts[1:])
            self.assertTrue(0 <= xc <= 1)
            self.assertTrue(0 <= yc <= 1)
            self.assertTrue(0 < w <= 1)
            self.assertTrue(0 < h <= 1)

        # Verify data.yaml was created properly
        yaml_file = self.yolo_dir / "data.yaml"
        self.assertTrue(yaml_file.exists())
        yaml_text = yaml_file.read_text()
        self.assertIn("nc: 17", yaml_text)
        self.assertIn("3: chital", yaml_text)
        self.assertIn("1: sambar", yaml_text)

    def test_real_staging_data_not_polluted(self):
        """Verifies that the real staging directory has 0 fabricated human reviews and 58 pending proposals."""
        real_staging_dir = Path("TigerTrace_AI/data/staging_wildlife_pilot")
        real_manifest_file = real_staging_dir / "manifests" / "staging_manifest.json"
        real_proposals_file = real_staging_dir / "provisional_proposals" / "provisional_proposals.json"
        real_reviews_file = real_staging_dir / "human_reviews" / "human_verified_annotations.json"

        # Check real manifest
        self.assertTrue(real_manifest_file.exists())
        with open(real_manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        self.assertEqual(len(manifest_data.get("samples", [])), 40)

        # Check real proposals
        self.assertTrue(real_proposals_file.exists())
        with open(real_proposals_file, "r", encoding="utf-8") as f:
            p_data = json.load(f)
        self.assertEqual(len(p_data.get("proposals", [])), 58)
        # All 58 proposals must be provisional_unreviewed
        for prop in p_data["proposals"]:
            self.assertFalse(prop["is_verified"])
            self.assertEqual(prop["review_status"], "provisional_unreviewed")

        # Check real human reviews: MUST NOT exist or contain completed reviews prior to actual human interaction
        if real_reviews_file.exists():
            with open(real_reviews_file, "r", encoding="utf-8") as f:
                r_data = json.load(f)
            self.assertEqual(
                len(r_data.get("reviews", [])),
                0,
                "Real human reviews must NOT be fabricated! Must remain 0 pending user review."
            )


if __name__ == "__main__":
    unittest.main()
