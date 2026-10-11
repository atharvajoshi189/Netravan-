# Wildlife Dataset Staging Pilot — Validation Summary

- **Execution Time:** `2026-10-10T20:49:23Z`
- **Staging Directory:** `TigerTrace_AI\data\staging_wildlife_pilot`
- **Download Budget:** `150.0 MB` (Actual: `6.31 MB`)
- **Total Ingested Samples:** `40`
- **Detection-Ready Bounding-Box Samples:** `0`
- **Image-Level Only (No BBox) Samples:** `40`

## Per-Species Ingestion Breakdown

| Species | Queried | Ingested | Detection Ready (BBoxes) | Image-Level Only | Status |
|---|:---:|:---:|:---:|:---:|---|
| `chital` | 20 | 10 | **0** | 10 | Image-Level Only (No BBox) |
| `sambar` | 20 | 10 | **0** | 10 | Image-Level Only (No BBox) |
| `gaur` | 20 | 10 | **0** | 10 | Image-Level Only (No BBox) |
| `nilgai` | 20 | 10 | **0** | 10 | Image-Level Only (No BBox) |

## Verified Licenses

- **CC-BY-NC**: 36 samples
- **CC-BY**: 4 samples

## Critical Data Gaps & Training Readiness

> [!WARNING]
> Species 'chital': 10 image-level samples ingested, but ZERO genuine bounding-box annotations exist. Cannot train YOLO detector.

> [!WARNING]
> Species 'sambar': 10 image-level samples ingested, but ZERO genuine bounding-box annotations exist. Cannot train YOLO detector.

> [!WARNING]
> Species 'gaur': 10 image-level samples ingested, but ZERO genuine bounding-box annotations exist. Cannot train YOLO detector.

> [!WARNING]
> Species 'nilgai': 10 image-level samples ingested, but ZERO genuine bounding-box annotations exist. Cannot train YOLO detector.


### Honest Assessment
None of the 4 priority species are ready for YOLO detection training because iNaturalist records do not provide object bounding boxes. Bounding boxes must either be manually annotated or sourced through formal institutional camera-trap agreements (such as WCT Central India).