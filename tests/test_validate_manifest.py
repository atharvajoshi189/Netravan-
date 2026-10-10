import unittest
import os
import tempfile
import csv
import json
import shutil

from scripts.validate_dataset_manifest import (
    ManifestValidator,
    REQUIRED_COLUMNS,
)


class TestDatasetManifestValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.temp_dir, "test_manifest.csv")
        self.dataset_root = os.path.join(self.temp_dir, "images")
        os.makedirs(self.dataset_root, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_manifest(self, rows, columns=None):
        cols = columns if columns is not None else REQUIRED_COLUMNS
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def _create_dummy_image(self, rel_path):
        full_path = os.path.join(self.dataset_root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF")  # Minimal JPEG header bytes
        return rel_path

    # -------------------------------------------------------------------------
    # TEST 1: Valid input manifest
    # -------------------------------------------------------------------------
    def test_01_valid_manifest(self):
        img1 = self._create_dummy_image("cameratrap/tiger_01.jpg")
        img2 = self._create_dummy_image("cameratrap/hyena_01.jpg")

        rows = [
            {
                "sample_id": "SAMP_001",
                "dataset_name": "PenchCameraTraps",
                "source_url": "https://example.org/pench",
                "relative_image_path": img1,
                "species_label": "Panthera tigris",
                "individual_id": "TIGER_BAJIRAO",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "100.0",
                "bbox_y_min": "150.0",
                "bbox_x_max": "450.0",
                "bbox_y_max": "500.0",
                "timestamp_utc": "2026-10-10T08:30:00Z",
                "camera_id": "PTR_CAM_01",
                "site_id": "PTR_STN_02",
                "latitude": "21.6950",
                "longitude": "79.2780",
                "split": "train",
                "license_id": "CC-BY-4.0",
                "attribution": "Pench Forest Department",
                "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "review_status": "verified",
            },
            {
                "sample_id": "SAMP_002",
                "dataset_name": "HyenaReID2022",
                "source_url": "https://lila.science/datasets",
                "relative_image_path": img2,
                "species_label": "Crocuta crocuta",
                "individual_id": "HYENA_042",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "0.1",
                "bbox_y_min": "0.2",
                "bbox_x_max": "0.8",
                "bbox_y_max": "0.9",
                "timestamp_utc": "2026-08-15T14:20:00+00:00",
                "camera_id": "HYN_CAM_05",
                "site_id": "SITE_B",
                "latitude": "-1.4500",
                "longitude": "35.1200",
                "split": "test",
                "license_id": "CC-BY-4.0",
                "attribution": "Hyena Project",
                "checksum_sha256": "f4c8996fb92427ae41e4649b934ca495991b7852b855e3b0c44298fc1c149afb",
                "review_status": "verified",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertTrue(report["is_valid"], f"Expected valid manifest, got errors: {report['errors']}")
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["total_samples"], 2)

    # -------------------------------------------------------------------------
    # TEST 2: Missing required columns
    # -------------------------------------------------------------------------
    def test_02_missing_columns(self):
        incomplete_columns = [c for c in REQUIRED_COLUMNS if c not in ("bbox_x_min", "license_id")]
        rows = [
            {"sample_id": "SAMP_001", "dataset_name": "TestDS"}
        ]
        self._write_manifest(rows, columns=incomplete_columns)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertFalse(report["is_valid"])
        self.assertGreater(report["error_count"], 0)
        col_errors = [e for e in report["errors"] if e["category"] == "columns"]
        self.assertTrue(any("Missing required column(s)" in e["message"] for e in col_errors))

    # -------------------------------------------------------------------------
    # TEST 3: Duplicate sample IDs
    # -------------------------------------------------------------------------
    def test_03_duplicate_sample_ids(self):
        rows = [
            {
                "sample_id": "DUP_ID_001",
                "dataset_name": "TestDS",
                "source_url": "https://example.org",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "T1",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "CC0",
                "attribution": "Tester",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            {
                "sample_id": "DUP_ID_001",  # Duplicate ID
                "dataset_name": "TestDS",
                "source_url": "https://example.org",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "T1",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "CC0",
                "attribution": "Tester",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertFalse(report["is_valid"])
        dup_errors = [e for e in report["errors"] if e["category"] == "duplicate_sample_id"]
        self.assertEqual(len(dup_errors), 1)
        self.assertIn("DUP_ID_001", dup_errors[0]["message"])

    # -------------------------------------------------------------------------
    # TEST 4: Invalid bounding boxes (inverted and partially missing)
    # -------------------------------------------------------------------------
    def test_04_invalid_bounding_boxes(self):
        rows = [
            {
                # Inverted coordinates: x_min >= x_max
                "sample_id": "BBOX_INV",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "400.0",
                "bbox_y_min": "100.0",
                "bbox_x_max": "200.0",  # Inverted!
                "bbox_y_max": "300.0",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            {
                # Partially missing bounding box coordinates
                "sample_id": "BBOX_PARTIAL",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "50.0",
                "bbox_y_min": "60.0",
                "bbox_x_max": "",       # Missing!
                "bbox_y_max": "120.0",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertFalse(report["is_valid"])
        inv_errors = [e for e in report["errors"] if e["category"] == "inverted_bbox_x"]
        partial_errors = [e for e in report["errors"] if e["category"] == "partially_missing_bbox"]
        self.assertEqual(len(inv_errors), 1)
        self.assertEqual(len(partial_errors), 1)

    # -------------------------------------------------------------------------
    # TEST 5: Invalid coordinates (latitude/longitude out of range)
    # -------------------------------------------------------------------------
    def test_05_invalid_coordinates(self):
        rows = [
            {
                "sample_id": "COORD_BAD",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "125.4000",   # Out of bounds (> 90.0)
                "longitude": "-195.0000", # Out of bounds (< -180.0)
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            }
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertFalse(report["is_valid"])
        lat_errors = [e for e in report["errors"] if e["category"] == "latitude_out_of_range"]
        lon_errors = [e for e in report["errors"] if e["category"] == "longitude_out_of_range"]
        self.assertEqual(len(lat_errors), 1)
        self.assertEqual(len(lon_errors), 1)

    # -------------------------------------------------------------------------
    # TEST 6: Missing image file on disk
    # -------------------------------------------------------------------------
    def test_06_missing_image_file(self):
        rows = [
            {
                "sample_id": "IMG_MISSING",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "nonexistent/does_not_exist.jpg",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            }
        ]
        self._write_manifest(rows)

        # Pass dataset_root so it actively verifies image file existence
        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        self.assertFalse(report["is_valid"])
        img_errors = [e for e in report["errors"] if e["category"] == "missing_image_file"]
        self.assertEqual(len(img_errors), 1)

    # -------------------------------------------------------------------------
    # TEST 7: Split leakage warning
    # -------------------------------------------------------------------------
    def test_07_split_leakage_warning(self):
        # The same individual 'TIGER_BAJIRAO' is placed in both 'train' and 'test'
        rows = [
            {
                "sample_id": "SPLIT_01",
                "dataset_name": "PenchDataset",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Panthera tigris",
                "individual_id": "TIGER_BAJIRAO",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "verified",
            },
            {
                "sample_id": "SPLIT_02",
                "dataset_name": "PenchDataset",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Panthera tigris",
                "individual_id": "TIGER_BAJIRAO",  # Same individual in test!
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "test",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "verified",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        # Split leakage is flagged as a quality warning
        self.assertGreater(report["split_leakage_count"], 0)
        leakage = report["split_leakages"][0]
        self.assertEqual(leakage["individual_id"], "TIGER_BAJIRAO")
        self.assertIn("train", leakage["splits_involved"])
        self.assertIn("test", leakage["splits_involved"])

    # -------------------------------------------------------------------------
    # TEST 8: Distinct identity concepts
    # -------------------------------------------------------------------------
    def test_08_distinct_identity_concepts(self):
        rows = [
            # 1. confirmed_known but missing individual_id -> error
            {
                "sample_id": "ID_CONF_NO_ID",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            # 2. unknown with no individual_id -> valid
            {
                "sample_id": "ID_UNKNOWN",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            # 3. missing_annotation -> valid
            {
                "sample_id": "ID_MISSING_ANNOTATION",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "missing_annotation",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            # 4. proposed_new_individual -> valid
            {
                "sample_id": "ID_PROPOSED",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "PTR_CANDIDATE_01",
                "identity_label_status": "proposed_new_individual",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "pending_review",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        inconsistent_errors = [e for e in report["errors"] if e["category"] == "inconsistent_identity"]
        self.assertEqual(len(inconsistent_errors), 1)
        self.assertIn("ID_CONF_NO_ID", inconsistent_errors[0]["sample_id"])

    # -------------------------------------------------------------------------
    # TEST 9: Timestamp timezone validation
    # -------------------------------------------------------------------------
    def test_09_timestamp_timezone_validation(self):
        rows = [
            {
                # Missing timezone indicator (naive timestamp) -> error
                "sample_id": "TS_NAIVE",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "2026-10-10 14:00:00",  # No UTC designation!
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
            {
                # Non-UTC timezone offset -> error
                "sample_id": "TS_NON_UTC",
                "dataset_name": "TestDS",
                "source_url": "",
                "relative_image_path": "",
                "species_label": "Tiger",
                "individual_id": "",
                "identity_label_status": "unknown",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "2026-10-10T14:00:00+05:30",  # Non-UTC offset!
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "",
                "attribution": "",
                "checksum_sha256": "",
                "review_status": "unreviewed",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        unverified_tz = [e for e in report["errors"] if e["category"] == "unverified_timezone"]
        non_utc_tz = [e for e in report["errors"] if e["category"] == "non_utc_timezone"]
        self.assertEqual(len(unverified_tz), 1)
        self.assertEqual(len(non_utc_tz), 1)

    # -------------------------------------------------------------------------
    # TEST 10: JSON report output generation and statistics
    # -------------------------------------------------------------------------
    def test_10_json_report_and_statistics(self):
        rows = [
            {
                "sample_id": "STAT_01",
                "dataset_name": "DS_Alpha",
                "source_url": "https://example.org",
                "relative_image_path": "",
                "species_label": "Panthera tigris",
                "individual_id": "T_01",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "2026-10-10T10:00:00Z",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "train",
                "license_id": "CC0",
                "attribution": "Tester",
                "checksum_sha256": "",
                "review_status": "verified",
            },
            {
                "sample_id": "STAT_02",
                "dataset_name": "DS_Alpha",
                "source_url": "https://example.org",
                "relative_image_path": "",
                "species_label": "Panthera pardus",
                "individual_id": "LEOPARD_01",
                "identity_label_status": "confirmed_known",
                "bbox_x_min": "",
                "bbox_y_min": "",
                "bbox_x_max": "",
                "bbox_y_max": "",
                "timestamp_utc": "2026-10-10T11:00:00Z",
                "camera_id": "",
                "site_id": "",
                "latitude": "",
                "longitude": "",
                "split": "val",
                "license_id": "CC0",
                "attribution": "Tester",
                "checksum_sha256": "",
                "review_status": "verified",
            },
        ]
        self._write_manifest(rows)

        validator = ManifestValidator(dataset_root=self.dataset_root)
        report = validator.validate_file(self.manifest_path)

        json_path = os.path.join(self.temp_dir, "report.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(report, jf)

        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as jf:
            loaded = json.load(jf)

        self.assertEqual(loaded["total_samples"], 2)
        stats = loaded["statistics"]
        self.assertEqual(stats["per_dataset_splits"]["DS_Alpha"]["train"], 1)
        self.assertEqual(stats["per_dataset_splits"]["DS_Alpha"]["val"], 1)
        self.assertIn("Panthera tigris", stats["per_species_splits"])
        self.assertIn("Panthera pardus", stats["per_species_splits"])


if __name__ == "__main__":
    unittest.main()
