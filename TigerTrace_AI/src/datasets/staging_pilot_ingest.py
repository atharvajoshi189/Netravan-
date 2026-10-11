"""
TigerTraceAI — Step 15B: Lightweight Wildlife Dataset Staging Pilot Ingestion Engine.

Handles isolated, safe ingestion and validation of public wildlife candidate data
for priority prey species (Chital, Sambar, Gaur, Nilgai).

Enforces:
1. Hard download size budget (100–200 MB configurable).
2. License verification and provenance tracking.
3. Image decoding, dimension, and checksum duplicate validation.
4. Strict separation of bounding-box detection vs. image-level occurrence data.
5. Encounter grouping to prevent camera sequence data leakage.
6. Zero alteration of production database, canonical manifests, or checkpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("staging_pilot_ingest")


# Default 4 priority prey species mapped to canonical taxonomy
PRIORITY_SPECIES = ["chital", "sambar", "gaur", "nilgai"]


@dataclass
class StagingSampleRecord:
    sample_id: str
    source_dataset: str
    source_url: str
    photo_id: str
    observation_id: str
    canonical_class_id: int
    canonical_class_name: str
    source_species_label: str
    scientific_name: str
    license_code: str
    license_permissive: bool
    attribution: str
    encounter_group_id: str
    observed_date: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    relative_file_path: Optional[str]
    checksum_sha256: str
    width_px: int
    height_px: int
    has_bounding_box: bool
    bbox_annotations: List[Dict[str, Any]]
    detection_ready: bool
    training_readiness: str
    status: str
    rejection_reason: Optional[str] = None


@dataclass
class StagingValidationReport:
    manifest_version: str = "1.0.0"
    created_at_utc: str = ""
    staging_directory: str = ""
    max_download_budget_bytes: int = 0
    max_download_budget_mb: float = 0.0
    actual_downloaded_bytes: int = 0
    actual_downloaded_mb: float = 0.0
    budget_exceeded: bool = False
    dry_run: bool = False
    total_queried: int = 0
    total_valid_ingested: int = 0
    total_rejected: int = 0
    species_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    detection_ready_count: int = 0
    image_level_only_count: int = 0
    rejection_summary: Dict[str, int] = field(default_factory=dict)
    licenses_used: Dict[str, int] = field(default_factory=dict)
    remaining_data_gaps: List[str] = field(default_factory=list)


class WildlifeStagingIngester:
    def __init__(
        self,
        taxonomy_path: Path,
        output_dir: Path,
        max_download_mb: float = 150.0,
        samples_per_species: int = 15,
        target_species: Optional[List[str]] = None,
        dry_run: bool = False,
        request_timeout: int = 15,
    ):
        self.taxonomy_path = Path(taxonomy_path)
        self.output_dir = Path(output_dir)
        self.max_download_bytes = int(max_download_mb * 1024 * 1024)
        self.max_download_mb = max_download_mb
        self.samples_per_species = samples_per_species
        self.target_species = target_species or PRIORITY_SPECIES
        self.dry_run = dry_run
        self.request_timeout = request_timeout

        self.downloaded_bytes: int = 0
        self.seen_checksums: Set[str] = set()
        self.seen_photo_ids: Set[str] = set()

        self.valid_samples: List[StagingSampleRecord] = []
        self.rejected_samples: List[StagingSampleRecord] = []
        self.rejection_counts: Dict[str, int] = {}
        self.license_counts: Dict[str, int] = {}

        self.taxonomy: Dict[str, Any] = self._load_taxonomy()
        self.species_map: Dict[str, Dict[str, Any]] = self._build_species_map()

        # Output folder hierarchy
        self.images_dir = self.output_dir / "images"
        self.manifests_dir = self.output_dir / "manifests"
        self.detection_ready_dir = self.output_dir / "detection_ready"
        self.image_level_dir = self.output_dir / "image_level_inventory"

    def _load_taxonomy(self) -> Dict[str, Any]:
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy configuration not found at {self.taxonomy_path}")
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_species_map(self) -> Dict[str, Dict[str, Any]]:
        s_map = {}
        for c in self.taxonomy.get("classes", []):
            name = c["canonical_name"].lower()
            s_map[name] = {
                "canonical_id": c["canonical_id"],
                "canonical_name": c["canonical_name"],
                "display_name": c["display_name"],
                "scientific_name": c["scientific_name"],
                "aliases": [a.lower() for a in c.get("aliases", [])],
            }
        return s_map

    def _prepare_directories(self) -> None:
        if not self.dry_run:
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.manifests_dir.mkdir(parents=True, exist_ok=True)
            self.detection_ready_dir.mkdir(parents=True, exist_ok=True)
            self.image_level_dir.mkdir(parents=True, exist_ok=True)

    def query_inaturalist_species(self, species_name: str, limit: int) -> List[Dict[str, Any]]:
        """Queries the official iNaturalist REST API for verified, licensed observations."""
        species_info = self.species_map.get(species_name.lower())
        if not species_info:
            logger.error(f"Species '{species_name}' not found in canonical taxonomy.")
            return []

        sci_name = species_info["scientific_name"]
        encoded_sci_name = urllib.parse.quote_plus(sci_name)
        # Fetch research-grade, licensed observations with photos
        # Request twice the target limit to account for possible corrupt/duplicate filtering
        per_page = min(limit * 2, 50)
        url = (
            f"https://api.inaturalist.org/v1/observations?"
            f"taxon_name={encoded_sci_name}&quality_grade=research&licensed=true&photos=true&per_page={per_page}"
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "TigerTraceAI-StagingPilot/1.0 (Wildlife Research & Conservation)",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                logger.info(
                    f"Retrieved {len(results)} candidate observations for '{species_name}' ({sci_name}) from iNaturalist."
                )
                return results
        except Exception as e:
            logger.error(f"Failed to query iNaturalist API for '{species_name}': {e}")
            return []

    def validate_and_ingest_image_bytes(
        self,
        raw_bytes: bytes,
        target_path: Path,
        expected_species: str,
    ) -> Tuple[bool, Optional[str], int, int, str]:
        """
        Validates raw image bytes:
        - Checks image decoding via OpenCV
        - Verifies dimensions >= 128x128
        - Computes SHA256
        - Checks for duplicate checksums
        """
        if not raw_bytes:
            return False, "empty_image_payload", 0, 0, ""

        sha256 = hashlib.sha256(raw_bytes).hexdigest()

        if sha256 in self.seen_checksums:
            return False, "duplicate_image_checksum", 0, 0, sha256

        # Decode image
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return False, "corrupt_unreadable_image", 0, 0, sha256

        height, width = img.shape[:2]
        if width < 128 or height < 128:
            return False, f"image_dimensions_below_threshold_{width}x{height}", width, height, sha256

        # Check existing file to prevent silent overwrite
        if not self.dry_run:
            if target_path.exists():
                return False, "target_file_already_exists_no_silent_overwrite", width, height, sha256
            with open(target_path, "wb") as f:
                f.write(raw_bytes)

        self.seen_checksums.add(sha256)
        return True, None, width, height, sha256

    def ingest_single_observation(
        self,
        obs: Dict[str, Any],
        species_name: str,
    ) -> Optional[StagingSampleRecord]:
        """Processes an observation, verifies license, provenance, and annotations."""
        species_info = self.species_map[species_name]
        obs_id = str(obs.get("id"))
        photos = obs.get("photos", [])

        if not photos:
            self._record_rejection("no_photos_in_observation")
            return None

        photo = photos[0]
        photo_id = str(photo.get("id"))

        if photo_id in self.seen_photo_ids:
            self._record_rejection("duplicate_photo_id")
            return None
        self.seen_photo_ids.add(photo_id)

        # License verification
        license_code = (
            photo.get("license_code")
            or obs.get("license_code")
            or "unknown"
        ).lower()

        # Check permissive status
        # Permissive: cc0, cc-by, cc-by-nc, cc-by-sa, cc-by-nc-sa
        permissive = license_code in ["cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"]
        if not permissive:
            self._record_rejection(f"unpermitted_license_{license_code}")
            return None

        self.license_counts[license_code] = self.license_counts.get(license_code, 0) + 1

        # Attribution & Metadata
        attribution = photo.get("attribution") or obs.get("user", {}).get("login", "Unknown Observer")
        observed_date = obs.get("observed_on") or obs.get("time_observed_at", "")[:10]
        user_id = str(obs.get("user", {}).get("id", "0"))
        encounter_group_id = f"enc_user{user_id}_{observed_date or 'undated'}"

        geojson = obs.get("geojson", {})
        coords = geojson.get("coordinates") if geojson else None
        longitude = coords[0] if coords and len(coords) >= 2 else None
        latitude = coords[1] if coords and len(coords) >= 2 else None

        # Build medium image URL (high resolution without 20MB raw file overhead)
        orig_url = photo.get("url", "")
        if "square" in orig_url:
            img_url = orig_url.replace("square", "medium")
        else:
            img_url = orig_url

        if not img_url:
            self._record_rejection("missing_photo_url")
            return None

        # Detection vs Image-Level Analysis
        # Check if iNaturalist has genuine bounding boxes (e.g., in annotations or flags)
        raw_annotations = obs.get("annotations", [])
        has_bbox = False
        bboxes: List[Dict[str, Any]] = []

        # iNaturalist annotations are biological phenology flags, NOT bounding boxes
        for anno in raw_annotations:
            if "bbox" in anno or "bounding_box" in anno:
                has_bbox = True
                bboxes.append(anno)

        detection_ready = has_bbox
        training_readiness = (
            "DETECTION_READY"
            if detection_ready
            else "NOT_READY_FOR_DETECTION_TRAINING_IMAGE_LEVEL_ONLY"
        )

        sample_id = f"inat_{obs_id}_{photo_id}"
        file_name = f"{sample_id}.jpg"
        target_path = self.images_dir / file_name

        # Dry run simulation
        if self.dry_run:
            simulated_bytes = 350 * 1024  # Estimate ~350 KB per medium JPEG
            if self.downloaded_bytes + simulated_bytes > self.max_download_bytes:
                self._record_rejection("download_budget_exceeded")
                return None
            self.downloaded_bytes += simulated_bytes
            return StagingSampleRecord(
                sample_id=sample_id,
                source_dataset="iNaturalist Open Data",
                source_url=img_url,
                photo_id=photo_id,
                observation_id=obs_id,
                canonical_class_id=species_info["canonical_id"],
                canonical_class_name=species_info["canonical_name"],
                source_species_label=obs.get("taxon", {}).get("name", species_info["scientific_name"]),
                scientific_name=species_info["scientific_name"],
                license_code=license_code,
                license_permissive=permissive,
                attribution=attribution,
                encounter_group_id=encounter_group_id,
                observed_date=observed_date,
                latitude=latitude,
                longitude=longitude,
                relative_file_path=f"images/{file_name}",
                checksum_sha256="dry_run_simulated_checksum",
                width_px=800,
                height_px=600,
                has_bounding_box=has_bbox,
                bbox_annotations=bboxes,
                detection_ready=detection_ready,
                training_readiness=training_readiness,
                status="valid_staged_dry_run",
            )

        # Actual Download with Budget Enforcement
        try:
            req = urllib.request.Request(
                img_url,
                headers={"User-Agent": "TigerTraceAI-StagingPilot/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                content_len_hdr = resp.headers.get("Content-Length")
                if content_len_hdr:
                    expected_len = int(content_len_hdr)
                    if self.downloaded_bytes + expected_len > self.max_download_bytes:
                        self._record_rejection(
                            f"download_budget_exceeded_{self.downloaded_bytes + expected_len}_gt_{self.max_download_bytes}"
                        )
                        return None

                raw_bytes = resp.read()

                if self.downloaded_bytes + len(raw_bytes) > self.max_download_bytes:
                    self._record_rejection("download_budget_exceeded")
                    return None

                self.downloaded_bytes += len(raw_bytes)

        except Exception as e:
            self._record_rejection(f"download_network_error_{str(e)[:40]}")
            return None

        # Image Validation
        is_valid, rej_reason, width, height, sha256 = self.validate_and_ingest_image_bytes(
            raw_bytes=raw_bytes,
            target_path=target_path,
            expected_species=species_name,
        )

        if not is_valid:
            self._record_rejection(rej_reason or "validation_failed")
            return None

        record = StagingSampleRecord(
            sample_id=sample_id,
            source_dataset="iNaturalist Open Data",
            source_url=img_url,
            photo_id=photo_id,
            observation_id=obs_id,
            canonical_class_id=species_info["canonical_id"],
            canonical_class_name=species_info["canonical_name"],
            source_species_label=obs.get("taxon", {}).get("name", species_info["scientific_name"]),
            scientific_name=species_info["scientific_name"],
            license_code=license_code,
            license_permissive=permissive,
            attribution=attribution,
            encounter_group_id=encounter_group_id,
            observed_date=observed_date,
            latitude=latitude,
            longitude=longitude,
            relative_file_path=f"images/{file_name}",
            checksum_sha256=sha256,
            width_px=width,
            height_px=height,
            has_bounding_box=has_bbox,
            bbox_annotations=bboxes,
            detection_ready=detection_ready,
            training_readiness=training_readiness,
            status="valid_staged",
        )

        return record

    def _record_rejection(self, reason: str) -> None:
        self.rejection_counts[reason] = self.rejection_counts.get(reason, 0) + 1

    def run_staging_pilot(self) -> StagingValidationReport:
        """Executes the staging pilot across the requested priority species."""
        start_time = time.time()
        logger.info(
            f"Starting Step 15B Wildlife Staging Pilot. Target species: {self.target_species}, "
            f"Budget limit: {self.max_download_mb:.1f} MB, Dry-run: {self.dry_run}"
        )

        self._prepare_directories()
        species_breakdown: Dict[str, Dict[str, int]] = {}

        for sp in self.target_species:
            sp_key = sp.lower()
            if sp_key not in self.species_map:
                logger.warning(f"Skipping unknown species: {sp}")
                continue

            species_breakdown[sp_key] = {"queried": 0, "valid_ingested": 0, "rejected": 0, "detection_ready": 0}
            candidates = self.query_inaturalist_species(sp_key, self.samples_per_species)
            species_breakdown[sp_key]["queried"] = len(candidates)

            for cand in candidates:
                if species_breakdown[sp_key]["valid_ingested"] >= self.samples_per_species:
                    break

                # Check budget before proceeding
                if self.downloaded_bytes >= self.max_download_bytes:
                    logger.warning(f"Download budget limit reached ({self.downloaded_bytes} bytes). Halting ingestion.")
                    self._record_rejection("download_budget_exceeded")
                    break

                record = self.ingest_single_observation(cand, sp_key)
                if record:
                    self.valid_samples.append(record)
                    species_breakdown[sp_key]["valid_ingested"] += 1
                    if record.detection_ready:
                        species_breakdown[sp_key]["detection_ready"] += 1
                else:
                    species_breakdown[sp_key]["rejected"] += 1

                # Polite pause to avoid hitting public API rate limits
                if not self.dry_run:
                    time.sleep(0.1)

        # Assemble and write manifest and reports
        report = self._generate_report(species_breakdown)
        if not self.dry_run:
            self._save_manifest_and_reports(report)

        logger.info(
            f"Staging pilot finished in {time.time() - start_time:.2f}s. "
            f"Valid samples: {len(self.valid_samples)}, Detection-ready: {report.detection_ready_count}, "
            f"Downloaded: {report.actual_downloaded_mb:.2f} MB"
        )
        return report

    def _generate_report(self, species_breakdown: Dict[str, Dict[str, int]]) -> StagingValidationReport:
        downloaded_mb = self.downloaded_bytes / (1024 * 1024)
        det_ready = sum(1 for s in self.valid_samples if s.detection_ready)
        img_level = sum(1 for s in self.valid_samples if not s.detection_ready)

        data_gaps: List[str] = []
        for sp in self.target_species:
            stats = species_breakdown.get(sp.lower(), {})
            det_count = stats.get("detection_ready", 0)
            valid_count = stats.get("valid_ingested", 0)

            if det_count == 0:
                data_gaps.append(
                    f"Species '{sp}': {valid_count} image-level samples ingested, but ZERO genuine bounding-box annotations exist. Cannot train YOLO detector."
                )

        report = StagingValidationReport(
            manifest_version="1.0.0",
            created_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            staging_directory=str(self.output_dir),
            max_download_budget_bytes=self.max_download_bytes,
            max_download_budget_mb=self.max_download_mb,
            actual_downloaded_bytes=self.downloaded_bytes,
            actual_downloaded_mb=round(downloaded_mb, 2),
            budget_exceeded=self.downloaded_bytes > self.max_download_bytes,
            dry_run=self.dry_run,
            total_queried=sum(s.get("queried", 0) for s in species_breakdown.values()),
            total_valid_ingested=len(self.valid_samples),
            total_rejected=sum(self.rejection_counts.values()),
            species_breakdown=species_breakdown,
            detection_ready_count=det_ready,
            image_level_only_count=img_level,
            rejection_summary=self.rejection_counts,
            licenses_used=self.license_counts,
            remaining_data_gaps=data_gaps,
        )
        return report

    def _save_manifest_and_reports(self, report: StagingValidationReport) -> None:
        # 1. Manifest
        manifest_payload = {
            "manifest_version": "1.0.0",
            "created_at_utc": report.created_at_utc,
            "taxonomy_version": self.taxonomy.get("taxonomy_version", "1.0.0"),
            "dataset_metadata": {
                "dataset_id": "staging_wildlife_prey_pilot_15b",
                "source_name": "iNaturalist Open Data",
                "source_url": "https://api.inaturalist.org/v1/observations",
                "license": "Creative Commons (CC-BY, CC-BY-NC, CC0)",
                "geographic_region": "Global & Indian Subcontinent",
                "is_camera_trap": False,
                "curator": "TigerTraceAI Staging Pilot",
            },
            "samples": [asdict(s) for s in self.valid_samples],
        }

        manifest_path = self.manifests_dir / "staging_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_payload, f, indent=2)

        # 2. Validation report JSON
        report_path = self.manifests_dir / "staging_validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2)

        # 3. Human-readable Markdown summary
        summary_md_path = self.manifests_dir / "staging_summary.md"
        with open(summary_md_path, "w", encoding="utf-8") as f:
            f.write(self._format_markdown_summary(report))

        # 4. Separate Inventory Lists
        image_level_inventory_path = self.image_level_dir / "image_level_inventory.json"
        with open(image_level_inventory_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "warning": "CRITICAL: These images contain taxon occurrences only. ZERO bounding-box coordinates exist. NOT ready for detection training.",
                    "samples": [asdict(s) for s in self.valid_samples if not s.detection_ready],
                },
                f,
                indent=2,
            )

        det_ready_inventory_path = self.detection_ready_dir / "detection_ready_inventory.json"
        with open(det_ready_inventory_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "info": "Detection-ready samples containing verified bounding boxes.",
                    "samples": [asdict(s) for s in self.valid_samples if s.detection_ready],
                },
                f,
                indent=2,
            )

    def _format_markdown_summary(self, r: StagingValidationReport) -> str:
        md = [
            "# Wildlife Dataset Staging Pilot — Validation Summary",
            "",
            f"- **Execution Time:** `{r.created_at_utc}`",
            f"- **Staging Directory:** `{r.staging_directory}`",
            f"- **Download Budget:** `{r.max_download_budget_mb:.1f} MB` (Actual: `{r.actual_downloaded_mb:.2f} MB`)",
            f"- **Total Ingested Samples:** `{r.total_valid_ingested}`",
            f"- **Detection-Ready Bounding-Box Samples:** `{r.detection_ready_count}`",
            f"- **Image-Level Only (No BBox) Samples:** `{r.image_level_only_count}`",
            "",
            "## Per-Species Ingestion Breakdown",
            "",
            "| Species | Queried | Ingested | Detection Ready (BBoxes) | Image-Level Only | Status |",
            "|---|:---:|:---:|:---:|:---:|---|",
        ]
        for sp, stats in r.species_breakdown.items():
            valid = stats.get("valid_ingested", 0)
            det = stats.get("detection_ready", 0)
            img_lvl = valid - det
            status = "Image-Level Only (No BBox)" if det == 0 else "Detection Ready"
            md.append(f"| `{sp}` | {stats.get('queried', 0)} | {valid} | **{det}** | {img_lvl} | {status} |")

        md.extend([
            "",
            "## Verified Licenses",
            "",
        ])
        for lic, count in r.licenses_used.items():
            md.append(f"- **{lic.upper()}**: {count} samples")

        if r.rejection_summary:
            md.extend([
                "",
                "## Rejection Summary",
                "",
            ])
            for reason, count in r.rejection_summary.items():
                md.append(f"- `{reason}`: {count}")

        md.extend([
            "",
            "## Critical Data Gaps & Training Readiness",
            "",
        ])
        for gap in r.remaining_data_gaps:
            md.append(f"> [!WARNING]\n> {gap}\n")

        md.append(
            "\n### Honest Assessment\n"
            "None of the 4 priority species are ready for YOLO detection training because iNaturalist "
            "records do not provide object bounding boxes. Bounding boxes must either be manually annotated "
            "or sourced through formal institutional camera-trap agreements (such as WCT Central India)."
        )
        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="TigerTraceAI Step 15B Staging Pilot Ingestion Engine")
    parser.add_argument(
        "--taxonomy",
        type=str,
        default="TigerTrace_AI/data/taxonomy/species_taxonomy.json",
        help="Path to species_taxonomy.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="TigerTrace_AI/data/staging_wildlife_pilot",
        help="Output isolated staging directory",
    )
    parser.add_argument(
        "--max-mb",
        type=float,
        default=150.0,
        help="Hard download limit in megabytes (default: 150.0 MB)",
    )
    parser.add_argument(
        "--samples-per-species",
        type=int,
        default=12,
        help="Max target samples per species",
    )
    parser.add_argument(
        "--species",
        nargs="+",
        default=PRIORITY_SPECIES,
        help="Target species list (default: chital sambar gaur nilgai)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving files or downloading images",
    )

    args = parser.parse_args()

    ingester = WildlifeStagingIngester(
        taxonomy_path=Path(args.taxonomy),
        output_dir=Path(args.output_dir),
        max_download_mb=args.max_mb,
        samples_per_species=args.samples_per_species,
        target_species=args.species,
        dry_run=args.dry_run,
    )

    report = ingester.run_staging_pilot()
    print("\n" + "=" * 60)
    print("STAGING PILOT COMPLETE")
    print(f"Total Valid Ingested: {report.total_valid_ingested}")
    print(f"Downloaded MB: {report.actual_downloaded_mb:.2f} MB / {report.max_download_budget_mb:.1f} MB")
    print(f"Detection-Ready Samples (with BBoxes): {report.detection_ready_count}")
    print(f"Image-Level Only Samples: {report.image_level_only_count}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
