# TigerTrace_AI Project Context

This file is a compact but complete handoff for ChatGPT or Claude. It summarizes the project structure, architecture, dataset, pipeline, and the main implementation files so the project can be understood without opening every source file.

## 1. Project Summary

TigerTrace_AI is an offline, CPU-first camera trap triage and individual tiger movement intelligence system built for Pench Tiger Reserve and the Maharashtra Government hackathon context. The system processes raw SD card image drops, removes blank frames, blurs humans for privacy, extracts tiger flank crops, performs stripe-based re-identification, stores everything in SQLite, generates occupancy maps, and raises behavior/deviation alerts for forest management.

The implementation is split into a production package at `TigerTrace_AI/` plus a dataset and documentation layer at the repository root.

## 2. High-Level Architecture

The pipeline is organized into four phases:

1. Phase 1: Ingest raw camera trap images, detect blank frames, quarantine blanks, and blur human subjects.
2. Phase 2: Extract tiger flank crops, match stripe patterns, auto-match or auto-enroll individuals, and persist sightings to SQLite.
3. Phase 3: Compute home ranges with Minimum Convex Polygon logic and generate an interactive Folium map of Pench.
4. Phase 4: Detect movement deviations such as village proximity, centroid shifts, novel stations, and prolonged absence, then export management briefings.

Core flow:

Raw SD card folder -> SDCardLoader -> Triage detector -> Quarantine or privacy blur -> Flank crop extraction -> Tiger Re-ID and enrollment -> SQLite persistence -> Home range / occupancy map -> Alert engine -> Markdown report

## 3. Repository Structure

Top-level layout:

- `TigerTrace_AI/`: Main application package.
- `dataset/`: Prepared training and verification artifacts.
- `DATASET_README.md`: Dataset breakdown and class counts.
- `PROJECT_SUMMARY_AND_PROGRESS.txt`: Long-form project narrative, implementation notes, and verification history.
- `README.md`: Main project overview and quick start.

Inside `TigerTrace_AI/`:

- `run_demo.py`: CLI demo runner for the full pipeline.
- `setup_and_seed_data.py`: Seeds reference catalogue and GIS station/village data.
- `src/pipeline.py`: Unified orchestrator for all phases.
- `src/db/schema.py`: SQLite schema and seeding for stations, villages, tigers, sightings, review queue, alerts, and triage logs.
- `src/ingest/sd_loader.py`: Recursive SD card scan, EXIF timestamp extraction, and station inference.
- `src/blank_filter/triage_detector.py`: CPU-based blank / person / animal / vehicle triage.
- `src/blank_filter/quarantine.py`: Blank frame quarantine and savings calculation.
- `src/privacy/human_blur.py`: Human privacy blurring.
- `src/reid/flank_extractor.py`: Flank crop extraction and enhancement.
- `src/reid/stripe_matcher.py`: SIFT-based stripe matching plus deep embedding similarity.
- `src/reid/enrollment.py`: Catalogue seeding, auto-match, review queueing, and auto-enrollment.
- `src/occupancy/pench_gis_data.py`: Pench core/buffer boundaries, camera stations, and villages.
- `src/occupancy/home_range.py`: MCP home range, centroid, area, and overlap calculations.
- `src/occupancy/map_generator.py`: Folium reserve map generation.
- `src/alerts/deviation_engine.py`: Movement deviation and conflict alerting.
- `tests/test_phase1_phase2.py`: Regression tests for the early pipeline.

## 4. Data And Dataset

The curated dataset is documented in `DATASET_README.md` and `PROJECT_SUMMARY_AND_PROGRESS.txt`.

The verified tiger dataset is organized into 7 classes:

- `T15_Collarwali`
- `T40_Patdev`
- `T-74_L-Mark`
- `Bajirao`
- `Swastik`
- `Karmajhiri_Core_Tigers`
- `Pench_General_Tigers`

The documented total is 95 verified tiger images across those 7 groups.

Dataset folders under `dataset/`:

- `verified_tiger_dataset/`: Renamed images plus YOLO-style `.txt` labels.
- `yolo_detection_dataset/`: YOLO training layout with `images/`, `labels/`, and `data.yaml`.
- `flank_stripe_crops/`: Flank crops for re-identification.
- `annotated_visualizations/`: Images rendered with bounding boxes and labels.
- `verified_tiger_dataset/verified_tiger_manifest.json`: Manifest for the verified tiger set.
- `yolo_detection_dataset/data.yaml`: YOLO dataset configuration.

The documentation says the project also includes non-tiger filtering outputs and other supporting artifacts. The main narrative in `PROJECT_SUMMARY_AND_PROGRESS.txt` describes the data source pipeline as a mix of official reports, reserve portals, public wildlife repositories, and manual curation.

## 5. Core Technical Approach

### Phase 1: Triage, Quarantine, Privacy

`src/blank_filter/triage_detector.py` uses Ultralytics YOLO with a confidence threshold of 0.20 to classify frames as blank, animal, person, or vehicle. Blank frames are staged into quarantine rather than deleted. Human frames are blurred by `src/privacy/human_blur.py` before being retained.

### Phase 2: Stripe Re-Identification

`src/reid/stripe_matcher.py` combines two signals:

- SIFT keypoint matching on flank stripe minutiae.
- ResNet-50 deep embeddings with cosine similarity.

`src/reid/enrollment.py` uses thresholds to decide between:

- High-confidence auto-match.
- Ambiguous review queue with visual match artifacts.
- Low-confidence auto-enrollment of a new tiger ID.

The database stores tiger metadata, sightings, crop paths, and match scores.

### Phase 3: Spatial Occupancy

`src/occupancy/home_range.py` computes tiger home ranges using MCP-style convex hull logic, converts lat/lon into local kilometer coordinates, calculates centroid and area, and finds overlaps between territories.

`src/occupancy/map_generator.py` renders a Folium map with:

- Core and buffer reserve polygons.
- Camera station markers.
- Village risk circles.
- Tiger home range polygons.
- Activity centroid markers.
- Territorial overlap layers.

### Phase 4: Deviation Alerts

`src/alerts/deviation_engine.py` evaluates a batch of sightings for:

- Village dispersal.
- Novel station capture.
- Centroid shift.
- Prolonged absence.

It stores alerts in SQLite and can export a markdown management briefing.

## 6. Database Design

`src/db/schema.py` creates the SQLite database at `TigerTrace_AI/data/database/tigertrace.db`.

Tables documented in the schema:

- `stations`: Camera trap station metadata and coordinates.
- `villages`: Surrounding villages and conflict risk fields.
- `tigers`: Known individuals and reference crops.
- `sightings`: Image-level capture records, tiger assignment, and crop paths.
- `review_queue`: Human review workflow for uncertain Re-ID results.
- `alerts`: Movement and conflict alerts.
- `triage_logs`: Batch-level blank-triage accounting.

The schema is seeded with Pench camera stations and villages from `src/occupancy/pench_gis_data.py`.

## 7. Main Pipeline Behavior

`src/pipeline.py` is the controlling orchestrator. It does the following:

1. Initializes the SQLite schema and seeds the Pench GIS data.
2. Scans a raw SD card folder recursively.
3. Runs blank detection and privacy blur.
4. Extracts flank crops for subject frames.
5. Inserts sightings and runs tiger identification / enrollment.
6. Queries historical sightings to build occupancy maps.
7. Evaluates alert conditions and exports a markdown report.

The pipeline returns a summary dictionary with batch metadata, counts, re-ID results, home ranges, overlaps, map path, alert list, alert report path, and execution time.

## 8. Operational Outputs

The project writes artifacts into the `TigerTrace_AI/data/` tree, including:

- `database/`: SQLite database.
- `privacy_blurred/`: Human-blurred images.
- `quarantine/`: Staged blank-frame quarantine.
- `tiger_crops/`: Flank crop outputs.
- `outputs/occupancy_maps/`: Generated Folium HTML maps.
- `outputs/alert_reports/`: Markdown alert briefings.
- `review_visualizations/`: SIFT match visualization images.

## 9. How It Is Meant To Be Used

Typical usage pattern from the docs:

1. Seed the reference catalogue with known tiger flank crops.
2. Process a raw SD card folder through the pipeline.
3. Inspect the returned summary, the SQLite database, the occupancy map HTML, and the alert markdown.

The main README and package README both position this as an offline workflow for field laptops rather than a cloud service.

## 10. Important Project Notes

- The project is designed for CPU-first offline operation.
- The system emphasizes explainability through visual match lines, stored crops, map layers, and markdown reports.
- The project scope is Pench Tiger Reserve and the surrounding human-wildlife interface.
- The documentation repeatedly treats the curated tiger dataset and the GIS station/village data as the key assets for the pipeline.

## 11. Best Source Files To Read Next

- `README.md`
- `TigerTrace_AI/README.md`
- `DATASET_README.md`
- `PROJECT_SUMMARY_AND_PROGRESS.txt`
- `TigerTrace_AI/src/pipeline.py`
- `TigerTrace_AI/src/db/schema.py`
- `TigerTrace_AI/src/alerts/deviation_engine.py`
- `TigerTrace_AI/src/occupancy/home_range.py`
- `TigerTrace_AI/src/occupancy/map_generator.py`

## 12. Short Handoff Version

If you need a one-paragraph prompt for another model, use this:

TigerTrace_AI is an offline CPU-first Pench Tiger Reserve camera-trap intelligence system. It ingests raw SD card images, filters blanks with YOLO, blurs humans for privacy, extracts tiger flank crops, matches stripes using SIFT plus ResNet embeddings, stores sightings in SQLite, computes home ranges and overlaps with Folium maps, and generates alerts for village proximity, centroid shifts, novel stations, and prolonged absence. The main code lives in `TigerTrace_AI/src/`, and the curated dataset is in `dataset/` with 7 tiger classes and YOLO/flank-crop artifacts.