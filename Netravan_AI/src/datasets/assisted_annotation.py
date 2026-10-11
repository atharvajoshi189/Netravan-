"""
TigerTraceAI — Step 15C: Assisted Annotation & MegaDetector Investigation Engine.

Investigates availability of MegaDetector (MDv5a/MDv5b) and provides assisted
animal proposal generation on staging images without treating proposals as confirmed species.
"""

from __future__ import annotations

import glob
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("assisted_annotation")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


@dataclass
class BBoxProposal:
    proposal_id: str
    sample_id: str
    image_file: str
    bbox_norm_xywh: List[float]  # [x_center, y_center, width, height] normalized
    bbox_pixel_xyxy: List[int]   # [x_min, y_min, x_max, y_max] absolute pixels
    proposal_source: str        # 'yolov8n_coco_quadruped' | 'megadetector_v5a'
    detector_label: str         # 'cow', 'sheep', 'horse', 'animal', etc.
    detector_confidence: float
    is_verified: bool = False
    review_status: str = "provisional_unreviewed"
    assigned_species: Optional[str] = None
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None


@dataclass
class MegaDetectorInvestigationReport:
    megadetector_installed: bool
    checkpoint_found: bool
    checkpoint_path: Optional[str]
    checkpoint_size_mb: float
    blocker_reason: Optional[str]
    setup_instructions: List[str]
    fallback_used: str
    total_staging_images: int
    provisional_proposals_count: int


class AssistedAnnotationEngine:
    """Manages assisted animal bounding-box proposal generation for staging images."""

    COCO_ANIMAL_CLASSES = {
        15: "cat",
        16: "dog",
        17: "horse",
        18: "sheep",
        19: "cow",
        20: "elephant",
        21: "bear",
        22: "zebra",
        23: "giraffe",
    }

    def __init__(
        self,
        staging_dir: Path,
        models_dir: Optional[Path] = None,
        confidence_threshold: float = 0.20,
    ):
        self.staging_dir = Path(staging_dir)
        self.images_dir = self.staging_dir / "images"
        self.manifest_path = self.staging_dir / "manifests" / "staging_manifest.json"
        self.proposals_dir = self.staging_dir / "provisional_proposals"
        self.models_dir = Path(models_dir) if models_dir else Path("TigerTrace_AI/data/models")
        self.confidence_threshold = confidence_threshold

        self.proposals: List[BBoxProposal] = []

    def check_megadetector_availability(self) -> MegaDetectorInvestigationReport:
        """
        Audits the local environment for MegaDetector checkpoints (md_v5a.pt / md_v5b.pt)
        and runtime libraries (PytorchWildlife).
        """
        # 1. Check for runtime library
        try:
            import PytorchWildlife  # noqa: F401
            runtime_available = True
        except ImportError:
            runtime_available = False

        # 2. Check for checkpoint files in repo
        possible_patterns = [
            "**/md_v5a*.pt",
            "**/md_v5b*.pt",
            "**/megadetector*.pt",
        ]
        found_ckpts = []
        for pat in possible_patterns:
            found_ckpts.extend(glob.glob(pat, recursive=True))

        ckpt_found = len(found_ckpts) > 0
        ckpt_path = found_ckpts[0] if ckpt_found else None
        ckpt_size_mb = 0.0
        if ckpt_path and os.path.exists(ckpt_path):
            ckpt_size_mb = round(os.path.getsize(ckpt_path) / (1024 * 1024), 2)

        blocker = None
        instructions = []
        if not ckpt_found:
            blocker = (
                "MegaDetector v5a checkpoint (md_v5a.0.0.pt, ~140 MB) is NOT present locally. "
                "Per Step 15A/15C safety rules, large model archives must not be downloaded "
                "without explicit user approval."
            )
            instructions = [
                "1. Download 'md_v5a.0.0.pt' (140 MB) from https://github.com/agentmorris/MegaDetector/releases",
                "2. Place the weights at 'TigerTrace_AI/data/models/md_v5a.0.0.pt'",
                "3. Install runtime: 'pip install PytorchWildlife' or clone the official MegaDetector repository.",
                "4. Run AssistedAnnotationEngine with md_checkpoint_path pointing to md_v5a.0.0.pt.",
            ]

        fallback = (
            "yolov8n_coco_quadruped_detector"
            if not ckpt_found
            else "megadetector_native"
        )

        return MegaDetectorInvestigationReport(
            megadetector_installed=runtime_available,
            checkpoint_found=ckpt_found,
            checkpoint_path=ckpt_path,
            checkpoint_size_mb=ckpt_size_mb,
            blocker_reason=blocker,
            setup_instructions=instructions,
            fallback_used=fallback,
            total_staging_images=0,
            provisional_proposals_count=0,
        )

    def generate_provisional_proposals_coco(
        self,
        yolo_checkpoint: str = "yolov8n.pt",
    ) -> List[BBoxProposal]:
        """
        Uses locally available YOLOv8n COCO weights to detect quadrupeds/large mammals
        as provisional spatial bounding boxes.

        CRITICAL RULE: Never marks an animal proposal as a confirmed species label.
        All proposals remain 'provisional_unreviewed'.
        """
        from ultralytics import YOLO

        if not os.path.exists(yolo_checkpoint):
            raise FileNotFoundError(f"Local YOLO checkpoint not found at {yolo_checkpoint}")

        model = YOLO(yolo_checkpoint)
        image_files = sorted(list(self.images_dir.glob("*.jpg")))
        logger.info(f"Generating assisted proposals across {len(image_files)} staging images using {yolo_checkpoint}...")

        proposals: List[BBoxProposal] = []
        proposal_idx = 1

        for img_path in image_files:
            file_name = img_path.name
            sample_id = img_path.stem

            # Read image to obtain exact dimensions
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            h_img, w_img = img.shape[:2]

            # Inference on single image
            results = model(str(img_path), verbose=False, conf=self.confidence_threshold)[0]
            boxes = results.boxes

            for b in boxes:
                cls_id = int(b.cls[0].item())
                conf = float(b.conf[0].item())

                # Check if detected object is a quadruped / large mammal or person
                # We filter to animal classes and large herbivores/quadrupeds
                if cls_id in self.COCO_ANIMAL_CLASSES:
                    coco_label = self.COCO_ANIMAL_CLASSES[cls_id]

                    # Normalized xywh
                    xywhn = b.xywhn[0].tolist()
                    x_c, y_c, w_norm, h_norm = xywhn

                    # Absolute xyxy in pixels
                    x1 = max(0, int((x_c - w_norm / 2) * w_img))
                    y1 = max(0, int((y_c - h_norm / 2) * h_img))
                    x2 = min(w_img, int((x_c + w_norm / 2) * w_img))
                    y2 = min(h_img, int((y_c + h_norm / 2) * h_img))

                    prop = BBoxProposal(
                        proposal_id=f"prop_{proposal_idx:04d}",
                        sample_id=sample_id,
                        image_file=file_name,
                        bbox_norm_xywh=[round(x_c, 5), round(y_c, 5), round(w_norm, 5), round(h_norm, 5)],
                        bbox_pixel_xyxy=[x1, y1, x2, y2],
                        proposal_source="yolov8n_coco_quadruped",
                        detector_label=coco_label,
                        detector_confidence=round(conf, 4),
                        is_verified=False,
                        review_status="provisional_unreviewed",
                        assigned_species=None,  # STRICT: not confirmed yet
                    )
                    proposals.append(prop)
                    proposal_idx += 1

        self.proposals = proposals
        self._save_provisional_proposals()
        return proposals

    def _save_provisional_proposals(self) -> None:
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        out_file = self.proposals_dir / "provisional_proposals.json"
        payload = {
            "version": "1.0.0",
            "info": "Provisional animal bounding-box proposals. NOT confirmed species labels. Requires human verification.",
            "total_proposals": len(self.proposals),
            "proposals": [asdict(p) for p in self.proposals],
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Saved {len(self.proposals)} provisional proposals to {out_file}")


def main():
    staging_dir = Path("TigerTrace_AI/data/staging_wildlife_pilot")
    engine = AssistedAnnotationEngine(staging_dir=staging_dir)

    # 1. Audit MegaDetector
    report = engine.check_megadetector_availability()
    print("\n" + "=" * 60)
    print("MEGADETECTOR INVESTIGATION AUDIT")
    print(f"MegaDetector Runtime Installed: {report.megadetector_installed}")
    print(f"Checkpoint Found: {report.checkpoint_found}")
    if report.blocker_reason:
        print(f"Blocker: {report.blocker_reason}")
    print(f"Fallback Strategy: {report.fallback_used}")
    print("=" * 60)

    # 2. Run local assisted proposals
    proposals = engine.generate_provisional_proposals_coco()
    print(f"\nGenerated {len(proposals)} provisional bounding-box proposals.")
    print("All proposals stored with 'review_status: provisional_unreviewed'.")


if __name__ == "__main__":
    main()
