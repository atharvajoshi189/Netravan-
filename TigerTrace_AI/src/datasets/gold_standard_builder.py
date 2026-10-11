"""
TigerTraceAI — Step 15C: Gold Standard Dataset Builder & Review Manager.

Manages human-in-the-loop review decisions, audit logging, coordinate validation,
encounter-grouped splitting, and YOLO detection-ready export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

logger = logging.getLogger("gold_standard_builder")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


# Canonical mapping for the 4 target species to species_taxonomy.json IDs
CANONICAL_SPECIES_IDS = {
    "chital": 3,
    "sambar": 1,
    "gaur": 6,
    "nilgai": 7,
}

VALID_REVIEW_ACTIONS = {
    "accepted_proposal",
    "modified_proposal",
    "manual_box",
    "rejected_proposal",
    "unknown_uncertain",
}


@dataclass
class VerifiedAnnotationBox:
    box_id: str
    sample_id: str
    canonical_class_id: int
    species_name: str
    bbox_norm_xywh: List[float]  # [x_center, y_center, width, height]
    bbox_pixel_xyxy: List[int]   # [x1, y1, x2, y2]
    source_proposal_id: Optional[str]
    review_action: str           # 'accepted_proposal' | 'modified_proposal' | 'manual_box' | 'unknown_uncertain'
    reviewer_id: str
    reviewed_at_utc: str
    notes: Optional[str] = None


@dataclass
class SampleReviewRecord:
    sample_id: str
    status: str                  # 'human_verified' | 'rejected_entirely' | 'unreviewed' | 'unknown_uncertain'
    reviewer_id: str
    reviewed_at_utc: str
    encounter_group_id: str
    boxes: List[VerifiedAnnotationBox] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    notes: Optional[str] = None


class GoldStandardBuilder:
    """Validates human review annotations, builds leakage-safe splits, and exports YOLO format."""

    def __init__(
        self,
        staging_dir: Path,
        taxonomy_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.staging_dir = Path(staging_dir)
        self.images_dir = self.staging_dir / "images"
        self.manifest_path = self.staging_dir / "manifests" / "staging_manifest.json"
        self.proposals_path = self.staging_dir / "provisional_proposals" / "provisional_proposals.json"
        self.reviews_dir = self.staging_dir / "human_reviews"
        self.output_yolo_dir = (
            Path(output_dir) if output_dir else self.staging_dir / "yolo_gold_standard"
        )
        self.taxonomy_path = (
            Path(taxonomy_path)
            if taxonomy_path
            else Path("TigerTrace_AI/data/taxonomy/species_taxonomy.json")
        )

        self.reviews: Dict[str, SampleReviewRecord] = {}
        self.manifest_samples: Dict[str, Dict[str, Any]] = {}
        self._load_staging_manifest()
        self._load_existing_reviews()

    def _load_staging_manifest(self) -> None:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Staging manifest not found at {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for s in data.get("samples", []):
            self.manifest_samples[s["sample_id"]] = s

    def _load_existing_reviews(self) -> None:
        reviews_file = self.reviews_dir / "human_verified_annotations.json"
        if reviews_file.exists():
            with open(reviews_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for r_data in data.get("reviews", []):
                s_id = r_data["sample_id"]
                boxes = [VerifiedAnnotationBox(**b) for b in r_data.get("boxes", [])]
                r_record = SampleReviewRecord(
                    sample_id=s_id,
                    status=r_data["status"],
                    reviewer_id=r_data["reviewer_id"],
                    reviewed_at_utc=r_data["reviewed_at_utc"],
                    encounter_group_id=r_data.get("encounter_group_id", "unknown_encounter"),
                    boxes=boxes,
                    rejection_reasons=r_data.get("rejection_reasons", []),
                    notes=r_data.get("notes"),
                )
                self.reviews[s_id] = r_record

    def validate_bbox_coordinates(
        self,
        bbox_norm: List[float],
        img_w: int,
        img_h: int,
    ) -> Tuple[bool, Optional[str], List[float], List[int]]:
        """
        Validates normalized coordinates [x_center, y_center, width, height]:
        - Ensures values within [0.0, 1.0]
        - Clamps minor boundary rounding errors (<= 0.005)
        - Rejects degenerate boxes (width <= 0, height <= 0, area < 0.0001)
        """
        if len(bbox_norm) != 4:
            return False, "invalid_bbox_length_must_be_4", [], []

        xc, yc, w, h = bbox_norm

        if w <= 0 or h <= 0:
            return False, f"degenerate_box_non_positive_dimensions_{w}x{h}", [], []

        if w * h < 0.0001:
            return False, f"box_area_too_small_{w*h:.6f}", [], []

        # Check out-of-bounds with small boundary tolerance
        tol = 0.005
        x_min = xc - w / 2
        x_max = xc + w / 2
        y_min = yc - h / 2
        y_max = yc + h / 2

        if x_min < -tol or y_min < -tol or x_max > 1.0 + tol or y_max > 1.0 + tol:
            return False, f"box_substantially_out_of_bounds_[{x_min:.3f},{y_min:.3f},{x_max:.3f},{y_max:.3f}]", [], []

        # Clamp to [0.0, 1.0]
        x_min_c = max(0.0, min(1.0, x_min))
        y_min_c = max(0.0, min(1.0, y_min))
        x_max_c = max(0.0, min(1.0, x_max))
        y_max_c = max(0.0, min(1.0, y_max))

        w_c = x_max_c - x_min_c
        h_c = y_max_c - y_min_c
        xc_c = x_min_c + w_c / 2
        yc_c = y_min_c + h_c / 2

        norm_clamped = [round(xc_c, 5), round(yc_c, 5), round(w_c, 5), round(h_c, 5)]

        # Pixel coords
        px1 = int(round(x_min_c * img_w))
        py1 = int(round(y_min_c * img_h))
        px2 = int(round(x_max_c * img_w))
        py2 = int(round(y_max_c * img_h))

        return True, None, norm_clamped, [px1, py1, px2, py2]

    def record_human_review(
        self,
        sample_id: str,
        reviewer_id: str,
        review_decision: str,  # 'human_verified' | 'rejected_entirely' | 'unknown_uncertain'
        boxes: List[Dict[str, Any]],
        notes: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Records a human review decision for a staging sample with full audit trail."""
        if sample_id not in self.manifest_samples:
            return False, f"sample_id_{sample_id}_not_found_in_staging_manifest"

        sample = self.manifest_samples[sample_id]
        img_path = self.images_dir / f"{sample_id}.jpg"
        if not img_path.exists():
            return False, f"image_file_missing_for_{sample_id}"

        im = cv2.imread(str(img_path))
        if im is None:
            return False, f"unreadable_image_{sample_id}"
        img_h, img_w = im.shape[:2]

        verified_boxes: List[VerifiedAnnotationBox] = []
        rejection_reasons: List[str] = []

        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        encounter_group = sample.get("encounter_group_id", "unknown_encounter")

        if review_decision == "rejected_entirely":
            record = SampleReviewRecord(
                sample_id=sample_id,
                status="rejected_entirely",
                reviewer_id=reviewer_id,
                reviewed_at_utc=now_utc,
                encounter_group_id=encounter_group,
                boxes=[],
                rejection_reasons=[notes or "reviewer_rejected_sample"],
                notes=notes,
            )
            self.reviews[sample_id] = record
            self._save_reviews()
            return True, None

        box_idx = 1
        for b in boxes:
            species_label = b.get("species_label", "").lower()
            if species_label not in CANONICAL_SPECIES_IDS and species_label != "unknown_uncertain":
                rejection_reasons.append(f"invalid_species_label_{species_label}")
                continue

            action = b.get("review_action", "accepted_proposal")
            if action not in VALID_REVIEW_ACTIONS:
                rejection_reasons.append(f"invalid_review_action_{action}")
                continue

            if action == "rejected_proposal":
                # Rejected individual proposal is logged but not added to valid boxes
                continue

            bbox_raw = b.get("bbox_norm_xywh", [])
            is_valid, err_msg, bbox_clamped, pixel_xyxy = self.validate_bbox_coordinates(
                bbox_raw, img_w, img_h
            )
            if not is_valid:
                rejection_reasons.append(err_msg or "invalid_coordinates")
                continue

            class_id = (
                CANONICAL_SPECIES_IDS[species_label]
                if species_label in CANONICAL_SPECIES_IDS
                else -1  # -1 represents unknown_uncertain
            )

            v_box = VerifiedAnnotationBox(
                box_id=f"{sample_id}_b{box_idx}",
                sample_id=sample_id,
                canonical_class_id=class_id,
                species_name=species_label,
                bbox_norm_xywh=bbox_clamped,
                bbox_pixel_xyxy=pixel_xyxy,
                source_proposal_id=b.get("source_proposal_id"),
                review_action=action,
                reviewer_id=reviewer_id,
                reviewed_at_utc=now_utc,
                notes=b.get("notes"),
            )
            verified_boxes.append(v_box)
            box_idx += 1

        status = review_decision
        if review_decision == "human_verified" and not verified_boxes:
            status = "rejected_no_valid_boxes"

        record = SampleReviewRecord(
            sample_id=sample_id,
            status=status,
            reviewer_id=reviewer_id,
            reviewed_at_utc=now_utc,
            encounter_group_id=encounter_group,
            boxes=verified_boxes,
            rejection_reasons=rejection_reasons,
            notes=notes,
        )
        self.reviews[sample_id] = record
        self._save_reviews()
        return True, None

    def _save_reviews(self) -> None:
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        out_file = self.reviews_dir / "human_verified_annotations.json"
        payload = {
            "version": "1.0.0",
            "info": "Audited human review decisions and gold-standard bounding boxes.",
            "total_reviewed_samples": len(self.reviews),
            "reviews": [
                {
                    "sample_id": r.sample_id,
                    "status": r.status,
                    "reviewer_id": r.reviewer_id,
                    "reviewed_at_utc": r.reviewed_at_utc,
                    "encounter_group_id": r.encounter_group_id,
                    "boxes": [asdict(b) for b in r.boxes],
                    "rejection_reasons": r.rejection_reasons,
                    "notes": r.notes,
                }
                for r in self.reviews.values()
            ],
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def export_yolo_detection_ready_dataset(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Exports human-verified samples into a standard YOLO detection layout:
        images/{train,val,test}
        labels/{train,val,test}
        data.yaml

        Enforces:
        - Leakage prevention by grouping encounters (all photos from same user/date remain together).
        - Excludes unreviewed, rejected, or unknown/uncertain samples from train split.
        - Preserves provenance, licenses, and attributions in gold_standard_manifest.json.
        """
        self.output_yolo_dir.mkdir(parents=True, exist_ok=True)
        images_yolo_dir = self.output_yolo_dir / "images"
        labels_yolo_dir = self.output_yolo_dir / "labels"

        for split in ["train", "val", "test"]:
            (images_yolo_dir / split).mkdir(parents=True, exist_ok=True)
            (labels_yolo_dir / split).mkdir(parents=True, exist_ok=True)

        # 1. Filter only verified samples with valid boxes
        verified_samples = [
            r for r in self.reviews.values()
            if r.status == "human_verified" and any(b.canonical_class_id >= 0 for b in r.boxes)
        ]

        # 2. Group by encounter_group_id
        encounter_groups: Dict[str, List[SampleReviewRecord]] = {}
        for r in verified_samples:
            encounter_groups.setdefault(r.encounter_group_id, []).append(r)

        # Deterministic sort for reproducible split
        sorted_encounters = sorted(list(encounter_groups.keys()))
        total_encounters = len(sorted_encounters)

        n_train = max(1, int(round(total_encounters * train_ratio)))
        n_val = max(1, int(round(total_encounters * val_ratio)))
        # Remaining goes to test
        train_encounters = set(sorted_encounters[:n_train])
        val_encounters = set(sorted_encounters[n_train : n_train + n_val])
        test_encounters = set(sorted_encounters[n_train + n_val :])

        split_counts = {"train": 0, "val": 0, "test": 0}
        split_boxes = {"train": 0, "val": 0, "test": 0}
        exported_samples = []

        for enc_id, group_records in encounter_groups.items():
            if enc_id in train_encounters:
                split = "train"
            elif enc_id in val_encounters:
                split = "val"
            else:
                split = "test"

            for rec in group_records:
                s_id = rec.sample_id
                src_img_file = self.images_dir / f"{s_id}.jpg"
                if not src_img_file.exists():
                    continue

                dst_img_file = images_yolo_dir / split / f"{s_id}.jpg"
                dst_label_file = labels_yolo_dir / split / f"{s_id}.txt"

                shutil.copy2(src_img_file, dst_img_file)

                # Write YOLO .txt lines: <class_id> <x_c> <y_c> <w> <h>
                label_lines = []
                for b in rec.boxes:
                    if b.canonical_class_id >= 0:  # Exclude unknown (-1) from detector training
                        xc, yc, w, h = b.bbox_norm_xywh
                        label_lines.append(f"{b.canonical_class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
                        split_boxes[split] += 1

                with open(dst_label_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

                split_counts[split] += 1

                manifest_sample = self.manifest_samples.get(s_id, {})
                exported_samples.append({
                    "sample_id": s_id,
                    "split": split,
                    "encounter_group_id": rec.encounter_group_id,
                    "source_url": manifest_sample.get("source_url"),
                    "license_code": manifest_sample.get("license_code"),
                    "attribution": manifest_sample.get("attribution"),
                    "boxes": [asdict(b) for b in rec.boxes if b.canonical_class_id >= 0],
                })

        # 3. Create data.yaml
        yaml_content = (
            f"path: {self.output_yolo_dir.as_posix()}\n"
            f"train: images/train\n"
            f"val: images/val\n"
            f"test: images/test\n\n"
            f"nc: 17\n"
            f"names:\n"
            f"  0: tiger\n"
            f"  1: sambar\n"
            f"  2: wild_boar\n"
            f"  3: chital\n"
            f"  4: cattle\n"
            f"  5: muntjac\n"
            f"  6: gaur\n"
            f"  7: nilgai\n"
            f"  8: sloth_bear\n"
            f"  9: goat\n"
            f"  10: indian_hare\n"
            f"  11: buffalo\n"
            f"  12: grey_junglefowl\n"
            f"  13: peafowl\n"
            f"  14: flying_squirrel\n"
            f"  15: grey_langur\n"
            f"  16: grey_mongoose\n"
        )
        yaml_path = self.output_yolo_dir / "data.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 4. Manifest
        gold_manifest_path = self.output_yolo_dir / "gold_standard_manifest.json"
        total_exported = len(exported_samples)
        is_too_small = total_exported < 500

        report_summary = {
            "version": "1.0.0",
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_verified_images": total_exported,
            "split_images_count": split_counts,
            "split_boxes_count": split_boxes,
            "total_boxes": sum(split_boxes.values()),
            "leakage_safety": "Grouped strictly by encounter_group_id",
            "is_too_small_for_reliable_training": is_too_small,
            "warning": (
                "CRITICAL PILOT BENCHMARK WARNING: This dataset contains only a small number of images. "
                "With ~5-8 images per class in the train split, it is COMPLETELY INSUFFICIENT for training "
                "a production 17-class wildlife detector. It serves STRICTLY as a gold-standard qualitative "
                "verification and evaluation benchmark."
            ),
            "samples": exported_samples,
        }

        with open(gold_manifest_path, "w", encoding="utf-8") as f:
            json.dump(report_summary, f, indent=2)

        logger.info(f"YOLO gold standard exported to {self.output_yolo_dir}: {split_counts} images, {split_boxes} boxes")
        return report_summary


def main():
    parser = argparse.ArgumentParser(description="TigerTraceAI Step 15C Gold Standard Builder")
    parser.add_argument(
        "--staging-dir",
        type=str,
        default="TigerTrace_AI/data/staging_wildlife_pilot",
        help="Path to staging directory",
    )
    parser.add_argument(
        "--export-yolo",
        action="store_true",
        help="Export reviewed samples to YOLO detection format",
    )
    args = parser.parse_args()

    builder = GoldStandardBuilder(staging_dir=Path(args.staging_dir))
    if args.export_yolo:
        summary = builder.export_yolo_detection_ready_dataset()
        print("\n" + "=" * 60)
        print("YOLO GOLD STANDARD EXPORT COMPLETE")
        print(f"Verified Images Exported: {summary['total_verified_images']}")
        print(f"Split breakdown: {summary['split_images_count']}")
        print(f"Total BBoxes: {summary['total_boxes']}")
        print(f"Warning: {summary['warning']}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
