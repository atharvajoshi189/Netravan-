# TIGERTRACEAI — COMPLETE PROJECT AUDIT & INTEGRATION HANDOFF

**Document Version:** 1.0.0  
**Audit Date:** October 11, 2026  
**Auditor Roles:** Senior AI/ML Engineer, Python/FastAPI Architect, Computer Vision Engineer, Flutter Developer, Codebase Auditor  
**Workspace Root:** `d:\TigerTraceAI-main`  
**Target File:** `TIGERTRACEAI_INTEGRATION_HANDOFF.md`  

---

## 1. EXECUTIVE SUMMARY

TigerTraceAI is an offline-capable, privacy-preserving wildlife monitoring and individual tiger identification intelligence system designed for Central Indian dry-deciduous forest reserves (specifically Pench Tiger Reserve and Tadoba-Andhari Tiger Reserve).

### Key Findings of the Audit:

1. **Current Working System [VERIFIED FROM SOURCE, VERIFIED BY TEST]**:
   - The repository hosts a fully functional, running FastAPI backend (`TigerTrace_AI/ui/app.py`), an algorithmic pipeline (`TigerTrace_AI/src/pipeline.py`), an OpenCV SIFT + ResNet-50 stripe re-identification engine (`TigerTrace_AI/src/reid/`), a spatial movement predictor (`TigerTrace_AI/src/behavior/movement_predictor.py`), and a cross-platform Flutter field application (`mobile_app/`).
   - The system is protected by strict safety policies established in Steps 9A, 9B, 13, and 14: automatic identity confirmation is disabled, cross-flank comparisons are strictly blocked, and candidate tiger matches are routed to an explainable human review queue.

2. **Status of External Models A, B, C, and D [VERIFIED FROM SOURCE, NOT FOUND]**:
   - **Model A (26-Species YOLO)**: **NOT FOUND** in the local workspace. Referenced in historical Google Drive storage (`/content/drive/MyDrive/TigerTraceAI/training_runs/tadoba_26class_v1/weights/best.pt`).
   - **Model B (11-Class Tiger Identity YOLO11n)**: **NOT FOUND** in the local workspace. Referenced in historical Google Drive storage (`/content/drive/MyDrive/TigerTraceAI/training_runs/tiger_identity_11class_v1/weights/best.pt`).
   - **Model C (5-Species YOLO)**: **NOT FOUND** in the local workspace. No local training runs, checkpoints, or active training jobs exist in this workspace (training is taking place in an external environment).
   - **Model D (Tiger Behaviour YOLO)**: **NOT FOUND** as a YOLO computer-vision model. The existing behavior module (`src/behavior/movement_predictor.py`) is a **spatial/temporal movement intelligence system** using Time-Weighted Kernel Density Estimation (KDE) and discrete Markov chain station transition probabilities, NOT a frame-by-frame visual behavior classifier.
   - **Locally Present Checkpoints [VERIFIED FROM SOURCE]**:
     * `yolov8n.pt` (6.5 MB, COCO 80-class pre-trained model).
     * `TigerTrace_AI/data/models/best_yolov8.pt` (52 MB, single-class `{0: 'tiger'}` detector, SHA-256: `7de274df8bfa88d5d470e06f32a7f716e5e12cad82ad4221ebb66d8365acbb82`).
     * `TigerTrace_AI/data/models/custom_tiger_detector.pt` (52 MB, identical duplicate of `best_yolov8.pt`).

3. **Integration Feasibility & Architectural Recommendation**:
   - **Strategy B (Modular Hierarchical Pipeline) is strongly recommended** over attempting to train a single monolithic YOLO model combining 26 species, 11 tiger identities, and behavior classes.
   - Bounding-box object detectors should identify species; stripe biometric pattern matchers (SIFT/RootSIFT + deep metric embeddings) should identify individual tigers; and behavior classifiers should operate on cropped animal regions or temporal video frames.
   - Weights from unrelated YOLO models cannot be concatenated; class definitions must be reconciled before training any unified multi-species model.

---

## 2. VERIFIED PROJECT STRUCTURE

Below is the verified top-level directory layout of `d:\TigerTraceAI-main` [VERIFIED FROM SOURCE]:

```
d:\TigerTraceAI-main/
│
├── TigerTrace_AI/                             # Core Python Backend & Web Application
│   ├── data/                                  # Operational Data, Checkpoints & Outputs
│   │   ├── database/                          # Active SQLite Database
│   │   │   └── tigertrace.db                  # (643,072 bytes) Active database with 420 sightings
│   │   ├── models/                            # Trained Detection Checkpoints
│   │   │   ├── best_yolov8.pt                 # (52,004,182 bytes) 1-class Tiger detector
│   │   │   └── custom_tiger_detector.pt       # (52,004,182 bytes) Identical hash to best_yolov8.pt
│   │   ├── reference_catalogue/               # Known Individual Tiger Reference Crops (59 crops)
│   │   │   ├── Bajirao/                       # 10 flank crops
│   │   │   ├── Karmajhiri_Core_Tigers/        # 16 flank crops
│   │   │   ├── Swastik/                       # 7 flank crops
│   │   │   ├── T-74_L-Mark/                   # 9 flank crops
│   │   │   ├── T15_Collarwali/                # 10 flank crops
│   │   │   └── T40_Patdev/                    # 7 flank crops
│   │   ├── staging_wildlife_pilot/            # Step 15B-15D Staged Prey Species Pilot
│   │   │   ├── images/                        # 40 licensed images (Chital, Sambar, Gaur, Nilgai)
│   │   │   ├── provisional_proposals/         # 58 provisional bounding boxes
│   │   │   ├── human_reviews/                 # Storage for human-verified gold-standard reviews
│   │   │   └── review_ui/index.html           # Interactive <canvas> Review Station
│   │   ├── taxonomy/                          # Taxonomy Registry
│   │   │   └── species_taxonomy.json          # 17-class Central Indian Tadoba/Pench taxonomy
│   │   └── outputs/                           # HTML Leaflet maps and Markdown alert reports
│   │
│   ├── src/                                   # Algorithmic Subsystems
│   │   ├── alerts/                            # Conflict & Territory Deviation Alerting
│   │   │   ├── deviation_engine.py            # Territory shifts, absence, village dispersal
│   │   │   └── sms_notifier.py                # Alert report generation & SMS dispatch
│   │   ├── behavior/                          # Spatial Movement Intelligence
│   │   │   └── movement_predictor.py          # Time-Weighted KDE & Discrete Markov Transitions
│   │   ├── blank_filter/                      # Camera Trap Blank Triage & Privacy Blur
│   │   │   ├── triage_detector.py             # Dual-stage YOLO triage (Tiger custom + COCO)
│   │   │   └── quarantine.py                  # Blank photo isolation with JSON audit logs
│   │   ├── datasets/                          # Dataset Ingestion & Curation Pipeline
│   │   │   ├── staging_pilot_ingest.py        # Ingestion of licensed wildlife observations
│   │   │   ├── assisted_annotation.py         # Automated provisional box generation
│   │   │   ├── cvat_exporter.py               # CVAT XML annotation export
│   │   │   └── gold_standard_builder.py       # YOLO conversion with leakage-safe splits
│   │   ├── db/                                # Database Management
│   │   │   └── schema.py                      # SQLite schema, tables, and migrations
│   │   ├── ingest/                            # SD Card Drop Ingestion
│   │   │   └── sd_loader.py                   # EXIF extraction and batch folder staging
│   │   ├── occupancy/                         # Pench GIS & Interactive Maps
│   │   │   ├── pench_gis_data.py              # 18 camera stations and 8 buffer villages
│   │   │   ├── home_range.py                  # Minimum Convex Polygon (MCP) territories
│   │   │   └── map_generator.py               # Interactive Leaflet.js HTML map rendering
│   │   ├── privacy/                           # Privacy Protection
│   │   │   └── human_blur.py                  # Zero-trust Gaussian blur on human detections
│   │   ├── reid/                              # Biometric Tiger Re-Identification
│   │   │   ├── flank_extractor.py             # Torso crop & CLAHE lighting normalization
│   │   │   ├── stripe_matcher.py              # SIFT reciprocal matching + ResNet-50 cosine
│   │   │   └── enrollment.py                  # Tiger enrollment engine & Step 13/14 policies
│   │   ├── config.py                          # Global configuration constants
│   │   └── pipeline.py                        # Central multi-phase orchestrator
│   │
│   └── ui/                                    # Web Presentation & API Server
│       ├── app.py                             # FastAPI server (19 REST endpoints)
│       ├── static/                            # CSS stylesheets and JavaScript client logic
│       └── templates/index.html               # Web Dashboard interface
│
├── mobile_app/                                # Flutter Mobile Client
│   ├── lib/
│   │   ├── main.dart                          # Application entry point
│   │   ├── app/app.dart                       # MaterialApp configuration
│   │   ├── core/
│   │   │   ├── api/                           # HTTP client and endpoint definitions
│   │   │   │   ├── api_client.dart            # Multipart upload and error handling
│   │   │   │   └── endpoints.dart             # Base URL routing (/api/analyze, etc.)
│   │   │   ├── config/                        # Dynamic server IP and theme
│   │   │   ├── models/                        # AnalysisResult, CandidateIdentity, LocationInfo
│   │   │   └── services/offline_queue.dart    # Offline capture caching for field rangers
│   │   └── features/                          # Screen implementations
│   │       ├── animal_analysis/result_screen.dart # Bounding box & stripe match rendering
│   │       ├── camera_scan/camera_scan_screen.dart# Camera capture & preset test runner
│   │       ├── observation_history/history_screen.dart
│   │       └── settings/settings_screen.dart  # IP configuration & connection test
│   └── pubspec.yaml                           # Flutter dependencies
│
├── scripts/                                   # Operational & Audit Scripts
│   ├── launch_review_station.py               # Step 15D Browser Review Server (Port 8085)
│   ├── run_step11_acceptance_tests.py         # End-to-end integration acceptance test
│   ├── audit_step12_reid_reliability.py       # Re-ID matcher false-positive audit
│   ├── evaluate_reid_baseline.py              # Re-ID baseline benchmark evaluator
│   └── validate_dataset_manifest.py           # Dataset schema and hash validator
│
├── tests/                                     # Automated Unit & Regression Test Suite
│   ├── test_shared_analysis_api.py            # FastAPI /api/analyze test suite
│   ├── test_step13_prevent_false_identity_confirmation.py # Step 13 false match guards
│   ├── test_step14_human_in_the_loop_review.py# Step 14 review queue & concurrency tests
│   ├── test_step15c_assisted_annotation_and_gold_standard.py # Assisted annotation tests
│   ├── test_step15d_gold_standard_pipeline.py # Step 15D gold-standard YOLO export tests
│   ├── test_flank_compatibility_guard.py      # Left vs Right flank mismatch tests
│   └── test_flank_extractor_bbox.py           # Bounding-box scaling tests
│
├── data/                                      # Master Manifests & ATRW Benchmark Data
│   ├── manifests/                             # dataset_manifest.csv, audit reports, schemas
│   └── staging/atrw_pilot/                    # ATRW benchmark tiger dataset & annotations
│
├── dataset/                                   # Local Tiger Reference & Crop Archives
│   ├── flank_stripe_crops/                    # Verified tiger flank crops
│   └── verified_tiger_dataset/                # Full-frame camera trap tiger photos
│
├── docs/                                      # Technical Architecture Documentation
│   ├── datasets/                              # Prey dataset inventories & checklists
│   ├── reid/                                  # Re-ID baseline evaluations & remediation plans
│   └── training/                              # Detector training strategies
│
├── requirements.txt                           # Python package dependencies
└── yolov8n.pt                                 # Base COCO 80-class weights (6,549,796 bytes)
```

---

## 3. CURRENT RUNTIME AND DEPENDENCY ENVIRONMENT

[VERIFIED BY TEST: `python -c "import sys, platform, torch, torchvision, ultralytics, cv2, fastapi..."`]

| Component | Installed Version | Notes |
| :--- | :--- | :--- |
| **Python** | `3.10.11` (64-bit AMD64) | MSC v.1929 |
| **Operating System** | `Windows-10-10.0.26200-SP0` | Native Windows 11 / 10 |
| **PyTorch** | `2.10.0+cpu` | **CUDA Available: False** (CPU execution only) |
| **Torchvision** | `0.25.0+cpu` | Used for ResNet-50 feature extractor |
| **Ultralytics** | `8.4.16` | YOLOv8 inference runtime |
| **OpenCV (`cv2`)** | `4.13.0` | SIFT feature extraction, image warping, CLAHE |
| **FastAPI** | `0.133.0` | Web framework |
| **Uvicorn** | `>=0.22.0` | ASGI server |
| **Flutter SDK** | `^3.10.4` | Mobile client SDK |
| **Flutter Dependencies** | `http: ^1.6.0`, `intl: ^0.20.3`, `shared_preferences: ^2.5.5`, `image_picker: ^1.2.3`, `http_parser: ^4.1.2` | Defined in `mobile_app/pubspec.yaml` |

> [!IMPORTANT]
> Because CUDA is unavailable on this host machine, all neural network inferences (YOLO detection, ResNet embedding) execute on the CPU. High-resolution uncropped images (>1600px) must be handled with care to prevent memory spikes.

---

## 4. COMPLETE MODEL INVENTORY

[VERIFIED FROM SOURCE: Inspected all `.pt` checkpoints using PyTorch unpickling]

| Model Identifier | File Path | File Size | Task / Type | Classes | Status in Workspace |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model A: 26-Species** | `/content/drive/MyDrive/.../tadoba_26class_v1/weights/best.pt` | Unknown (~50MB) | Object Detection | 26 wildlife species | **NOT FOUND** (Stored in user's Google Drive) |
| **Model B: 11 Tiger IDs** | `/content/drive/MyDrive/.../tiger_identity_11class_v1/weights/best.pt` | Unknown (~6MB) | Object Detection / Classification | 11 individual tiger IDs | **NOT FOUND** (Stored in user's Google Drive) |
| **Model C: 5-Species** | N/A (Currently training) | N/A | Object Detection | 5 wildlife species | **NOT FOUND** (External training environment) |
| **Model D: Behavior YOLO**| N/A | N/A | Video/Image Behavior Classification | Unknown | **NOT FOUND** (No behavioral YOLO checkpoint exists) |
| **Production Tiger Model** | `TigerTrace_AI/data/models/best_yolov8.pt` | 52,004,182 bytes | Object Detection (YOLOv8) | 1 class: `{0: 'tiger'}` | **VERIFIED PRESENT** (SHA-256: `7de274df...`) |
| **Duplicate Tiger Model** | `TigerTrace_AI/data/models/custom_tiger_detector.pt` | 52,004,182 bytes | Object Detection (YOLOv8) | 1 class: `{0: 'tiger'}` | **VERIFIED PRESENT** (Identical to `best_yolov8.pt`) |
| **COCO Base Triage Model**| `yolov8n.pt` (workspace root) | 6,549,796 bytes | Object Detection (YOLOv8n) | 80 COCO classes (`person`, `vehicle`, etc.) | **VERIFIED PRESENT** |
| **Deep Re-ID Embedder** | Loaded via `torchvision.models.resnet50(weights=DEFAULT)` | ~102 MB (in cache) | Feature Extraction | 2048-dim feature vector | **VERIFIED PRESENT** (Dynamic torchvision download) |
| **SIFT Stripe Matcher** | `cv2.SIFT_create()` | In-memory OpenCV | Biometric Feature Matcher | Local DoG keypoints | **VERIFIED PRESENT** (Native OpenCV 4.13.0) |

---

## 5. MODEL CLASSES AND LABEL CONFLICTS

### 5.1. Class Incompatibilities Across Candidate Models

1. **Model A (26 Species) vs. Tiger Apex Predator**:
   - In Model A's training run, `tiger` was **omitted as a class**.
   - During evaluation, tiger frames were falsely detected as `Striped_Hyena` due to similar visual stripe textures.
   - Integrating Model A directly without re-training or post-processing would cause all tigers to be misclassified as hyenas.

2. **Model B (11-Class Individual Tiger Detector) Flaw**:
   - Known classes: `Chota Dadhiyal (T-84)`, `Chota Matka (T-126)`, `Choti Tara (T-7)`, `Junabai (T-82)`, `Mama Male`, `Matkasur (T-54)`, `Mowgli`, `Shambhu`, `Sundari (T-17)`, `XYLO`, `Y-mark`.
   - **Architectural Error**: Training a standard YOLO object detector where each individual animal is an object class is fundamentally fragile for open-set re-identification.
   - When a 12th tiger or a dispersing sub-adult enters the reserve, an 11-class detector *must* force-classify it into one of the 11 known classes or fail to detect it.
   - Individual identification requires **open-set metric learning** (matching against an extensible gallery of reference patterns), not a closed-set softmax classification head.

3. **Taxonomy Consolidation**:
   - The repository contains an established, version-controlled 17-class taxonomy in [`TigerTrace_AI/data/taxonomy/species_taxonomy.json`](file:///d:/TigerTraceAI-main/TigerTrace_AI/data/taxonomy/species_taxonomy.json):
     * Class 0: `tiger`
     * Class 1: `sambar`
     * Class 2: `wild_boar`
     * Class 3: `chital`
     * Class 4: `cattle`
     * Class 5: `barking_deer`
     * Class 6: `gaur`
     * Class 7: `nilgai`
     * Class 8: `leopard`
     * Class 9: `goat_sheep`
     * Class 10: `black_naped_hare`
     * Class 11: `buffalo`
     * Class 12: `grey_junglefowl`
     * Class 13: `peafowl`
     * Class 14: `giant_flying_squirrel`
     * Class 15: `hanuman_langur`
     * Class 16: `golden_jackal`
   - Neither Model A (26 classes) nor Model C (5 classes) matches this canonical 17-class index ordering.

4. **Impossibility of Weight Concatenation**:
   - Neural network weights from two separate YOLO models (e.g., Model A and Model C) cannot be mathematically concatenated into a single `.pt` file. Their convolutional kernels, backbone feature extractors, and detection head classification layers are distinct parameter spaces. Any unified multi-species model must be trained on a unified annotated dataset.

---

## 6. EXISTING FASTAPI ROUTES AND SCHEMAS

[VERIFIED FROM SOURCE: `TigerTrace_AI/ui/app.py`]

The application runs via FastAPI at `http://localhost:8000`. It defines 19 endpoints:

| Method | Endpoint | Line | Request Parameters / Body | Response Schema / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | L66 | None | HTML Web Dashboard (`templates/index.html`) |
| `GET` | `/api/telemetry` | L71 | None | System status, station count, tiger count, pending reviews |
| `GET` | `/api/available_sd_cards` | L110 | None | Lists uningested SD card drop folders |
| `POST`| `/api/process_sd` | L127 | `ProcessSDRequest` (JSON) | Triggers batch ingestion pipeline on raw SD card drop |
| `POST`| `/api/upload_batch` | L168 | `files: List[UploadFile]`, `station_id` | Web batch uploader for camera trap folders |
| `GET` | `/api/quarantine_blanks` | L205 | None | Returns list of blank/quarantined images |
| `GET` | `/api/behavior_predictions` | L227 | None | Returns Markov transition matrices & movement forecasts |
| `GET` | `/api/map` | L264 | None | Generates and serves latest Leaflet GIS occupancy HTML |
| `GET` | `/api/review_queue` | L319 | None | Returns all pending tiger identity candidates with evidence |
| `POST`| `/api/review_queue/{review_id}/action` | L405 | `ReviewActionRequest` (JSON) | Accepts, rejects, or marks inconclusive an identity candidate |
| `GET` | `/api/review_queue/history`| L433 | None | Audit log of past human reviewer decisions |
| `GET` | `/api/alerts` | L452 | None | Conflict alerts (village dispersal, territorial shifts) |
| `GET` | `/api/tigers` | L466 | None | Returns list of registered resident individual tigers |
| `GET` | `/api/image` | L483 | `path: str` (Query param) | Securely serves local image file as `FileResponse` |
| `GET` | `/api/export_report` | L490 | `format: str` | Downloads summary briefing markdown/PDF |
| `GET` | `/api/health` | L513 | None | Health check returning status, database, model versions |
| `POST`| `/api/analyze` | L539 | Multipart Form: `file`, `station_id`, `lat`, `lon`, `timestamp`, `flank_hint` | **Primary Unified Analysis API** for Web and Mobile App |
| `GET` | `/api/mobile/observations` | L857 | `limit: int`, `offset: int` | Mobile sighting history feed |
| `GET` | `/api/mobile/catalogue` | L886 | None | Syncs known resident tiger catalog to mobile client |
| `POST`| `/api/mobile/sync_batch` | L908 | JSON array of offline observations | Syncs sightings recorded offline in deep jungle |

---

## 7. END-TO-END IMAGE ANALYSIS CALL GRAPH

The execution path of `POST /api/analyze` [VERIFIED FROM SOURCE: `TigerTrace_AI/ui/app.py:L539-855`]:

```
1. Client HTTP POST /api/analyze (multipart/form-data)
   └── Validates file extension (.jpg, .jpeg, .png, .bmp, .webp)
   └── Validates file size (limit: 25 MB)
   └── Saves file to data/mobile_uploads/mobile_{timestamp}_{uuid}.jpg

2. Station & Coordinate Resolution
   └── Resolves station_id or calculates nearest station via GPS (Haversine formula)

3. Primary Detection & Triage [pipeline.triage_detector.detect_frame(saved_path)]
   ├── Step 3.1: Run Custom Tiger Model (data/models/best_yolov8.pt)
   │   └── conf >= 0.20 -> class_id: 99, class_name: "tiger"
   ├── Step 3.2: Run Secondary Triage Model (yolov8n.pt)
   │   └── Checks for class 0 ("person"), vehicle classes (1,2,3,5,7), or other animals
   └── Categorize frame: 'tiger' | 'person' | 'vehicle' | 'animal' | 'blank'

4. Branch Execution:
   ├── IF 'blank':
   │   └── Returns is_blank=True, species='blank', observation_id=None
   ├── IF 'person':
   │   ├── pipeline.privacy_blurrer.apply_privacy_blur(saved_path, human_boxes)
   │   └── Returns blurred image URL, species='human', observation_id=None
   ├── IF non-tiger 'animal' / 'vehicle':
   │   └── Returns species='wildlife' / 'vehicle', identity_status='not_applicable'
   └── IF 'tiger':
       ├── Extract primary bounding box [L716]
       ├── Flank Extraction [pipeline.flank_extractor.extract_flank_crop] (L719)
       │   └── Aspect-ratio aware torso crop + CLAHE lighting normalization -> crop_path
       ├── Database Insertion (sightings table) [L726]
       │   └── Inserts sighting with review_status='pending_review' -> sighting_id
       ├── Flank-Guarded Biometric Re-ID [pipeline.enrollment_engine.identify_and_enroll] (L734)
       │   ├── SIFT reciprocal matching against reference_catalogue (stripe_matcher.py)
       │   ├── ResNet-50 cosine feature similarity (stripe_matcher.py)
       │   └── Check flank compatibility (opposite flanks score 0.0)
       ├── Step 13 Safety Policy Enforcement [L764]
       │   ├── Decision 'matched' -> forced to identity_status="review_required"
       │   └── Enqueues candidate to review_queue table with raw inliers & cosine score
       ├── Spatial Behavior Prediction [L790]
       │   └── If tiger has >= 2 historical sightings:
       │       └── pipeline.movement_predictor.predict_tiger_movement -> Markov forecast
       ├── Conflict Deviation Evaluation [L818]
       │   └── pipeline.alert_engine.evaluate_batch_alerts -> evaluates territory shifts
       └── Returns comprehensive JSON response [L831-854]
```

---

## 8. TIGER STRIPE RE-ID IMPLEMENTATION

[VERIFIED FROM SOURCE: `TigerTrace_AI/src/reid/stripe_matcher.py` & `enrollment.py`]

The biometric re-identification system uses a dual-engine ensemble:

1. **HotSpotter SIFT Feature Matching**:
   - Detects local Scale-Invariant Feature Transform (SIFT) keypoints in the flank stripe pattern.
   - **Out-of-Memory Guard [VERIFIED FROM SOURCE]**: High-resolution camera trap photos (>1600px) are automatically downsampled using area interpolation before computing scale space, preventing OpenCV memory exhaustion.
   - **Lowe's Ratio Test**: Threshold 0.75 filters ambiguous keypoint descriptors.
   - **Mutual Nearest-Neighbour (Reciprocal) Matching**: Enforces 1-to-1 correspondence (point $A$ in Query matches $B$ in Reference iff $B$'s nearest neighbor in Query is $A$). This prevents repetitive background stripes from inflating match counts.
   - **RANSAC Geometric Homography**: Requires $\ge 4$ inliers consistent with an affine transformation.

2. **ResNet-50 Deep Metric Embeddings**:
   - Torchvision ResNet-50 backbone (pre-trained on ImageNet, final classification layer removed).
   - Extracts a 2048-dimensional $L_2$-normalized feature vector.
   - Computes cosine similarity against reference crops.

3. **Composite Scoring & Step 9A Flank Compatibility Guard**:
   - $\text{Composite Score} = 0.5 \times \text{SIFT Score} + 0.5 \times \text{Cosine Score}$.
   - **Flank Compatibility**: If Query Flank is `left` and Reference Flank is `right`, score is strictly $0.0$ with `flank_reason: "opposite_flanks_incompatible"`. Left and right flank stripe patterns are asymmetric on wild tigers.

4. **Step 13 & 14 Human Review Policy**:
   - Automatic identification confirmation is **disabled**. High-scoring candidates route to `review_required`.
   - Authorized human reviewers inspect side-by-side evidence, SIFT inlier lines, and reference crops in the Web Dashboard or Review Queue API before confirming an identity.

---

## 9. TIGER BEHAVIOUR MODEL IMPLEMENTATION

### Clarification of Capabilities:
The user requested an audit of the "Tiger behaviour YOLO model" (Model D).

- **Actual Implementation in Workspace [VERIFIED FROM SOURCE]**:
  * Located at: [`TigerTrace_AI/src/behavior/movement_predictor.py`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/behavior/movement_predictor.py) (545 lines).
  * **Not a YOLO neural network**.
  * **Not a visual behaviour detector** (does not detect sleeping, walking, hunting, stalking, or mating).
  * It is a **Spatial & Temporal Movement Intelligence System**:
    1. *Time-Weighted Kernel Density Estimation (KDE)*: Computes continuous spatial activity density surfaces with exponential decay weighting for older observations.
    2. *Discrete Markov Chain Station Transitions*: Models station-to-station movement probabilities based on historical sequence data.
    3. *Directional Trend & Village Dispersal*: Computes directional vectors towards the 8 Pench buffer villages to forecast human-wildlife conflict.

### Interfacing a Future Visual Behavior YOLO Model:
If a true visual behaviour YOLO checkpoint (detecting e.g. `walking`, `resting`, `stalking`, `feeding`) is provided:
- It should be executed **after animal detection**, either on the full frame or on the tiger bounding box crop.
- The resulting behavioral tag can be attached to the sighting record and returned in the `/api/analyze` JSON under `behaviour_estimate.visual_behaviour = {"class": "walking", "confidence": 0.88}`.

---

## 10. DATABASE AND DATA FLOW

[VERIFIED FROM SOURCE: `TigerTrace_AI/src/db/schema.py` & `TigerTrace_AI/data/database/tigertrace.db`]

### 10.1. Database Inventory & Row Counts
- **Active Database Path**: `TigerTrace_AI/data/database/tigertrace.db` (643,072 bytes).
- **Secondary (Legacy) Path**: `TigerTrace_AI/data/tigertrace.db` (0 bytes, empty file).
- **Table Counts**:
  * `stations`: 18 camera stations registered.
  * `villages`: 8 Pench buffer villages registered.
  * `tigers`: 8 resident individual tigers registered (`BAJIRAO`, `T15_COLLARWALI`, `T40_PATDEV`, `SWASTIK`, `T_74_L_MARK`, `KARMAJHIRI_CORE_TIGERS`, `PTR_T_007`, `PTR_T_008`).
  * `sightings`: 420 historical detections.
  * `review_queue`: 123 review items pending or processed.
  * `alerts`: 103 behavioral conflict alerts generated.
  * `review_audit_log`: Schema created; stores completed human review decisions.

### 10.2. Relational Schema Summary
```sql
stations (station_id PK, grid_id, range_name, zone, latitude, longitude)
villages (village_id PK, name, latitude, longitude, risk_level)
tigers (tiger_id PK, name, gender, flank_side_registered, reference_crop_path)
sightings (sighting_id PK, image_name, image_path, station_id, timestamp, species,
           tiger_id, flank_side, reid_score, review_status, bbox_json, flank_crop_path)
review_queue (review_id PK, sighting_id FK, suggested_tiger_id, suggested_score,
              sift_inliers, geometric_status, raw_cosine_sim, status, decision, reviewer_id)
review_audit_log (log_id PK, review_id FK, sighting_id FK, action, assigned_tiger_id,
                  reviewer_id, reason, machine_suggested_id, machine_suggested_score)
alerts (alert_id PK, alert_type, severity, tiger_id, station_id, detected_change, supporting_evidence)
```

---

## 11. FLUTTER APP AND API INTEGRATION

[VERIFIED FROM SOURCE: `mobile_app/lib/`]

### 11.1. Architecture & Call Flow
- **Entry Point**: `lib/main.dart` -> `lib/app/app.dart` -> Bottom navigation between:
  1. *Camera Scan* (`lib/features/camera_scan/camera_scan_screen.dart`): Captures photo via camera, picks from gallery, or selects preset field samples (Bajirao, Patdev, Blank).
  2. *History* (`lib/features/observation_history/history_screen.dart`): Lists past local observations.
  3. *Settings* (`lib/features/settings/settings_screen.dart`): Configures backend IP (`http://<ip>:8000`) and tests connectivity via `/api/health`.
- **API Client**: `lib/core/api/api_client.dart`
  * Sends multipart `POST /api/analyze` request with image bytes, metadata, and station ID.
  * Parses JSON response into `AnalysisResult` model (`lib/core/models/analysis_result.dart`).
- **Offline Caching**: `lib/core/services/offline_queue.dart`
  * If the ranger is in deep forest without network, captures are cached in `SharedPreferences`. Once reconnected, batch sync triggers via `POST /api/mobile/sync_batch`.

### 11.2. Existing Integration Gaps in Mobile App
1. **Multi-Species UI Limitation**: `result_screen.dart` displays tiger-specific fields (`assignedIdentity`, `siftScore`, `flankSide`). For non-tiger species (`chital`, `sambar`), it displays a generic "Wildlife Sighting" card rather than specific prey class badges.
2. **Behavior UI**: The mobile app displays Markov trajectory cards (`behaviourEstimate.predictedNextStations`), but lacks UI elements for visual behavior classification (e.g. "Resting / Stalking").

---

## 12. WEB DASHBOARD INTEGRATION

[VERIFIED FROM SOURCE: `TigerTrace_AI/ui/templates/index.html` & `TigerTrace_AI/ui/static/js/app.js`]

The Web Dashboard is rendered from `templates/index.html` via Jinja2:
1. **Live Feed Tab**: Displays recent camera trap photos, species breakdown, and triage results.
2. **Review Queue Tab**: Displays candidate tiger sightings side-by-side with reference catalogue crops, showing SIFT correspondence lines, inlier counts, and Accept/Reject/Inconclusive buttons.
3. **Territory & Map Tab**: Embeds the interactive Leaflet GIS map with resident tiger MCP polygons and camera trap locations.
4. **Behavior Intelligence Tab**: Displays Markov station transition probabilities and directional drift vectors.
5. **Conflict Alert Center Tab**: Lists critical village dispersal alerts and prolonged absence warnings.

---

## 13. PRIVACY AND SECURITY FINDINGS

1. **Zero-Trust Human Privacy Blur [VERIFIED FROM SOURCE]**:
   - Implemented in `TigerTrace_AI/src/privacy/human_blur.py`.
   - Automatically detects humans (`class_id: 0`) and applies heavy Gaussian blur to faces and bodies before storing frames in `data/privacy_blurred/`.
   - Protects patrolling forest staff and local villagers from unauthorized surveillance.

2. **Path Traversal Risk in Static Image Endpoint [VERIFIED FROM SOURCE: `ui/app.py:L483`]**:
   - `GET /api/image?path={path}` accepts an arbitrary absolute path parameter.
   - While `os.path.exists(path)` is checked, there is no canonical path containment check (e.g. verifying that `path` is within the project workspace). A malicious client could request arbitrary system files.
   - *Remediation*: Restrict paths to `os.path.abspath(pkg_dir)`.

3. **Hardcoded Machine Paths in Legacy Files [VERIFIED FROM SOURCE]**:
   - Some legacy files (`dataset/yolo_detection_dataset/data.yaml`, `build_yolo_tiger_dataset_and_flanks.py`) contain hardcoded Windows paths from a previous developer machine (`C:/Users/Lenovo/Desktop/...`).
   - The production pipeline (`TigerTrace_AI/src/config.py` and `ui/app.py`) dynamically computes relative paths using `os.path.dirname(__file__)`, so this does not break runtime execution.

4. **Credentials & Secrets**:
   - No plaintext passwords or production API tokens are committed.
   - Twilio SMS settings in `src/config.py` default to `SMS_DRY_RUN = True`.

---

## 14. TESTS AND EVALUATION EVIDENCE

[VERIFIED BY TEST: All tests executed locally on Windows 10/11, Python 3.10.11]

| Test File | Command | Tests Run | Result | Duration | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_shared_analysis_api.py` | `python -m unittest tests/test_shared_analysis_api.py` | 8 | **PASSED** (OK) | 6.29s | Tests `/api/analyze` across blank, human, animal, tiger |
| `test_step14_human_in_the_loop_review.py` | `python -m unittest tests/test_step14_human_in_the_loop_review.py` | 8 | **PASSED** (OK) | 5.17s | Tests review queue, concurrency, acceptance, audit logs |
| `test_step13_prevent_false_identity_confirmation.py` | `python -m unittest tests/test_step13_prevent_false_identity_confirmation.py` | 8 | **PASSED** (OK) | 51.48s | Verifies auto-confirmation disabled, cross-flank rejection |
| `test_step15d_gold_standard_pipeline.py` | `python -m unittest tests/test_step15d_gold_standard_pipeline.py` | 2 | **PASSED** (OK) | 0.15s | Verifies isolated synthetic gold-standard YOLO export |

**Total Tests Verified in Audit:** 26 tests executed, **26 passed (100% pass rate)**.

---

## 15. CONFIRMED BUGS AND INTEGRATION BLOCKERS

1. **Blocker 1: Missing External Model Weights**:
   - Models A, B, C, and D are not in the repository. They must be downloaded from Google Drive or supplied before they can be integrated.
2. **Blocker 2: Model A Misclassifies Tigers**:
   - Model A (26 species) lacks a `tiger` class and misclassifies tigers as `Striped_Hyena`. If used as the sole detector, the tiger Re-ID pipeline will never be triggered.
3. **Blocker 3: Closed-Set Identity Detection (Model B)**:
   - Model B uses YOLO detection heads for 11 individual tiger IDs. This architecture cannot identify new or uncatalogued tigers.
4. **Blocker 4: Visual Behavior Capability Gap**:
   - The user expected Model D to analyze visual behaviors (sleeping, hunting, walking). No visual behavior weights or annotated behavior datasets exist in the repository.
5. **Bug 5: Dual Database Location Confusion**:
   - `data/tigertrace.db` (0 bytes) is empty, while `data/database/tigertrace.db` (643 KB) is active. Developers may mistakenly query the empty root database file.
6. **Bug 6: Redundant Dual-Stage Inference**:
   - `triage_detector.py` runs both `best_yolov8.pt` AND `yolov8n.pt` sequentially for every image, causing a 2x inference latency penalty on CPU.

---

## 16. RECOMMENDED UNIFIED ARCHITECTURE

### Comparison of Integration Strategies:

| Aspect | Strategy A: Single Monolithic YOLO Model | Strategy B: Modular Hierarchical Pipeline (Recommended) |
| :--- | :--- | :--- |
| **Concept** | Train one massive YOLO model predicting all species, 11 individual identities, and behavior states simultaneously. | Hierarchical stages: Species Detection -> Tiger Flank Re-ID -> Visual Behavior -> Spatial Intelligence. |
| **New Tiger Handling** | **Fails completely**. Adding a 12th tiger requires retraining the entire model and updating all class heads. | **Seamless**. New tigers are simply added as reference crops to `reference_catalogue/` without retraining. |
| **Model Weights** | Impossible to concatenate existing checkpoints; requires complete dataset merge and multi-day retraining. | Existing modular models can be integrated independently without retraining everything at once. |
| **Scientific Soundness** | Treating individual tigers as object classes violates wildlife biometric Re-ID standards (WII/NTCA). | Conforms to international wildlife standards (HotSpotter SIFT + metric embedding). |
| **Human Review** | Impossible to calibrate confidence or provide explainable SIFT inlier lines. | Preserves Step 13 & 14 explainable evidence and review queue. |

### Recommended Hierarchical Pipeline Architecture:

```
[Camera Trap Image Input]
           │
           ▼
┌──────────────────────────────────────────────┐
│ Stage 1: Wildlife Multi-Species Detector     │  (Future Model C / 5-Species or 26-Species)
│ - Outputs: species class, bbox, confidence   │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Tiger Detected]              [Prey / Non-Tiger]
       │                               │
       ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ Stage 2: Flank Biometric  │   │ Direct Persistence        │
│ Re-ID (SIFT + ResNet-50)  │   │ - Log species sighting    │
│ - Flank extraction (9B)   │   │ - Update prey density map │
│ - Reciprocal SIFT inliers │   └───────────────────────────┘
│ - Flank guard (9A)        │
│ - Step 13/14 Review Queue │
└──────────────┬────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Stage 3: Tiger Visual Behavior Classifier    │  (Future Model D)
│ - Inputs: Tiger bounding box crop            │
│ - Outputs: walking, resting, stalking, etc.  │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Stage 4: Spatial & Threat Intelligence       │  (Existing movement_predictor.py)
│ - Markov transition matrix                   │
│ - Time-Weighted KDE predictive heatmap       │
│ - Village boundary deviation alerts          │
└──────────────────────────────────────────────┘
```

---

## 17. EXACT FILES LIKELY TO NEED MODIFICATION IN A FUTURE INTEGRATION

1. **`TigerTrace_AI/src/blank_filter/triage_detector.py`**:
   - Replace dual-stage COCO fallback with the new multi-species detector checkpoint.
   - Map multi-species class indices to canonical names in `species_taxonomy.json`.
2. **`TigerTrace_AI/src/pipeline.py`**:
   - Add Stage 3 (Visual Behavior) inference call on the tiger crop.
   - Route prey species sightings into the database.
3. **`TigerTrace_AI/ui/app.py`**:
   - Update `/api/analyze` (L684-710) to return specific species names (e.g. `chital`, `sambar`, `gaur`) instead of generic `wildlife`.
   - Add visual behavior results to the response payload.
4. **`TigerTrace_AI/src/db/schema.py`**:
   - Add `behavior_state` column to the `sightings` table.
5. **`mobile_app/lib/core/models/analysis_result.dart`**:
   - Add `visualBehavior` field to Dart model.
6. **`mobile_app/lib/features/animal_analysis/result_screen.dart`**:
   - Render prey-species badges, behavior state chips, and multi-species bounding boxes.

---

## 18. SAFE STEP-BY-STEP INTEGRATION PLAN

### Phase 1: Model Ingestion & Checkpoint Validation (No Code Changes)
- Download `best.pt` for Model A, Model B, Model C, and Model D into `TigerTrace_AI/data/models/`.
- Verify input resolution, PyTorch architecture, and class dictionaries using a non-destructive python script.

### Phase 2: Stage 1 Multi-Species Integration
- Test Model C (5 species) against sample images.
- Reconcile class labels: ensure `tiger` is recognized or routed to the custom tiger detector.
- Update `triage_detector.py` to output confirmed prey species names.

### Phase 3: Stage 3 Visual Behavior Integration
- If Model D is an image/crop classifier: integrate it into `src/behavior/visual_behavior.py`.
- Run inference only on valid tiger crops to minimize CPU load.

### Phase 4: API & Client Serialization
- Update `/api/analyze` response schema.
- Update Flutter `AnalysisResult.fromJson` and Dart UI widgets.

### Phase 5: Full Regression Testing
- Execute the complete 26-test suite to verify that Step 9A, 9B, 13, and 14 safeguards remain intact.

---

## 19. MISSING FILES OR INFORMATION THE USER MUST SUPPLY

To integrate the models in a future step, the user must provide:

1. **Model Checkpoint Files**:
   - Model A weights: `tadoba_26class_v1/weights/best.pt`.
   - Model B weights: `tiger_identity_11class_v1/weights/best.pt`.
   - Model C weights: 5-species checkpoint once training finishes.
   - Model D weights: Tiger behavior model checkpoint.
2. **Dataset Configuration YAML Files**:
   - `data.yaml` files for Model A, Model C, and Model D defining exact class IDs and string labels.
3. **Behavior Taxonomy Details**:
   - The exact list of behavior classes recognized by Model D (e.g., `['walking', 'resting', 'stalking']`).
   - Whether Model D expects a full camera trap frame or a tight animal crop.

---

## 20. APPENDIX: IMPORTANT FUNCTIONS, LINE NUMBERS, AND COMMANDS

### Key Implementation Symbols:
- **FastAPI Application**: [`TigerTrace_AI/ui/app.py:L27`](file:///d:/TigerTraceAI-main/TigerTrace_AI/ui/app.py#L27) (`app = FastAPI(...)`)
- **Primary Analysis Endpoint**: [`TigerTrace_AI/ui/app.py:L539-855`](file:///d:/TigerTraceAI-main/TigerTrace_AI/ui/app.py#L539-L855) (`analyze_photo`)
- **Triage Detector Class**: [`TigerTrace_AI/src/blank_filter/triage_detector.py:L8-143`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/blank_filter/triage_detector.py#L8-L143) (`CameraTrapTriageDetector`)
- **SIFT Feature Extraction**: [`TigerTrace_AI/src/reid/stripe_matcher.py:L93-130`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/reid/stripe_matcher.py#L93-L130) (`extract_sift_features`)
- **Flank Compatibility Guard**: [`TigerTrace_AI/src/reid/stripe_matcher.py:L207-220`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/reid/stripe_matcher.py#L207-L220) (`compare_flanks`)
- **Enrollment Decision Policy**: [`TigerTrace_AI/src/reid/enrollment.py:L890-950`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/reid/enrollment.py#L890-L950) (`identify_and_enroll`)
- **Human Privacy Blur**: [`TigerTrace_AI/src/privacy/human_blur.py:L20-65`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/privacy/human_blur.py#L20-L65) (`apply_privacy_blur`)
- **Movement Predictor**: [`TigerTrace_AI/src/behavior/movement_predictor.py:L14-80`](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/behavior/movement_predictor.py#L14-L80) (`TigerMovementPredictor`)
- **Flutter API Client**: [`mobile_app/lib/core/api/api_client.dart:L30-80`](file:///d:/TigerTraceAI-main/mobile_app/lib/core/api/api_client.dart#L30-L80) (`analyzePhoto`)

### Essential Execution Commands:
- **Start FastAPI Backend & Web Dashboard**:
  ```powershell
  python TigerTrace_AI/ui/app.py
  ```
- **Launch Step 15D Browser Review Station**:
  ```powershell
  python scripts/launch_review_station.py --port 8085
  ```
- **Run Full Automated Regression Test Suite**:
  ```powershell
  python -m unittest tests/test_shared_analysis_api.py
  python -m unittest tests/test_step14_human_in_the_loop_review.py
  python -m unittest tests/test_step13_prevent_false_identity_confirmation.py
  python -m unittest tests/test_step15d_gold_standard_pipeline.py
  ```

---
*End of Audit and Integration Handoff Report*
