#!/usr/bin/env python3
"""
scripts/validate_dataset_manifest.py

Standalone validator for TigerTraceAI dataset manifests.
Enforces structural integrity, data cleanliness, provenance, coordinate bounds,
timezone-explicit ISO-8601 timestamps, bounding box sanity, and split leakage detection.

Design Principles:
- Purely diagnostic: Never silently alters, deletes, or relabels data.
- Distinguishes structural errors (non-zero exit code) from quality warnings.
- Explicit concept distinction: 'unknown', 'missing_annotation', and 'proposed_new_individual'
  are preserved as distinct concepts.
- Produces both human-readable terminal output and machine-readable JSON reports.
"""

import os
import sys
import csv
import json
import re
import argparse
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple

# Exact 21 columns required in the standardized dataset manifest
REQUIRED_COLUMNS = [
    "sample_id",
    "dataset_name",
    "source_url",
    "relative_image_path",
    "species_label",
    "individual_id",
    "identity_label_status",
    "bbox_x_min",
    "bbox_y_min",
    "bbox_x_max",
    "bbox_y_max",
    "timestamp_utc",
    "camera_id",
    "site_id",
    "latitude",
    "longitude",
    "split",
    "license_id",
    "attribution",
    "checksum_sha256",
    "review_status",
]

# Distinct recognized identity label concepts
VALID_IDENTITY_STATUSES = {
    "confirmed_known",       # Individual identity is confirmed and mapped
    "unknown",               # Animal observed, but individual identity is unidentifiable
    "missing_annotation",    # Individual identity annotation was not performed / not available
    "proposed_new_individual", # Prospective novel individual awaiting review/approval
}

# Values treated as non-identifying sentinels when checking split leakage
UNKNOWN_IDENTITY_SENTINELS = {
    "",
    "unknown",
    "unidentified",
    "unmatched",
    "none",
    "nan",
    "null",
}

# Permitted splits
VALID_SPLITS = {"train", "val", "validation", "test", "unassigned", "holdout"}

# Permitted review statuses
VALID_REVIEW_STATUSES = {"unreviewed", "reviewed", "verified", "flagged", "rejected", "pending_review"}

# Regex for ISO-8601 timestamp with explicit UTC timezone indicator (Z or +00:00 / +0000)
ISO_UTC_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00|\+0000|-00:00|-0000)$"
)
# Regex detecting any other non-UTC timezone offset like +05:30 or -04:00
OFFSET_TIMEZONE_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?([+-]\d{2}:?\d{2})$"
)


class ManifestValidator:
    def __init__(self, dataset_root: Optional[str] = None, strict: bool = False):
        self.dataset_root = dataset_root
        self.strict = strict
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.split_leakages: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}

    def add_error(self, category: str, message: str, row_idx: Optional[int] = None, sample_id: Optional[str] = None):
        self.errors.append({
            "level": "ERROR",
            "category": category,
            "message": message,
            "row_index": row_idx,
            "sample_id": sample_id,
        })

    def add_warning(self, category: str, message: str, row_idx: Optional[int] = None, sample_id: Optional[str] = None):
        self.warnings.append({
            "level": "WARNING",
            "category": category,
            "message": message,
            "row_index": row_idx,
            "sample_id": sample_id,
        })

    def validate_file(self, manifest_path: str) -> Dict[str, Any]:
        """Validates a dataset manifest CSV file."""
        if not os.path.exists(manifest_path):
            self.add_error("file_io", f"Manifest file not found: {manifest_path}")
            return self._build_report(manifest_path, total_rows=0)

        with open(manifest_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                self.add_error("file_format", "Manifest file is empty (no header row found)")
                return self._build_report(manifest_path, total_rows=0)

        # Validate columns
        col_indices = self._validate_header(header)
        if col_indices is None:
            # Fatal column mismatch; cannot safely parse rows by column index
            return self._build_report(manifest_path, total_rows=0)

        # Parse rows
        rows: List[Dict[str, str]] = []
        with open(manifest_path, mode="r", encoding="utf-8", errors="replace") as f:
            dict_reader = csv.DictReader(f)
            for row_idx, row in enumerate(dict_reader, start=2):  # 1-indexed; row 1 is header
                rows.append(row)
                self._validate_row(row, row_idx)

        # Cross-row validations
        self._validate_sample_id_uniqueness(rows)
        self._validate_split_leakage(rows)
        self._compute_statistics(rows)

        return self._build_report(manifest_path, total_rows=len(rows))

    def _validate_header(self, header: List[str]) -> Optional[Dict[str, int]]:
        header_cleaned = [col.strip() for col in header]
        header_set = set(header_cleaned)
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in header_set]
        unexpected_cols = [c for c in header_cleaned if c not in REQUIRED_COLUMNS]

        if missing_cols:
            self.add_error("columns", f"Missing required column(s): {', '.join(missing_cols)}")
            return None

        if unexpected_cols:
            self.add_warning("columns", f"Extra / unexpected column(s) present: {', '.join(unexpected_cols)}")

        return {col: idx for idx, col in enumerate(header_cleaned)}

    def _validate_sample_id_uniqueness(self, rows: List[Dict[str, str]]):
        seen_ids: Dict[str, int] = {}
        for row_idx, row in enumerate(rows, start=2):
            sample_id = row.get("sample_id", "").strip()
            if not sample_id:
                self.add_error("sample_id", "sample_id is empty or missing", row_idx=row_idx)
                continue
            if sample_id in seen_ids:
                prev_row = seen_ids[sample_id]
                self.add_error(
                    "duplicate_sample_id",
                    f"Duplicate sample_id '{sample_id}' (first seen at row {prev_row}, repeated at row {row_idx})",
                    row_idx=row_idx,
                    sample_id=sample_id,
                )
            else:
                seen_ids[sample_id] = row_idx

    def _validate_row(self, row: Dict[str, str], row_idx: int):
        sample_id = row.get("sample_id", "").strip()

        # 1. Image path validation
        rel_img_path = row.get("relative_image_path", "").strip()
        if rel_img_path:
            if self.dataset_root:
                full_img_path = os.path.join(self.dataset_root, rel_img_path)
                if not os.path.isfile(full_img_path):
                    self.add_error(
                        "missing_image_file",
                        f"Image file does not exist at resolved path: {full_img_path}",
                        row_idx=row_idx,
                        sample_id=sample_id,
                    )
        else:
            self.add_warning(
                "image_path_empty",
                "relative_image_path is blank",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        # 2. Species label check
        species = row.get("species_label", "").strip()
        if not species:
            self.add_warning(
                "missing_species",
                "species_label is blank",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        # 3. Identity and Label Status validation
        self._validate_identity_status(row, row_idx, sample_id)

        # 4. Bounding box coordinates validation
        self._validate_bbox(row, row_idx, sample_id)

        # 5. Geocoordinates validation (lat/lon)
        self._validate_coordinates(row, row_idx, sample_id)

        # 6. Timestamp UTC validation
        self._validate_timestamp(row, row_idx, sample_id)

        # 7. Split check
        split = row.get("split", "").strip().lower()
        if split and split not in VALID_SPLITS:
            self.add_warning(
                "unrecognized_split",
                f"Unrecognized split '{split}'. Expected one of: {', '.join(sorted(VALID_SPLITS))}",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        # 8. Provenance and Licensing
        source_url = row.get("source_url", "").strip()
        license_id = row.get("license_id", "").strip()
        attribution = row.get("attribution", "").strip()
        if not source_url:
            self.add_warning("missing_provenance", "source_url is blank", row_idx=row_idx, sample_id=sample_id)
        if not license_id:
            self.add_warning("missing_license", "license_id is blank", row_idx=row_idx, sample_id=sample_id)
        if not attribution:
            self.add_warning("missing_attribution", "attribution is blank", row_idx=row_idx, sample_id=sample_id)

    def _validate_identity_status(self, row: Dict[str, str], row_idx: int, sample_id: str):
        id_status = row.get("identity_label_status", "").strip().lower()
        ind_id = row.get("individual_id", "").strip()

        if not id_status:
            self.add_warning(
                "missing_identity_status",
                "identity_label_status is blank. Must specify one of: " + ", ".join(sorted(VALID_IDENTITY_STATUSES)),
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        if id_status not in VALID_IDENTITY_STATUSES:
            self.add_error(
                "invalid_identity_status",
                f"Invalid identity_label_status '{id_status}'. Must be one of: {', '.join(sorted(VALID_IDENTITY_STATUSES))}",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        # Semantic integrity between individual_id and identity_label_status
        if id_status == "confirmed_known" and not ind_id:
            self.add_error(
                "inconsistent_identity",
                "identity_label_status is 'confirmed_known' but individual_id is empty",
                row_idx=row_idx,
                sample_id=sample_id,
            )
        elif id_status == "missing_annotation" and ind_id and ind_id.lower() not in UNKNOWN_IDENTITY_SENTINELS:
            self.add_warning(
                "inconsistent_identity",
                f"identity_label_status is 'missing_annotation' but individual_id is provided ('{ind_id}')",
                row_idx=row_idx,
                sample_id=sample_id,
            )
        elif id_status == "proposed_new_individual" and not ind_id:
            self.add_warning(
                "inconsistent_identity",
                "identity_label_status is 'proposed_new_individual' but no candidate individual_id was proposed",
                row_idx=row_idx,
                sample_id=sample_id,
            )

    def _validate_bbox(self, row: Dict[str, str], row_idx: int, sample_id: str):
        coords = [
            ("bbox_x_min", row.get("bbox_x_min", "").strip()),
            ("bbox_y_min", row.get("bbox_y_min", "").strip()),
            ("bbox_x_max", row.get("bbox_x_max", "").strip()),
            ("bbox_y_max", row.get("bbox_y_max", "").strip()),
        ]

        present = [k for k, v in coords if v != ""]
        if len(present) == 0:
            # Whole bounding box is absent -> valid image-level sample
            return

        if len(present) < 4:
            missing_names = [k for k, v in coords if v == ""]
            self.add_error(
                "partially_missing_bbox",
                f"Partially missing bounding box coordinates: {', '.join(missing_names)} are missing",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        try:
            x_min = float(coords[0][1])
            y_min = float(coords[1][1])
            x_max = float(coords[2][1])
            y_max = float(coords[3][1])
        except ValueError:
            self.add_error(
                "malformed_bbox",
                "Bounding box coordinates must be numeric floating-point values",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        if x_min < 0 or y_min < 0:
            self.add_error(
                "negative_bbox_coords",
                f"Bounding box coordinates cannot be negative: ({x_min}, {y_min}, {x_max}, {y_max})",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        if x_min >= x_max:
            self.add_error(
                "inverted_bbox_x",
                f"Invalid bounding box: bbox_x_min ({x_min}) >= bbox_x_max ({x_max})",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        if y_min >= y_max:
            self.add_error(
                "inverted_bbox_y",
                f"Invalid bounding box: bbox_y_min ({y_min}) >= bbox_y_max ({y_max})",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        # If coords appear to be normalized ([0, 1]) check bounds
        if max(x_min, y_min, x_max, y_max) <= 1.0:
            if x_max > 1.0 or y_max > 1.0:
                self.add_error(
                    "normalized_bbox_out_of_bounds",
                    f"Normalized bounding box coordinate exceeds 1.0: ({x_min}, {y_min}, {x_max}, {y_max})",
                    row_idx=row_idx,
                    sample_id=sample_id,
                )

    def _validate_coordinates(self, row: Dict[str, str], row_idx: int, sample_id: str):
        lat_str = row.get("latitude", "").strip()
        lon_str = row.get("longitude", "").strip()

        if not lat_str and not lon_str:
            return

        if bool(lat_str) != bool(lon_str):
            self.add_error(
                "partially_missing_coordinates",
                "One of latitude or longitude is provided while the other is blank",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            self.add_error(
                "malformed_coordinates",
                f"Latitude ('{lat_str}') or Longitude ('{lon_str}') is not a valid number",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        if not (-90.0 <= lat <= 90.0):
            self.add_error(
                "latitude_out_of_range",
                f"Latitude {lat} out of valid range [-90.0, 90.0]",
                row_idx=row_idx,
                sample_id=sample_id,
            )

        if not (-180.0 <= lon <= 180.0):
            self.add_error(
                "longitude_out_of_range",
                f"Longitude {lon} out of valid range [-180.0, 180.0]",
                row_idx=row_idx,
                sample_id=sample_id,
            )

    def _validate_timestamp(self, row: Dict[str, str], row_idx: int, sample_id: str):
        ts_str = row.get("timestamp_utc", "").strip()
        if not ts_str:
            return

        # Check for strict ISO UTC designation
        if ISO_UTC_REGEX.match(ts_str):
            # Parse to ensure valid calendar day and time (e.g., month <= 12, day <= 31)
            clean_ts = ts_str.rstrip("Z").replace("+00:00", "").replace("+0000", "").replace("-00:00", "").replace("-0000", "")
            try:
                datetime.fromisoformat(clean_ts)
            except ValueError as e:
                self.add_error(
                    "unparseable_timestamp",
                    f"Invalid calendar date/time in timestamp '{ts_str}': {e}",
                    row_idx=row_idx,
                    sample_id=sample_id,
                )
            return

        # Non-UTC timezone offset found
        match = OFFSET_TIMEZONE_REGEX.match(ts_str)
        if match:
            offset = match.group(1)
            self.add_error(
                "non_utc_timezone",
                f"Timestamp '{ts_str}' has non-UTC timezone offset '{offset}'. timestamp_utc must be converted to UTC.",
                row_idx=row_idx,
                sample_id=sample_id,
            )
            return

        # Timestamp lacks any explicit timezone offset
        self.add_error(
            "unverified_timezone",
            f"Timestamp '{ts_str}' lacks an explicit UTC timezone indicator ('Z' or '+00:00'). "
            "Do not silently assume a local or UTC timezone.",
            row_idx=row_idx,
            sample_id=sample_id,
        )

    def _validate_split_leakage(self, rows: List[Dict[str, str]]):
        """
        Detects individuals appearing across multiple splits within the same dataset.
        Split leakage can severely invalidate Re-ID benchmarking evaluations.
        """
        # Mapping: (dataset_name, individual_id) -> dict(splits -> list of sample_ids)
        individual_splits: Dict[Tuple[str, str], Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

        for row in rows:
            dataset_name = row.get("dataset_name", "").strip()
            individual_id = row.get("individual_id", "").strip()
            split = row.get("split", "").strip().lower()
            sample_id = row.get("sample_id", "").strip()

            if not individual_id or individual_id.lower() in UNKNOWN_IDENTITY_SENTINELS:
                continue
            if not split:
                split = "unassigned"

            individual_splits[(dataset_name, individual_id)][split].append(sample_id)

        for (dataset_name, individual_id), splits_map in individual_splits.items():
            active_splits = set(splits_map.keys()) - {"unassigned"}
            if len(active_splits) > 1:
                leakage_info = {
                    "dataset_name": dataset_name,
                    "individual_id": individual_id,
                    "splits_involved": sorted(list(active_splits)),
                    "sample_counts_per_split": {s: len(s_ids) for s, s_ids in splits_map.items() if s in active_splits},
                    "sample_ids_sample": {s: s_ids[:3] for s, s_ids in splits_map.items() if s in active_splits},
                }
                self.split_leakages.append(leakage_info)
                self.add_warning(
                    "split_leakage",
                    f"Individual '{individual_id}' in dataset '{dataset_name}' appears in multiple splits: {', '.join(sorted(active_splits))}",
                    sample_id=", ".join(splits_map[list(active_splits)[0]][:2]),
                )

    def _compute_statistics(self, rows: List[Dict[str, str]]):
        """Computes per-dataset and per-species split statistics."""
        dataset_splits: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        species_splits: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        dataset_species_splits: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        individual_counts: Dict[str, Set[str]] = defaultdict(set)

        for row in rows:
            ds = row.get("dataset_name", "").strip() or "unnamed_dataset"
            sp = row.get("species_label", "").strip() or "unspecified_species"
            split = row.get("split", "").strip().lower() or "unassigned"
            ind_id = row.get("individual_id", "").strip()

            dataset_splits[ds][split] += 1
            species_splits[sp][split] += 1
            dataset_species_splits[ds][sp][split] += 1

            if ind_id and ind_id.lower() not in UNKNOWN_IDENTITY_SENTINELS:
                individual_counts[ds].add(ind_id)

        self.stats = {
            "total_samples": len(rows),
            "per_dataset_splits": {ds: dict(splits) for ds, splits in dataset_splits.items()},
            "per_species_splits": {sp: dict(splits) for sp, splits in species_splits.items()},
            "dataset_species_splits": {
                ds: {sp: dict(splits) for sp, splits in sp_map.items()}
                for ds, sp_map in dataset_species_splits.items()
            },
            "unique_individuals_per_dataset": {ds: len(inds) for ds, inds in individual_counts.items()},
        }

    def _build_report(self, manifest_path: str, total_rows: int) -> Dict[str, Any]:
        is_valid = len(self.errors) == 0
        if self.strict and len(self.warnings) > 0:
            is_valid = False

        return {
            "manifest_path": os.path.abspath(manifest_path),
            "dataset_root": os.path.abspath(self.dataset_root) if self.dataset_root else None,
            "total_samples": total_rows,
            "is_valid": is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "split_leakage_count": len(self.split_leakages),
            "errors": self.errors,
            "warnings": self.warnings,
            "split_leakages": self.split_leakages,
            "statistics": self.stats,
        }

    def format_human_report(self, report: Dict[str, Any]) -> str:
        """Formats the validation report into clean human-readable terminal text."""
        lines = []
        lines.append("=" * 80)
        lines.append("           TIGERTRACE AI - DATASET MANIFEST VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Manifest File : {report['manifest_path']}")
        lines.append(f"Dataset Root  : {report['dataset_root'] or 'None (relative paths not checked against disk)'}")
        lines.append(f"Total Samples : {report['total_samples']}")
        lines.append(f"Overall Status: {'PASSED' if report['is_valid'] else 'FAILED'}")
        lines.append(f"Errors Found  : {report['error_count']}")
        lines.append(f"Warnings Found: {report['warning_count']}")
        lines.append("-" * 80)

        # 1. Structural Errors
        if report["errors"]:
            lines.append("\n[ERROR] STRUCTURAL ERRORS (Must be resolved):")
            for idx, err in enumerate(report["errors"][:50], start=1):
                loc = f"Row {err['row_index']}" if err.get("row_index") else "Header/Global"
                sid = f" [Sample: {err['sample_id']}]" if err.get("sample_id") else ""
                lines.append(f"  {idx:02d}. ({err['category'].upper()}) {loc}{sid}: {err['message']}")
            if len(report["errors"]) > 50:
                lines.append(f"  ... and {len(report['errors']) - 50} additional errors.")
        else:
            lines.append("\n[OK] No structural errors detected.")

        # 2. Quality Warnings
        if report["warnings"]:
            lines.append("\n[WARNING] QUALITY WARNINGS:")
            for idx, w in enumerate(report["warnings"][:30], start=1):
                loc = f"Row {w['row_index']}" if w.get("row_index") else "Global"
                lines.append(f"  {idx:02d}. ({w['category'].upper()}) {loc}: {w['message']}")
            if len(report["warnings"]) > 30:
                lines.append(f"  ... and {len(report['warnings']) - 30} additional warnings.")

        # 3. Split Leakage Warnings
        if report["split_leakages"]:
            lines.append("\n[SPLIT LEAKAGE] WARNINGS (Re-ID Benchmark Contamination Risk):")
            for leak in report["split_leakages"][:10]:
                splits_str = ", ".join(leak["splits_involved"])
                lines.append(f"  - Dataset '{leak['dataset_name']}': Individual '{leak['individual_id']}' in splits [{splits_str}]")
                for s, count in leak["sample_counts_per_split"].items():
                    lines.append(f"      * {s}: {count} samples")

        # 4. Dataset & Species Split Statistics
        stats = report.get("statistics", {})
        if stats.get("per_dataset_splits"):
            lines.append("\n" + "-" * 80)
            lines.append("DATASET & SPLIT SUMMARY STATISTICS")
            lines.append("-" * 80)
            for ds, sp_map in stats["per_dataset_splits"].items():
                inds_count = stats.get("unique_individuals_per_dataset", {}).get(ds, 0)
                lines.append(f"\nDataset: {ds} (Unique Individuals: {inds_count})")
                for split_name, count in sorted(sp_map.items()):
                    lines.append(f"  - Split '{split_name}': {count} samples")

        if stats.get("per_species_splits"):
            lines.append("\nSpecies Representation across Splits:")
            for sp, split_counts in stats["per_species_splits"].items():
                split_summary = ", ".join([f"{k}: {v}" for k, v in sorted(split_counts.items())])
                lines.append(f"  - {sp}: {split_summary}")

        lines.append("\n" + "=" * 80)
        lines.append("END OF MANIFEST AUDIT REPORT")
        lines.append("=" * 80 + "\n")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate wildlife dataset manifests for TigerTraceAI."
    )
    parser.add_argument(
        "--manifest",
        "-m",
        required=True,
        help="Path to dataset_manifest.csv file to validate.",
    )
    parser.add_argument(
        "--dataset-root",
        "-r",
        default=None,
        help="Root directory where image files are stored to verify image path existence.",
    )
    parser.add_argument(
        "--json-output",
        "-j",
        default=None,
        help="Optional path to write the structured JSON validation report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail validation with non-zero exit code on warnings as well as errors.",
    )

    args = parser.parse_args()

    validator = ManifestValidator(dataset_root=args.dataset_root, strict=args.strict)
    report = validator.validate_file(args.manifest)

    # Print human-readable report to stdout
    print(validator.format_human_report(report))

    # Optional JSON output
    if args.json_output:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_output)), exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as jf:
            json.dump(report, jf, indent=2)
        print(f"[JSON REPORT] Saved structured audit results to: {args.json_output}")

    # Return exit code: 0 if valid, 1 if structural errors (or warnings in strict mode)
    if not report["is_valid"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
