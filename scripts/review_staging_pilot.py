"""
TigerTraceAI — Step 15C Review Station CLI Script.

Provides an interactive CLI or automated validation for reviewing the 40 staging images,
inspecting provisional proposals, recording reviewer approvals/rejections,
and exporting leakage-safe YOLO datasets.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from TigerTrace_AI.src.datasets.assisted_annotation import AssistedAnnotationEngine
from TigerTrace_AI.src.datasets.cvat_exporter import CVATProjectExporter
from TigerTrace_AI.src.datasets.gold_standard_builder import GoldStandardBuilder


def main():
    parser = argparse.ArgumentParser(description="TigerTraceAI Step 15C Staging Review CLI")
    parser.add_argument(
        "--staging-dir",
        type=str,
        default="TigerTrace_AI/data/staging_wildlife_pilot",
        help="Path to staging pilot directory",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display current review status across all 40 images",
    )
    parser.add_argument(
        "--export-yolo",
        action="store_true",
        help="Export all human-verified samples into YOLO detection layout",
    )
    parser.add_argument(
        "--generate-cvat",
        action="store_true",
        help="Generate or update CVAT XML annotation project",
    )
    parser.add_argument(
        "--run-assisted",
        action="store_true",
        help="Run assisted proposal generator on staging images",
    )
    args = parser.parse_args()

    staging_path = Path(args.staging_dir)

    if args.run_assisted:
        engine = AssistedAnnotationEngine(staging_dir=staging_path)
        audit = engine.check_megadetector_availability()
        print("\n--- MegaDetector Audit ---")
        print(f"Installed: {audit.megadetector_installed}, Checkpoint: {audit.checkpoint_found}")
        if audit.blocker_reason:
            print(f"Blocker: {audit.blocker_reason}")
        props = engine.generate_provisional_proposals_coco()
        print(f"Provisional Proposals Generated: {len(props)}")

    if args.generate_cvat:
        exporter = CVATProjectExporter(staging_dir=staging_path)
        xml_p = exporter.export()
        print(f"CVAT XML exported to: {xml_p}")

    builder = GoldStandardBuilder(staging_dir=staging_path)

    if args.export_yolo:
        summary = builder.export_yolo_detection_ready_dataset()
        print("\n--- YOLO Gold Standard Export Summary ---")
        print(f"Total Verified Images Exported: {summary['total_verified_images']}")
        print(f"Split breakdown: {summary['split_images_count']}")
        print(f"Total BBoxes: {summary['total_boxes']}")
        print(f"Benchmark Warning: {summary['warning']}")

    # Default display status
    proposals_file = staging_path / "provisional_proposals" / "provisional_proposals.json"
    prop_count = 0
    if proposals_file.exists():
        with open(proposals_file, "r", encoding="utf-8") as f:
            prop_count = len(json.load(f).get("proposals", []))

    reviewed_count = len(builder.reviews)
    verified_boxes = sum(len(r.boxes) for r in builder.reviews.values() if r.status == "human_verified")

    print("\n" + "=" * 60)
    print("STEP 15C STAGING PILOT STATUS")
    print(f"Total Staging Images: {len(builder.manifest_samples)}")
    print(f"Provisional Proposals (Assisted): {prop_count} (All 'provisional_unreviewed')")
    print(f"Human-Reviewed Images: {reviewed_count} / {len(builder.manifest_samples)}")
    print(f"Human-Verified BBoxes: {verified_boxes}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
