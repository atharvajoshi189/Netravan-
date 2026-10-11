"""
Unit tests for TigerTraceAI Step 15C: Assisted Annotation & Gold-Standard Dataset Preparation.

Tests:
1. MegaDetector availability audit & blocker reporting.
2. Coordinate normalization, clamping, and pixel conversion.
3. Degenerate and out-of-bounds box rejection.
4. Unknown / uncertain label handling (excluded from training).
5. Multiple animal bounding boxes per image.
6. Rejected proposal handling.
7. Unreviewed annotations strictly excluded from YOLO export.
8. Encounter-grouped leakage-safe splitting.
9. Export manifest warning for small pilot size.
10. CVAT XML format export validity.
"""

import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

from TigerTrace_AI.src.datasets.assisted_annotation import (
    AssistedAnnotationEngine,
    BBoxProposal,
)
from TigerTrace_AI.src.datasets.cvat_exporter import CVATProjectExporter
from TigerTrace_AI.src.datasets.gold_standard_builder import (
    GoldStandardBuilder,
    CANONICAL_SPECIES_IDS,
)


class TestStep15CAssistedAnnotationAndGoldStandard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="tt_test_15c_")
        self.staging_dir = Path(self.temp_dir) / "staging"
        self.images_dir = self.staging_dir / "images"
        self.manifests_dir = self.staging_dir / "manifests"
        self.proposals_dir = self.staging_dir / "provisional_proposals"
        self.yolo_dir = self.staging_dir / "yolo_gold_standard"

        self.images_dir.mkdir(parents=True)
        self.manifests_dir.mkdir(parents=True)
        self.proposals_dir.mkdir(parents=True)

        # Create 2 synthetic test images
        self._create_synthetic_image("test_sample_01.jpg", 400, 300)
        self._create_synthetic_image("test_sample_02.jpg", 600, 450)

        # Create synthetic staging manifest
        manifest_data = {
            "manifest_version": "1.0.0",
            "samples": [
                {
                    "sample_id": "test_sample_01",
                    "canonical_class_name": "chital",
                    "canonical_class_id": 3,
                    "scientific_name": "Axis axis",
                    "license_code": "cc-by",
                    "attribution": "(c) Field Biologist A",
                    "encounter_group_id": "enc_user01_2026-10-01",
                    "width_px": 400,
                    "height_px": 300,
                },
                {
                    "sample_id": "test_sample_02",
                    "canonical_class_name": "sambar",
                    "canonical_class_id": 1,
                    "scientific_name": "Rusa unicolor",
                    "license_code": "cc-by-nc",
                    "attribution": "(c) Field Biologist B",
                    "encounter_group_id": "enc_user02_2026-10-02",
                    "width_px": 600,
                    "height_px": 450,
                },
            ],
        }
        with open(self.manifests_dir / "staging_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        # Create synthetic provisional proposals
        proposals_data = {
            "proposals": [
                {
                    "proposal_id": "prop_0001",
                    "sample_id": "test_sample_01",
                    "image_file": "test_sample_01.jpg",
                    "bbox_norm_xywh": [0.5, 0.5, 0.4, 0.4],
                    "bbox_pixel_xyxy": [120, 90, 280, 210],
                    "proposal_source": "yolov8n_coco_quadruped",
                    "detector_label": "cow",
                    "detector_confidence": 0.85,
                    "review_status": "provisional_unreviewed",
                }
            ]
        }
        with open(self.proposals_dir / "provisional_proposals.json", "w", encoding="utf-8") as f:
            json.dump(proposals_data, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_image(self, filename: str, w: int, h: int):
        img = np.full((h, w, 3), (100, 150, 80), dtype=np.uint8)
        cv2.imwrite(str(self.images_dir / filename), img)

    def test_megadetector_availability_audit(self):
        """Verifies MegaDetector audit reports checkpoint blocker and instructions when missing."""
        engine = AssistedAnnotationEngine(staging_dir=self.staging_dir)
        report = engine.check_megadetector_availability()

        self.assertFalse(report.checkpoint_found)
        self.assertIsNotNone(report.blocker_reason)
        self.assertIn("MegaDetector v5a", report.blocker_reason)
        self.assertGreater(len(report.setup_instructions), 0)
        self.assertEqual(report.fallback_used, "yolov8n_coco_quadruped_detector")

    def test_coordinate_validation_and_clamping(self):
        """Verifies coordinate validation clamps boundary rounding errors and maps to pixels."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir)
        # Slightly over 1.0 boundary (rounding error)
        raw_box = [0.5, 0.5, 1.004, 1.003]
        valid, err, clamped, pixels = builder.validate_bbox_coordinates(raw_box, img_w=400, img_h=300)

        self.assertTrue(valid)
        self.assertIsNone(err)
        # Clamped values must not exceed 1.0
        self.assertLessEqual(clamped[0] + clamped[2] / 2, 1.0001)
        self.assertEqual(pixels, [0, 0, 400, 300])

    def test_invalid_and_degenerate_boxes_rejection(self):
        """Verifies rejection of non-positive dimensions and extreme out-of-bounds coordinates."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir)

        # Zero width
        valid1, err1, _, _ = builder.validate_bbox_coordinates([0.5, 0.5, 0.0, 0.4], 400, 300)
        self.assertFalse(valid1)
        self.assertIn("degenerate_box", err1)

        # Substantially out of bounds
        valid2, err2, _, _ = builder.validate_bbox_coordinates([1.8, 0.5, 0.4, 0.4], 400, 300)
        self.assertFalse(valid2)
        self.assertIn("out_of_bounds", err2)

    def test_unknown_uncertain_label_handling(self):
        """Verifies that unknown/uncertain boxes receive class ID -1 and are excluded from YOLO export."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)

        # Record human review marking sample 01 as unknown_uncertain
        success, err = builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="expert_reviewer_1",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "unknown_uncertain",
                    "bbox_norm_xywh": [0.5, 0.5, 0.3, 0.3],
                    "review_action": "unknown_uncertain",
                }
            ],
            notes="Animal obscured by thick bamboo brush",
        )
        self.assertTrue(success)
        rec = builder.reviews["test_sample_01"]
        self.assertEqual(rec.boxes[0].canonical_class_id, -1)

        # Export YOLO dataset
        summary = builder.export_yolo_detection_ready_dataset()
        # Since the only box has class_id -1, it must be excluded from training label files
        self.assertEqual(summary["total_boxes"], 0)

    def test_multiple_boxes_per_image(self):
        """Verifies handling of multiple animals in a single image."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)

        success, err = builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="expert_reviewer_1",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.3, 0.4, 0.2, 0.25],
                    "review_action": "accepted_proposal",
                },
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.7, 0.6, 0.25, 0.3],
                    "review_action": "manual_box",
                },
            ],
            notes="Two chital feeding in open grassland",
        )
        self.assertTrue(success)
        rec = builder.reviews["test_sample_01"]
        self.assertEqual(len(rec.boxes), 2)
        self.assertEqual(rec.boxes[0].canonical_class_id, CANONICAL_SPECIES_IDS["chital"])
        self.assertEqual(rec.boxes[1].canonical_class_id, CANONICAL_SPECIES_IDS["chital"])

        summary = builder.export_yolo_detection_ready_dataset()
        self.assertEqual(summary["total_boxes"], 2)

    def test_rejected_proposal_action(self):
        """Verifies that an explicitly rejected proposal is not added to valid detection boxes."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir)

        success, err = builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="expert_reviewer_1",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.5, 0.5, 0.4, 0.4],
                    "review_action": "rejected_proposal",
                    "source_proposal_id": "prop_0001",
                }
            ],
            notes="False alarm: rock silhouette",
        )
        self.assertTrue(success)
        rec = builder.reviews["test_sample_01"]
        self.assertEqual(len(rec.boxes), 0)
        self.assertEqual(rec.status, "rejected_no_valid_boxes")

    def test_unreviewed_annotations_not_exported(self):
        """Verifies that unreviewed samples are strictly omitted from the YOLO dataset."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)
        # Review sample 01, leave sample 02 completely unreviewed
        builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="reviewer_a",
            review_decision="human_verified",
            boxes=[
                {
                    "species_label": "chital",
                    "bbox_norm_xywh": [0.5, 0.5, 0.3, 0.3],
                    "review_action": "accepted_proposal",
                }
            ],
        )

        summary = builder.export_yolo_detection_ready_dataset()
        self.assertEqual(summary["total_verified_images"], 1)
        exported_ids = [s["sample_id"] for s in summary["samples"]]
        self.assertIn("test_sample_01", exported_ids)
        self.assertNotIn("test_sample_02", exported_ids, "Unreviewed sample 02 must not be exported")

    def test_encounter_grouped_leakage_safe_split(self):
        """Verifies burst photos from the same encounter stay in the same split."""
        # Add another sample sharing encounter_group_id with sample 01
        manifest_path = self.manifests_dir / "staging_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["samples"].append({
            "sample_id": "test_sample_01_burst2",
            "canonical_class_name": "chital",
            "canonical_class_id": 3,
            "scientific_name": "Axis axis",
            "encounter_group_id": "enc_user01_2026-10-01",  # Same group as sample 01
            "width_px": 400,
            "height_px": 300,
        })
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self._create_synthetic_image("test_sample_01_burst2.jpg", 400, 300)

        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)
        builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="rev",
            review_decision="human_verified",
            boxes=[{"species_label": "chital", "bbox_norm_xywh": [0.5, 0.5, 0.3, 0.3]}],
        )
        builder.record_human_review(
            sample_id="test_sample_01_burst2",
            reviewer_id="rev",
            review_decision="human_verified",
            boxes=[{"species_label": "chital", "bbox_norm_xywh": [0.5, 0.5, 0.3, 0.3]}],
        )

        summary = builder.export_yolo_detection_ready_dataset()
        samples_by_id = {s["sample_id"]: s["split"] for s in summary["samples"]}
        self.assertEqual(
            samples_by_id["test_sample_01"],
            samples_by_id["test_sample_01_burst2"],
            "Burst photos sharing encounter_group_id must belong to the exact same split"
        )

    def test_pilot_too_small_warning_flag(self):
        """Verifies export manifest explicitly flags small pilot size as unsuitable for reliable training."""
        builder = GoldStandardBuilder(staging_dir=self.staging_dir, output_dir=self.yolo_dir)
        builder.record_human_review(
            sample_id="test_sample_01",
            reviewer_id="rev",
            review_decision="human_verified",
            boxes=[{"species_label": "chital", "bbox_norm_xywh": [0.5, 0.5, 0.3, 0.3]}],
        )
        summary = builder.export_yolo_detection_ready_dataset()

        self.assertTrue(summary["is_too_small_for_reliable_training"])
        self.assertIn("INSUFFICIENT for training", summary["warning"])

    def test_cvat_xml_generation(self):
        """Verifies CVAT XML exporter generates valid XML conforming to CVAT for Images 1.1."""
        exporter = CVATProjectExporter(staging_dir=self.staging_dir)
        xml_path = exporter.export()

        self.assertTrue(xml_path.exists())
        # Parse XML to verify well-formedness
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
        self.assertEqual(root.tag, "annotations")
        self.assertEqual(root.find("version").text, "1.1")

        labels = [l.find("name").text for l in root.findall(".//label")]
        self.assertIn("chital", labels)
        self.assertIn("sambar", labels)
        self.assertIn("gaur", labels)
        self.assertIn("nilgai", labels)
        self.assertIn("unknown_uncertain", labels)


if __name__ == "__main__":
    unittest.main()
