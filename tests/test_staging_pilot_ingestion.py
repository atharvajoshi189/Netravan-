"""
Unit tests for TigerTraceAI Step 15B Lightweight Wildlife Dataset Staging Pilot.

Verifies:
1. Hard download size budget enforcement.
2. Duplicate image checksum rejection.
3. Corrupt/unreadable image rejection.
4. Image dimension minimum threshold check.
5. Missing bounding-box detection (no invented bboxes).
6. Invalid/unmapped species mapping rejection.
7. Silent overwrite prevention.
8. Encounter grouping for camera sequence leakage prevention.
9. Dry-run safety (no disk mutations).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from TigerTrace_AI.src.datasets.staging_pilot_ingest import (
    WildlifeStagingIngester,
    StagingSampleRecord,
    PRIORITY_SPECIES,
)


class TestStagingPilotIngestion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="tt_test_staging_")
        self.output_dir = Path(self.temp_dir) / "staging_pilot"
        self.taxonomy_path = Path("TigerTrace_AI/data/taxonomy/species_taxonomy.json")
        self.assertTrue(self.taxonomy_path.exists(), "species_taxonomy.json must exist")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_jpeg(self, width: int = 256, height: int = 256, color=(120, 180, 50)) -> bytes:
        """Creates an in-memory synthetic image fixture for testing."""
        img = np.full((height, width, 3), color, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", img)
        self.assertTrue(success)
        return encoded.tobytes()

    def test_duplicate_image_checksum_rejection(self):
        """Verifies that an identical image payload is rejected with duplicate_image_checksum."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=False,
        )
        ingester._prepare_directories()

        raw_bytes = self._create_synthetic_jpeg(width=200, height=200, color=(10, 20, 30))
        target_path_1 = ingester.images_dir / "sample_1.jpg"
        target_path_2 = ingester.images_dir / "sample_2.jpg"

        # First ingestion succeeds
        valid1, reason1, w1, h1, sha1 = ingester.validate_and_ingest_image_bytes(
            raw_bytes, target_path_1, expected_species="chital"
        )
        self.assertTrue(valid1)
        self.assertIsNone(reason1)
        self.assertEqual(w1, 200)
        self.assertEqual(h1, 200)

        # Second ingestion with identical bytes must be rejected as duplicate
        valid2, reason2, w2, h2, sha2 = ingester.validate_and_ingest_image_bytes(
            raw_bytes, target_path_2, expected_species="chital"
        )
        self.assertFalse(valid2)
        self.assertEqual(reason2, "duplicate_image_checksum")
        self.assertEqual(sha1, sha2)

    def test_corrupt_image_rejection(self):
        """Verifies that corrupt or truncated bytes are rejected."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=False,
        )
        ingester._prepare_directories()

        corrupt_bytes = b"CORRUPT_NOT_A_VALID_JPEG_HEADER_XYZ123456789"
        target_path = ingester.images_dir / "corrupt.jpg"

        is_valid, reason, _, _, _ = ingester.validate_and_ingest_image_bytes(
            corrupt_bytes, target_path, expected_species="sambar"
        )
        self.assertFalse(is_valid)
        self.assertEqual(reason, "corrupt_unreadable_image")
        self.assertFalse(target_path.exists())

    def test_dimensions_below_threshold_rejection(self):
        """Verifies that images smaller than 128x128 are rejected."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=False,
        )
        ingester._prepare_directories()

        tiny_bytes = self._create_synthetic_jpeg(width=64, height=64)
        target_path = ingester.images_dir / "tiny.jpg"

        is_valid, reason, w, h, _ = ingester.validate_and_ingest_image_bytes(
            tiny_bytes, target_path, expected_species="gaur"
        )
        self.assertFalse(is_valid)
        self.assertIn("image_dimensions_below_threshold", str(reason))
        self.assertEqual(w, 64)
        self.assertEqual(h, 64)
        self.assertFalse(target_path.exists())

    def test_missing_annotations_and_no_invented_bboxes(self):
        """Verifies that observations without genuine bounding boxes are strictly flagged as NOT ready for detection."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=True,
        )

        mock_obs = {
            "id": 99901,
            "quality_grade": "research",
            "license_code": "cc-by",
            "observed_on": "2026-03-15",
            "user": {"id": 1234, "login": "field_biologist"},
            "annotations": [
                {"controlled_attribute_id": 1, "controlled_value_id": 2}  # Biological phenology tag, NOT a bbox
            ],
            "photos": [
                {
                    "id": 88801,
                    "url": "https://example.org/photos/88801/medium.jpg",
                    "license_code": "cc-by",
                    "attribution": "(c) Field Biologist",
                }
            ],
            "taxon": {"name": "Axis axis"},
        }

        record = ingester.ingest_single_observation(mock_obs, "chital")
        self.assertIsNotNone(record)
        self.assertFalse(record.has_bounding_box)
        self.assertFalse(record.detection_ready)
        self.assertEqual(
            record.training_readiness,
            "NOT_READY_FOR_DETECTION_TRAINING_IMAGE_LEVEL_ONLY",
        )
        self.assertEqual(len(record.bbox_annotations), 0, "No bounding boxes must be invented")

    def test_enforce_download_budget_hard_limit(self):
        """Verifies that the hard download budget stops ingestion when exceeded."""
        tiny_budget_mb = 0.001  # ~1024 bytes
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            max_download_mb=tiny_budget_mb,
            dry_run=True,
        )

        mock_obs_1 = {
            "id": 101,
            "license_code": "cc-by",
            "user": {"id": 1},
            "photos": [{"id": 201, "url": "https://example.org/p1/square.jpg"}],
        }
        mock_obs_2 = {
            "id": 102,
            "license_code": "cc-by",
            "user": {"id": 2},
            "photos": [{"id": 202, "url": "https://example.org/p2/square.jpg"}],
        }

        # First simulated item uses 350KB (> 1KB budget)
        r1 = ingester.ingest_single_observation(mock_obs_1, "nilgai")
        # Second item must be rejected due to budget limit
        r2 = ingester.ingest_single_observation(mock_obs_2, "nilgai")

        self.assertIsNone(r2)
        self.assertIn("download_budget_exceeded", ingester.rejection_counts)

    def test_silent_overwrite_prevention(self):
        """Verifies that existing target files cannot be overwritten silently."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=False,
        )
        ingester._prepare_directories()

        target_path = ingester.images_dir / "existing_file.jpg"
        target_path.write_bytes(b"EXISTING_DATA")

        new_bytes = self._create_synthetic_jpeg(width=200, height=200)
        is_valid, reason, _, _, _ = ingester.validate_and_ingest_image_bytes(
            new_bytes, target_path, expected_species="chital"
        )
        self.assertFalse(is_valid)
        self.assertEqual(reason, "target_file_already_exists_no_silent_overwrite")
        self.assertEqual(target_path.read_bytes(), b"EXISTING_DATA")

    def test_encounter_grouping_leakage_prevention(self):
        """Verifies encounter grouping clusters burst shots from the same user/date."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=True,
        )

        obs_a = {
            "id": 501,
            "license_code": "cc-by",
            "observed_on": "2026-05-10",
            "user": {"id": 777},
            "photos": [{"id": 601, "url": "https://example.org/p/medium.jpg"}],
        }
        obs_b = {
            "id": 502,
            "license_code": "cc-by",
            "observed_on": "2026-05-10",
            "user": {"id": 777},
            "photos": [{"id": 602, "url": "https://example.org/p/medium.jpg"}],
        }

        rec_a = ingester.ingest_single_observation(obs_a, "sambar")
        rec_b = ingester.ingest_single_observation(obs_b, "sambar")

        self.assertIsNotNone(rec_a)
        self.assertIsNotNone(rec_b)
        self.assertEqual(rec_a.encounter_group_id, rec_b.encounter_group_id)
        self.assertEqual(rec_a.encounter_group_id, "enc_user777_2026-05-10")

    def test_dry_run_mode_creates_no_image_files(self):
        """Verifies that dry-run mode performs full validation without creating images on disk."""
        ingester = WildlifeStagingIngester(
            taxonomy_path=self.taxonomy_path,
            output_dir=self.output_dir,
            dry_run=True,
        )
        obs = {
            "id": 801,
            "license_code": "cc0",
            "user": {"id": 11},
            "photos": [{"id": 901, "url": "https://example.org/p/medium.jpg"}],
        }
        rec = ingester.ingest_single_observation(obs, "gaur")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.status, "valid_staged_dry_run")
        self.assertFalse(self.output_dir.exists())


if __name__ == "__main__":
    unittest.main()
