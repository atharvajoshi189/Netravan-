# ==============================================================================
#            TIGERTRACE_AI — COMPLETE PROJECT ARCHITECTURE & FILE GUIDE
# ==============================================================================
# Comprehensive Reference for Pench Tiger Reserve & Wildlife Intelligence System
# Last Updated: October 2026
# ==============================================================================

## 1. PROJECT OVERVIEW & GOALS

TigerTraceAI is an end-to-end, privacy-preserving, offline-capable AI system designed 
for wildlife monitoring, camera trap triage, individual tiger re-identification, 
and human-wildlife conflict mitigation in Pench Tiger Reserve and Central Indian forests.

### Core Challenges Solved:
1. **Camera Trap Blank Triage**: 70% to 90% of camera trap triggers are empty 
   (triggered by wind, shadows, or heat). TigerTraceAI automatically filters and 
   quarantines these, saving hundreds of ranger hours.
2. **Human Privacy Protection**: Strict zero-trust blurring of human faces and bodies 
   before saving or visualizing camera trap frames.
3. **Individual Tiger Re-Identification (Re-ID)**: Extracting flank stripe patterns 
   and matching them against reference catalogs using SIFT reciprocal keypoint 
   correspondence, RANSAC spatial verification, and ResNet-50 deep embeddings.
4. **Safety & False Match Prevention (Steps 13 & 14)**: Strict safeguards preventing 
   unverified automatic identity confirmation. Candidate matches are routed to a 
   human review queue with raw explainable evidence.
5. **GIS Occupancy & Predictive Intelligence**: Generating Leaflet interactive heatmaps, 
   Minimum Convex Polygon (MCP) home ranges, movement forecasting, and real-time 
   deviation/conflict alerts.
6. **Multi-Species Wildlife Expansion (Step 15A–15D)**: Ingestion of Tadoba/Pench prey 
   species (Chital, Sambar, Gaur, Nilgai), assisted annotation, an interactive browser 
   review station, and gold-standard YOLO dataset compilation.
7. **Cross-Platform Ranger Field Deployment**: A companion Flutter mobile application 
   allowing rangers in the field to take photos, run local/remote analysis, review 
   evidence, and work offline.

---

## 2. HIGH-LEVEL WORKSPACE DIRECTORY TREE

```
TigerTraceAI-main/
│
├── TigerTrace_AI/                     # Core backend engine, AI algorithms & Web UI
│   ├── data/                          # Operational databases, models, staging datasets, outputs
│   ├── src/                           # Python algorithmic packages and pipelines
│   │   ├── alerts/                    # Deviation engine & SMS notifications
│   │   ├── behavior/                  # Tiger movement prediction & Markov models
│   │   ├── blank_filter/              # Camera trap blank triage & quarantine
│   │   ├── datasets/                  # Multi-species ingestion, CVAT export, gold standard
│   │   ├── db/                        # SQLite schema & database connection management
│   │   ├── ingest/                    # SD card image loader & batch ingestion
│   │   ├── occupancy/                 # Pench GIS coordinates, home ranges & Leaflet maps
│   │   ├── privacy/                   # Automatic human face/body blurring
│   │   ├── reid/                      # Flank extraction, SIFT stripe matching, enrollment
│   │   ├── config.py                  # Global path and threshold configurations
│   │   └── pipeline.py                # Central orchestrator integrating all modules
│   └── ui/                            # FastAPI server & Web Dashboard (HTML/CSS/JS)
│
├── mobile_app/                        # Flutter cross-platform mobile application
│   ├── lib/                           # Dart application source code
│   │   ├── core/                      # API client, config, models, offline queue
│   │   └── features/                  # Camera scan, analysis result, history, settings
│   ├── android/                       # Android native project files
│   ├── ios/                           # iOS native project files
│   └── web/                           # Flutter web build
│
├── scripts/                           # Utility, audit, evaluation & launcher scripts
│   ├── launch_review_station.py       # Browser-based Human Review Station HTTP server
│   ├── run_step11_acceptance_tests.py # End-to-end acceptance testing
│   ├── audit_step12_reid_reliability.py# Re-ID false match audit runner
│   ├── evaluate_reid_baseline.py      # Baseline CMC/Rank-1 Re-ID evaluation
│   ├── review_staging_pilot.py        # Terminal review summary for staged pilot data
│   └── validate_dataset_manifest.py   # Dataset manifest schema & hash validator
│
├── tests/                             # Automated test suites (Steps 9 through 15D)
│   ├── test_shared_analysis_api.py    # FastAPI /api/analyze verification
│   ├── test_step12_reid_reliability_audit.py # Re-ID score calibration audit
│   ├── test_step13_prevent_false_identity_confirmation.py # Step 13 safety guards
│   ├── test_step14_human_in_the_loop_review.py # Human review queue backend & DB
│   ├── test_step15c_assisted_annotation_and_gold_standard.py # Assisted annotation
│   ├── test_step15d_gold_standard_pipeline.py # Isolated review pipeline tests
│   └── ...                            # Ingestion safety and manifest unit tests
│
├── data/                              # Canonical manifests & ATRW benchmark staging
│   ├── manifests/                     # Master dataset manifests, schemas, audit reports
│   └── staging/atrw_pilot/            # ATRW tiger benchmark images and keypoints
│
├── dataset/                           # Reference tiger flank crops and verified dataset
│   ├── flank_stripe_crops/            # Cropped flanks of known tigers (Bajirao, Patdev, etc.)
│   └── verified_tiger_dataset/        # Raw verified tiger sightings
│
├── docs/                              # Technical documentation and architecture reports
│   ├── datasets/                      # Dataset inventory, ATRW reports, checklists
│   ├── reid/                          # Re-ID baseline evaluations & remediation plans
│   └── training/                      # Multi-species detector training strategies
│
├── Launch_TigerTrace_AI.bat           # One-click Windows launch script
├── Launch_TigerTrace_AI.sh            # Linux/macOS bash launcher
├── requirements.txt                   # Python dependencies
└── yolov8n.pt                         # Base YOLOv8 detector weights
```

---

## 3. DETAILED DIRECTORY & FILE BREAKDOWN

### 3.1. Core Application — `TigerTrace_AI/src/`

#### `TigerTrace_AI/src/pipeline.py`
- **Role**: The central orchestration pipeline of TigerTraceAI.
- **Workflow**:
  1. Accepts an incoming image path or raw bytes.
  2. Runs **Human Blur** to censor human faces or bodies for forest guard privacy.
  3. Runs **Triage Detector** to check for blanks or animals.
  4. If blank, sends image to **Quarantine** and stops.
  5. If tiger detected, runs **Flank Extractor** to extract left/right stripe patches.
  6. Passes flank to **TigerEnrollmentEngine** and **StripeReIDMatcher**.
  7. Enforces Step 13/14 safety rules: routes candidate matches to `review_required`.
  8. Updates SQLite database with sighting, coordinates, and timestamp.
  9. Evaluates **Behavior / Deviation Engine** for territorial shifts or conflict alerts.
  10. Triggers **Map Generator** to update Leaflet GIS occupancy maps.

#### `TigerTrace_AI/src/config.py`
- **Role**: Central configuration defining file system paths, model paths, confidence 
  thresholds (YOLO triage: 0.20), SIFT parameters, and database locations.

#### `TigerTrace_AI/src/privacy/human_blur.py`
- **Role**: Zero-trust privacy protector.
- **Mechanism**: Runs YOLO human detection (`person` class). Applies heavy Gaussian 
  blur to the bounding box of any detected person, ensuring anti-poaching patrol 
  personnel or villagers are never recorded without consent.

#### `TigerTrace_AI/src/blank_filter/triage_detector.py`
- **Role**: Eliminates false-positive blank triggers (windblown leaves, heat waves, rain).
- **Mechanism**: Evaluates frames using YOLOv8. If no animal or human is detected with 
  sufficient confidence, categorizes the frame as `blank`.

#### `TigerTrace_AI/src/blank_filter/quarantine.py`
- **Role**: Moves blank images to a structured quarantine directory with JSON metadata 
  for auditability, preventing database clutter while ensuring zero data loss.

#### `TigerTrace_AI/src/reid/flank_extractor.py`
- **Role**: Crops the tiger's torso/flank stripe pattern from the full-body bounding box.
- **Mechanism**: Computes aspect-ratio aware torso regions (excluding head, tail, and paws), 
  normalizes dimensions, and tags flank orientation (left vs. right).

#### `TigerTrace_AI/src/reid/stripe_matcher.py`
- **Role**: Algorithmic engine for tiger stripe matching (individual Re-ID).
- **Key Algorithms**:
  1. **HotSpotter SIFT Feature Extraction**: Extracts distinctive stripe edge keypoints 
     and descriptors, with automatic downsampling on huge images (>1600px) to prevent 
     memory spikes.
  2. **Mutual Nearest-Neighbour Matching**: Enforces reciprocal 1-to-1 correspondence 
     to prevent one query keypoint from falsely matching multiple reference keypoints.
  3. **RANSAC Geometric Verification**: Fits a homography matrix; requires at least 4 
     inliers to confirm structural alignment.
  4. **ResNet-50 Deep Feature Embedding**: Extracts 2048-dimensional cosine similarity.
  5. **Flank Compatibility Guard**: Strictly blocks cross-flank false matches (e.g., 
     left flank compared to right flank returns score 0.0).

#### `TigerTrace_AI/src/reid/enrollment.py`
- **Role**: Manages database enrollment and identity decisions.
- **Key Policy**:
  - Implements **Step 13 & 14 Safety Policy**: Automatic match confirmation is disabled.
  - Matches with high similarity are routed to `review_required` in the database.
  - Logs match candidates, SIFT inlier count, cosine score, and flank orientation.

#### `TigerTrace_AI/src/behavior/movement_predictor.py`
- **Role**: Spatial movement forecasting for individual tigers.
- **Mechanism**: Uses historical station-to-station sighting transitions and Markov chain 
  probabilities to predict the next likely camera trap station where a tiger will appear.

#### `TigerTrace_AI/src/occupancy/pench_gis_data.py`
- **Role**: Registry of Pench Tiger Reserve camera trap stations (e.g., `PTR_STN_01` to 
  `PTR_STN_14`), including latitude, longitude, core/buffer zone designation, and 
  proximity to village boundaries.

#### `TigerTrace_AI/src/occupancy/home_range.py`
- **Role**: Calculates Minimum Convex Polygons (MCP) and territorial overlap between 
  individual tigers.

#### `TigerTrace_AI/src/occupancy/map_generator.py`
- **Role**: Generates self-contained interactive HTML maps using Leaflet.js and OpenStreetMap.
- **Features**: Visualizes camera stations, tiger sighting markers, home range polygons, 
  and predictive movement vectors.

#### `TigerTrace_AI/src/alerts/deviation_engine.py`
- **Role**: Detects anomalous behavior that may lead to human-wildlife conflict.
- **Alert Types**:
  1. *Territory Shift*: A core tiger moving into buffer or boundary zones.
  2. *Village Proximity*: Sightings near village borders.
  3. *Prolonged Absence*: Individual not sighted for over 14 days.

#### `TigerTrace_AI/src/alerts/sms_notifier.py`
- **Role**: Generates markdown briefing reports and mock/Twilio SMS alert payloads for 
  forest range officers.

#### `TigerTrace_AI/src/db/schema.py`
- **Role**: SQLite database schema setup and migration.
- **Key Tables**:
  - `sightings`: Image paths, timestamps, stations, species, detected boxes.
  - `tiger_catalogue`: Registered individual tigers, flank crops, reference images.
  - `reid_comparisons`: Scores, SIFT inliers, cosine similarity, decisions.
  - `human_review_queue`: Pending reviews, confirmed identities, reviewer notes.

#### `TigerTrace_AI/src/datasets/`
- `staging_pilot_ingest.py`: Ingests licensed wildlife images (Chital, Sambar, Gaur, Nilgai).
- `assisted_annotation.py`: Runs object detectors to propose initial animal bounding boxes.
- `cvat_exporter.py`: Exports datasets in standard CVAT XML format.
- `gold_standard_builder.py`: Compiles verified annotations into YOLO format with 
  leakage-safe encounter-based train/val/test splits.

---

### 3.2. Web Dashboard & API — `TigerTrace_AI/ui/`

#### `TigerTrace_AI/ui/app.py`
- **Role**: FastAPI backend application running on port 8000.
- **Key Endpoints**:
  - `POST /api/analyze`: Multi-part image upload for camera trap analysis.
  - `GET /api/sightings`: Fetch recent sightings for dashboard feeds.
  - `GET /api/reviews/pending`: Fetch unreviewed identity candidates.
  - `POST /api/reviews/{id}/decision`: Accept, Reject, or Mark Inconclusive an identity.
  - `GET /api/map/latest`: Retrieve the latest Leaflet GIS occupancy map.

#### `TigerTrace_AI/ui/templates/index.html`
- **Role**: Single-page web dashboard interface with tabs for:
  - Live Camera Trap Feed & Batch Uploader
  - Territory & GIS Occupancy Map
  - Human Review Queue (Side-by-side stripe comparison)
  - Intelligence & Alert Briefings

#### `TigerTrace_AI/ui/static/css/style.css` & `js/app.js`
- **Role**: Sleek dark-mode styling, dynamic table rendering, photo modals, and real-time 
  REST API polling.

---

### 3.3. Mobile Application — `mobile_app/` (Flutter)

Built with Flutter to support offline field use on Android, iOS, and Web.

#### `mobile_app/lib/main.dart` & `app/app.dart`
- **Role**: App initialization, dependency injection, and material theme setup.

#### `mobile_app/lib/core/api/api_client.dart` & `endpoints.dart`
- **Role**: HTTP client communicating with the FastAPI backend over Wi-Fi, hotspot, or LAN. 
  Handles multipart image uploads and JSON parsing.

#### `mobile_app/lib/core/config/app_config.dart` & `theme.dart`
- **Role**: Configurable backend URL setting (allowing rangers to connect to a field 
  laptop IP), offline caching flags, and wildlife color themes.

#### `mobile_app/lib/core/models/`
- `analysis_result.dart`: Dart model representing species, bounding box, flank crop, 
  candidate tiger ID, SIFT inliers, composite score, and review status.
- `observation_record.dart`: Model for logged observations.

#### `mobile_app/lib/core/services/offline_queue.dart`
- **Role**: Caches captured photos locally in SQLite/shared preferences when in deep 
  jungle areas without connectivity, syncing automatically once reconnected.

#### `mobile_app/lib/features/camera_scan/camera_scan_screen.dart`
- **Role**: Camera capture interface with quick-action buttons for preset test images 
  or live camera trap photos.

#### `mobile_app/lib/features/animal_analysis/result_screen.dart`
- **Role**: Displays the analysis output: bounding box overlays, candidate tiger 
  identity, SIFT match visualization, and clear warnings that candidate scores are 
  uncalibrated and require human review.

#### `mobile_app/lib/features/observation_history/history_screen.dart`
- **Role**: Searchable list of past observations recorded on the mobile device.

#### `mobile_app/lib/features/settings/settings_screen.dart`
- **Role**: UI to configure server IP, test connection, and clear offline cache.

---

### 3.4. Scripts — `scripts/`

#### `scripts/launch_review_station.py`
- **Role**: Dedicated local HTTP server (running on `http://127.0.0.1:8085`) serving the 
  Step 15D Browser Review Station.
- **Features**:
  - Serves static images and the interactive annotation UI.
  - Implements REST endpoints: `GET /api/samples`, `POST /api/save_review`, `GET /api/status`.
  - Persists human decisions directly to `human_reviews/{sample_id}.json` using 
    `GoldStandardBuilder`.

#### `scripts/run_step11_acceptance_tests.py`
- **Role**: Executes automated end-to-end acceptance tests simulating the mobile app 
  uploading photos to the FastAPI backend and verifying database persistence.

#### `scripts/audit_step12_reid_reliability.py`
- **Role**: Systematic testing of the SIFT and deep embedding Re-ID matcher across known 
  and unknown tiger probes, evaluating false-match vulnerability.

#### `scripts/evaluate_reid_baseline.py`
- **Role**: Computes baseline CMC (Cumulative Matching Characteristics), Rank-1, Rank-5, 
  and mAP metrics on reference tiger datasets.

#### `scripts/validate_dataset_manifest.py`
- **Role**: Validates CSV manifests against JSON schemas, checking SHA256 hashes, URLs, 
  and license attribution.

---

### 3.5. Tests Suite — `tests/`

Exhaustive regression and unit tests guaranteeing stability and safety:
- `test_shared_analysis_api.py`: Validates `/api/analyze` across blank, animal, and tiger images.
- `test_flank_compatibility_guard.py`: Verifies left-vs-right flank mismatch blocking.
- `test_flank_extractor_bbox.py`: Checks aspect-ratio scaling and bounding box cropping.
- `test_reid_matcher_audit.py`: Validates SIFT inlier counting and RANSAC homography.
- `test_step12_reid_reliability_audit.py`: Verifies calibration and unverified score reporting.
- `test_step13_prevent_false_identity_confirmation.py`: Confirms candidate matches route to 
  `review_required` and auto-confirmation is disabled.
- `test_step14_human_in_the_loop_review.py`: Validates the backend review queue, decision 
  persisting, and audit trail logging.
- `test_step15c_assisted_annotation_and_gold_standard.py`: Tests provisional proposal generation 
  and CVAT XML export.
- `test_step15d_gold_standard_pipeline.py`: Tests the isolated gold-standard YOLO conversion 
  pipeline with synthetic test fixtures, verifying leakage-safe splitting and rejection handling.

---

### 3.6. Data & Datasets — `TigerTrace_AI/data/` & `dataset/`

- `TigerTrace_AI/data/tigertrace.db`: SQLite database storing sightings, catalogs, and reviews.
- `TigerTrace_AI/data/models/best_yolov8.pt`: Trained custom YOLOv8 tiger detector weights.
- `TigerTrace_AI/data/reference_catalogue/`: High-quality reference flank images for known 
  Pench individual tigers:
  - **Bajirao** (Dominant male, core territory)
  - **T40 Patdev** (Female, central Pench)
  - **Swastik** (Male)
  - **T15 Collarwali** (Legendary queen of Pench)
  - **T-74 L-Mark**
- `TigerTrace_AI/data/staging_wildlife_pilot/`: Step 15B-15D staged wildlife pilot:
  - 40 licensed images across 4 prey species (10 Chital, 10 Sambar, 10 Gaur, 10 Nilgai).
  - 58 provisional bounding box proposals.
  - `review_ui/index.html`: Interactive `<canvas>` review station allowing box dragging, 
    drawing, and species tagging.
  - `human_reviews/`: Destination directory for human-verified gold-standard reviews.
- `data/manifests/dataset_manifest.csv`: Master audit manifest tracking images, source 
  URLs, licenses, and SHA256 checksums.

---

## 4. END-TO-END WORKFLOW SUMMARY

```
                    +---------------------------+
                    | Camera Trap Photo (Field) |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | Step 1: Human Blur        | (Privacy Protection)
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | Step 2: Triage Detector   | (YOLOv8 Filter)
                    +------+-------------+------+
                           |             |
                 Blank     |             | Animal Detected
                           v             v
             +---------------+    +---------------------------+
             | Quarantine    |    | Step 3: Animal Sighting   |
             +---------------+    +-------------+-------------+
                                                |
                                        Tiger   |   Prey Species
                                                v
                                  +---------------------------+
                                  | Step 4: Flank Extractor   |
                                  +-------------+-------------+
                                                |
                                                v
                                  +---------------------------+
                                  | Step 5: SIFT Stripe Match |
                                  |        & ResNet-50 Cosine |
                                  +-------------+-------------+
                                                |
                                                v
                                  +---------------------------+
                                  | Step 6: Step 13/14 Policy |
                                  | Candidate -> Review Queue |
                                  +-------------+-------------+
                                                |
                                                v
                                  +---------------------------+
                                  | Step 7: GIS Heatmap &     |
                                  | Conflict Alert Engine     |
                                  +---------------------------+
```

---

## 5. QUICK LAUNCH & EXECUTION COMMANDS

### A. Run the Web Dashboard & API (Default: Port 8000)
```powershell
python TigerTrace_AI/ui/app.py
```
Open in browser: `http://localhost:8000`

### B. Launch the Step 15D Human Review Station (Port 8085)
```powershell
python scripts/launch_review_station.py --port 8085
```
Open in browser: `http://127.0.0.1:8085`

### C. Run the Complete Test Suite
```powershell
# Run Step 15D Gold-Standard Pipeline Tests
python -m unittest tests/test_step15d_gold_standard_pipeline.py

# Run Step 14 Human Review Queue Tests
python -m unittest tests/test_step14_human_in_the_loop_review.py

# Run Step 13 False Confirmation Safety Tests
python -m unittest tests/test_step13_prevent_false_identity_confirmation.py

# Run Step 11 Mobile Acceptance Tests
python -m unittest tests/test_shared_analysis_api.py
```

### D. Run the Mobile App (Flutter)
```powershell
cd mobile_app
flutter run -d chrome     # Run in Chrome browser
# OR
flutter run -d <device_id> # Run on connected Android phone
```

---
*End of Guide — TigerTraceAI Engineering Team*
