import os
import sys
import unittest
import csv
import numpy as np
import cv2
import tempfile
import shutil

# Ensure TigerTrace_AI package and root are on sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pkg_dir = os.path.join(repo_root, "TigerTrace_AI")
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.reid.flank_extractor import FlankExtractor, resolve_and_validate_bbox


class TestFlankExtractorBoundingBox(unittest.TestCase):
    """
    Step 9B Regression Test Suite: Normalized and Absolute Bounding-Box Handling.
    Covers:
    1. A normalized box extracts the expected sub-region.
    2. Pixel-coordinate boxes retain existing behavior.
    3. A normalized box touching image boundaries is handled correctly.
    4. Empty/missing boxes preserve the documented pre-cropped-image behavior.
    5. Malformed coordinate counts are rejected safely.
    6. Reversed and zero-area boxes are rejected.
    7. Negative and out-of-bounds values are handled according to documented policy.
    8. NaN and infinity are rejected.
    9. A valid crop is not silently replaced with the full image.
    10. Existing ATRW pilot manifest entries with empty bbox fields continue to work.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = FlankExtractor(target_size=(384, 384))

        # Create a synthetic 200x200 3-channel test image with 4 distinct quadrants:
        # Top-Left [0:100, 0:100]: Solid Blue (255, 0, 0)
        # Top-Right [0:100, 100:200]: Solid Green (0, 255, 0)
        # Bottom-Left [100:200, 0:100]: Solid Red (0, 0, 255)
        # Bottom-Right [100:200, 100:200]: Solid White (255, 255, 255)
        self.img_h, self.img_w = 200, 200
        self.quad_img = np.zeros((self.img_h, self.img_w, 3), dtype=np.uint8)
        self.quad_img[0:100, 0:100] = [255, 0, 0]      # Blue
        self.quad_img[0:100, 100:200] = [0, 255, 0]    # Green
        self.quad_img[100:200, 0:100] = [0, 0, 255]    # Red
        self.quad_img[100:200, 100:200] = [255, 255, 255]  # White

        self.test_img_path = os.path.join(self.temp_dir, "quad_test.png")
        cv2.imwrite(self.test_img_path, self.quad_img)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. A normalized box extracts the expected sub-region
    # -------------------------------------------------------------------------
    def test_01_normalized_box_extracts_expected_subregion(self):
        # Top-left quadrant in normalized space [0.0, 0.0, 0.5, 0.5]
        resolved = resolve_and_validate_bbox([0.0, 0.0, 0.5, 0.5], img_width=self.img_w, img_height=self.img_h)
        self.assertEqual(resolved, (0, 0, 100, 100))

        crop, _ = self.extractor.extract_flank_crop(
            self.test_img_path, bbox_xyxy=[0.0, 0.0, 0.5, 0.5], save_enhanced=False
        )
        self.assertEqual(crop.shape, (384, 384, 3))
        # Top-left quadrant is blue; every pixel in the unenhanced crop must be Blue [255, 0, 0]
        self.assertTrue(np.all(crop[:, :, 0] == 255))
        self.assertTrue(np.all(crop[:, :, 1] == 0))
        self.assertTrue(np.all(crop[:, :, 2] == 0))

        # Bottom-right quadrant [0.5, 0.5, 1.0, 1.0] -> White [255, 255, 255]
        crop_br, _ = self.extractor.extract_flank_crop(
            self.test_img_path, bbox_xyxy=[0.5, 0.5, 1.0, 1.0], save_enhanced=False
        )
        self.assertTrue(np.all(crop_br == 255))

        # Arbitrary normalized coordinates on a 1000x1000 dimension
        res_1000 = resolve_and_validate_bbox([0.1, 0.2, 0.8, 0.9], img_width=1000, img_height=1000)
        self.assertEqual(res_1000, (100, 200, 800, 900))

    # -------------------------------------------------------------------------
    # 2. Pixel-coordinate boxes retain existing behavior
    # -------------------------------------------------------------------------
    def test_02_pixel_coordinate_boxes_retain_existing_behavior(self):
        # Pixel coordinates [0, 0, 100, 100] corresponds to top-left quadrant
        resolved = resolve_and_validate_bbox([0, 0, 100, 100], img_width=self.img_w, img_height=self.img_h)
        self.assertEqual(resolved, (0, 0, 100, 100))

        crop, _ = self.extractor.extract_flank_crop(
            self.test_img_path, bbox_xyxy=[0, 0, 100, 100], save_enhanced=False
        )
        self.assertTrue(np.all(crop[:, :, 0] == 255))
        self.assertTrue(np.all(crop[:, :, 1] == 0))
        self.assertTrue(np.all(crop[:, :, 2] == 0))

        # Pixel coordinates on 500x500 image
        res_pixel = resolve_and_validate_bbox([50, 60, 250, 260], img_width=500, img_height=500)
        self.assertEqual(res_pixel, (50, 60, 250, 260))

    # -------------------------------------------------------------------------
    # 3. A normalized box touching image boundaries is handled correctly
    # -------------------------------------------------------------------------
    def test_03_normalized_box_touching_image_boundaries(self):
        # Full normalized frame [0.0, 0.0, 1.0, 1.0]
        res_full = resolve_and_validate_bbox([0.0, 0.0, 1.0, 1.0], img_width=self.img_w, img_height=self.img_h)
        self.assertEqual(res_full, (0, 0, 200, 200))

        # Bottom half touching left, right, bottom [0.0, 0.5, 1.0, 1.0]
        res_bottom = resolve_and_validate_bbox([0.0, 0.5, 1.0, 1.0], img_width=self.img_w, img_height=self.img_h)
        self.assertEqual(res_bottom, (0, 100, 200, 200))

        # Boundary clipping with edge values
        res_edge = resolve_and_validate_bbox([0.0, 0.0, 1.0, 0.5], img_width=self.img_w, img_height=self.img_h)
        self.assertEqual(res_edge, (0, 0, 200, 100))

    # -------------------------------------------------------------------------
    # 4. Empty/missing boxes preserve the documented pre-cropped-image behavior
    # -------------------------------------------------------------------------
    def test_04_empty_and_missing_boxes_preserve_precropped_behavior(self):
        # bbox=None returns None from resolver
        self.assertIsNone(resolve_and_validate_bbox(None, img_width=200, img_height=200))

        # Empty string or empty container returns None
        self.assertIsNone(resolve_and_validate_bbox("", img_width=200, img_height=200))
        self.assertIsNone(resolve_and_validate_bbox([], img_width=200, img_height=200))
        self.assertIsNone(resolve_and_validate_bbox((), img_width=200, img_height=200))

        # Manifest CSV-style empty fields ["", "", "", ""] returns None
        self.assertIsNone(resolve_and_validate_bbox(["", "", "", ""], img_width=200, img_height=200))
        self.assertIsNone(resolve_and_validate_bbox([None, None, None, None], img_width=200, img_height=200))

        # In extractor, bbox=None extracts the full image
        crop_none, _ = self.extractor.extract_flank_crop(self.test_img_path, bbox_xyxy=None)
        self.assertEqual(crop_none.shape, (384, 384, 3))

        crop_empty_list, _ = self.extractor.extract_flank_crop(self.test_img_path, bbox_xyxy=[])
        self.assertTrue(np.array_equal(crop_none, crop_empty_list))

        crop_empty_fields, _ = self.extractor.extract_flank_crop(self.test_img_path, bbox_xyxy=["", "", "", ""])
        self.assertTrue(np.array_equal(crop_none, crop_empty_fields))

    # -------------------------------------------------------------------------
    # 5. Malformed coordinate counts are rejected safely
    # -------------------------------------------------------------------------
    def test_05_malformed_coordinate_counts_rejected(self):
        with self.assertRaises(ValueError):
            resolve_and_validate_bbox([0.1, 0.2, 0.8], img_width=200, img_height=200)

        with self.assertRaises(ValueError):
            resolve_and_validate_bbox([0.1, 0.2, 0.8, 0.9, 1.0], img_width=200, img_height=200)

        with self.assertRaises(ValueError):
            resolve_and_validate_bbox([100], img_width=200, img_height=200)

        with self.assertRaises(ValueError):
            self.extractor.extract_flank_crop(self.test_img_path, bbox_xyxy=[10, 20])

    # -------------------------------------------------------------------------
    # 6. Reversed and zero-area boxes are rejected
    # -------------------------------------------------------------------------
    def test_06_reversed_and_zero_area_boxes_rejected(self):
        # x2 <= x1 (horizontal reverse)
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.8, 0.2, 0.1, 0.9], img_width=200, img_height=200)
        self.assertIn("x2 <= x1", str(ctx.exception))

        # y2 <= y1 (vertical reverse)
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.1, 0.9, 0.8, 0.2], img_width=200, img_height=200)
        self.assertIn("y2 <= y1", str(ctx.exception))

        # Zero width (x1 == x2)
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.5, 0.1, 0.5, 0.9], img_width=200, img_height=200)
        self.assertIn("x2 <= x1", str(ctx.exception))

        # Zero height (y1 == y2)
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.1, 0.5, 0.8, 0.5], img_width=200, img_height=200)
        self.assertIn("y2 <= y1", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 7. Negative and out-of-bounds values handled according to policy
    # -------------------------------------------------------------------------
    def test_07_negative_and_out_of_bounds_policy(self):
        # Negative coordinate strictly rejected
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([-0.1, 0.2, 0.8, 0.9], img_width=200, img_height=200)
        self.assertIn("non-negative", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([10, -5, 100, 100], img_width=200, img_height=200)
        self.assertIn("non-negative", str(ctx.exception))

        # Pixel box origin entirely outside image dimensions rejected
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([250, 50, 300, 100], img_width=200, img_height=200)
        self.assertIn("outside image dimensions", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([50, 250, 100, 300], img_width=200, img_height=200)
        self.assertIn("outside image dimensions", str(ctx.exception))

        # Pixel box starting inside but extending slightly beyond image is clipped
        res_clipped = resolve_and_validate_bbox([50, 50, 215, 210], img_width=200, img_height=200)
        self.assertEqual(res_clipped, (50, 50, 200, 200))

    # -------------------------------------------------------------------------
    # 8. NaN and infinity are rejected
    # -------------------------------------------------------------------------
    def test_08_nan_and_infinity_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([float("nan"), 0.2, 0.8, 0.9], img_width=200, img_height=200)
        self.assertIn("non-finite", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.1, float("inf"), 0.8, 0.9], img_width=200, img_height=200)
        self.assertIn("non-finite", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.1, 0.2, float("-inf"), 0.9], img_width=200, img_height=200)
        self.assertIn("non-finite", str(ctx.exception))

        # Non-numeric string
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox(["invalid", 0.2, 0.8, 0.9], img_width=200, img_height=200)
        self.assertIn("numeric", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 9. A valid crop is not silently replaced with the full image
    # -------------------------------------------------------------------------
    def test_09_valid_crop_not_silently_replaced_with_full_image(self):
        # Top-left quadrant crop
        crop_sub, _ = self.extractor.extract_flank_crop(
            self.test_img_path, bbox_xyxy=[0.0, 0.0, 0.5, 0.5], save_enhanced=False
        )
        # Full image crop
        crop_full, _ = self.extractor.extract_flank_crop(
            self.test_img_path, bbox_xyxy=None, save_enhanced=False
        )
        # Sub-region (pure blue) must NOT equal full image (multicolor quadrants)
        self.assertFalse(
            np.array_equal(crop_sub, crop_full),
            "Valid sub-crop must NOT be silently replaced with the full image!"
        )

        # Degenerate box below minimum threshold (40x40 pixels) is rejected, NOT silently replaced with full image
        # e.g., 200x200 image, [0.1, 0.1, 0.12, 0.12] -> width=4px, height=4px < 40px
        with self.assertRaises(ValueError) as ctx:
            resolve_and_validate_bbox([0.1, 0.1, 0.12, 0.12], img_width=200, img_height=200)
        self.assertIn("below minimum viable dimension", str(ctx.exception))

        with self.assertRaises(ValueError):
            self.extractor.extract_flank_crop(self.test_img_path, bbox_xyxy=[0.1, 0.1, 0.12, 0.12])

    # -------------------------------------------------------------------------
    # 10. Existing ATRW pilot manifest entries with empty bbox fields continue to work
    # -------------------------------------------------------------------------
    def test_10_existing_atrw_pilot_manifest_entries_work(self):
        pilot_manifest_path = os.path.join(repo_root, "data", "staging", "atrw_pilot", "atrw_pilot_manifest.csv")
        self.assertTrue(os.path.exists(pilot_manifest_path), "ATRW pilot manifest must exist")

        with open(pilot_manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        self.assertEqual(len(records), 13, "Must have exactly 13 approved ATRW records")

        staging_dir = os.path.join(repo_root, "data", "staging", "atrw_pilot")
        for r in records:
            # Confirm manifest fields are genuinely empty
            self.assertEqual(r["bbox_x_min"], "")
            self.assertEqual(r["bbox_y_min"], "")
            self.assertEqual(r["bbox_x_max"], "")
            self.assertEqual(r["bbox_y_max"], "")

            img_path = os.path.join(staging_dir, r["relative_image_path"])
            self.assertTrue(os.path.exists(img_path), f"Image must exist: {img_path}")

            # Pass empty bbox representation from manifest
            manifest_bbox = [r["bbox_x_min"], r["bbox_y_min"], r["bbox_x_max"], r["bbox_y_max"]]
            crop, crop_path = self.extractor.extract_flank_crop(
                img_path, bbox_xyxy=manifest_bbox, output_dir=None, save_enhanced=False
            )
            self.assertIsNotNone(crop)
            self.assertEqual(crop.shape, (384, 384, 3))


if __name__ == "__main__":
    unittest.main()
