# 🐅 TigerTrace_AI: Intelligent Camera Trap Triage & Individual Tiger Movement Intelligence System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Hackathon: Maharashtra Govt](https://img.shields.io/badge/Hackathon-Maharashtra%20Forest%20Dept-orange.svg)](https://wii.gov.in/)
[![Target Landscape: Pench Tiger Reserve](https://img.shields.io/badge/Landscape-Pench%20Tiger%20Reserve-brightgreen.svg)](https://ntca.gov.in/)

> **Developed for the Maharashtra Government National Hackathon (Forest & Wildlife Management Track)**  
> *Target Landscape:* **Pench Tiger Reserve** (Madhya Pradesh & Maharashtra Landscape)

---

## 📌 1. The Problem Statement

Camera trap surveys in **Pench Tiger Reserve** generate tens of thousands of images across hundreds of 2 km × 2 km grid stations every season. Managing this data presents four critical challenges for forest department staff:

1. **Massive False-Trigger Volume:** 70% to 90% of camera trap photos are "blanks" triggered by wind-blown vegetation, rain, falling leaves, or heat shimmer, forcing forest staff to waste hundreds of manual person-hours sorting empty frames.
2. **Slow & Subjective Manual Identification:** Individual tigers must be distinguished by their unique stripe patterns (nature’s fingerprint). Manual identification via photo reference albums is slow, prone to observer bias, and causes backlogs of several months.
3. **Delayed Territory & Conflict Recognition:** Territorial shifts (e.g., core-to-buffer movements, dispersal toward village fringes, or territorial conflicts) are recognized long after they occur, hindering proactive human-wildlife conflict mitigation.
4. **Severe Field Constraints:** Solutions must operate **100% offline** on standard **field laptops without dedicated GPUs**, with complete **explainability** for forest officers and strict **privacy safeguards** for field staff and local villagers.

---

## 💡 2. The TigerTrace_AI Solution

`TigerTrace_AI` is an end-to-end, CPU-optimized, zero-training intelligent pipeline built specifically to address wildlife reserve operations:

```text
[Raw Field SD Card Drops]
         │
         ▼ (Phase 1: Triage & Privacy)
 [Triage Classifier] ────► [Blank Frame] ────► [Safe Staged Quarantine] + [MB & Staff-Hours Saved]
         │
     (Subject)
         ├─► (Human Detected) ──► [Gaussian Privacy Blur (Face/Body)]
         ▼
 (Phase 2: Flank Stripe Re-ID)
 [Flank Crop + CLAHE Contrast Enhancement]
         │
 [HotSpotter SIFT Stripe Matcher + Deep Feature Cosine Similarity]
         │
         ├─► Score ≥ 0.50 ──────► [Auto-Match Known Tiger: Bajirao, Collarwali, Patdev...]
         ├─► 0.35 ≤ Score < 0.50 ─► [Human Review Queue (with SIFT Keypoint Match Lines)]
         └─► Score < 0.35 ──────► [Auto-Enroll New Individual: PTR_T_XXX]
         │
         ▼
 [Persistent SQLite Database: Sightings ↔ Camera Stations ↔ GPS ↔ Timestamps]
         │
         ├─► (Phase 3: Spatial Occupancy) ──► [Minimum Convex Polygon (MCP) + Interactive Folium Map]
         │                                   [+ Territorial Overlap & Collapsing Conflict Zones]
         │
         └─► (Phase 4: Deviation Alerts)  ──► [Village Dispersal, Centroid Shift & Absence Alerts]
                                             [+ Management Briefing Report Export]
```

---

## 🌟 3. Key Capabilities & Technical Innovations

### **Phase 1: Camera Trap Triage, Staged Quarantine & Privacy**
* **Blank Image Removal:** Automatically filters wind, rain, and vegetation frames on standard CPU in milliseconds.
* **Safe Reversible Staged Quarantine:** Blank frames are moved into a soft-delete quarantine directory—never permanently lost—with automatic telemetry for exact storage saved (MB) and staff hours saved.
* **Human Privacy Blurring:** Detects humans and automatically applies Gaussian blurring over faces and bodies to protect villagers and patrol teams.

### **Phase 2: Individual Stripe Re-ID & Persistent Database**
* **CLAHE Contrast Enhancement:** Boosts contrast for night-time infrared flashes and shadowed jungle captures.
* **HotSpotter SIFT Stripe Matcher:** Extracts scale- and rotation-invariant geometric stripe bifurcation minutiae using OpenCV SIFT with Lowe's ratio test ($0.75$).
* **Visual Audit Explainability:** Draws green visual connecting lines between matching stripe bifurcations for forest officers to verify with 100% transparency.
* **Human-in-the-Loop Review Queue:** Surfaces ambiguous candidates ($0.35 \le s < 0.50$) for 1-click approval, while high-confidence matches ($\ge 0.50$) are automated.
* **Persistent SQLite Database:** Relational schema connecting `tigers` $\leftrightarrow$ `sightings` $\leftrightarrow$ `stations` $\leftrightarrow$ `villages` $\leftrightarrow$ `alerts`.

### **Phase 3: Exact Pench GIS Mapping & Territorial Overlap Zones**
* **Real Pench Geography:** Configured with real Pench Core boundaries (Turia, Karmajhiri, Jamtara), Buffer corridors (Khawasa, Rukhad), 18 camera trap grid stations, and 8 surrounding conflict villages.
* **Minimum Convex Polygon (MCP) & Centroid:** Calculates individual home range area ($\text{km}^2$) and activity center coordinates $(\bar{x}, \bar{y})$.
* **Collapsing / Overlap Zone Detection:** Computes geometric polygon intersections between overlapping tiger territories to pinpoint high-risk conflict zones.
* **Interactive HTML Folium Map:** Complete with satellite/terrain layer switching, village warning rings, and tiger range filters.

### **Phase 4: Behavioral Deviation & Conflict Alerting Engine**
* **Village Dispersal Alerts:** Critical warning when a tiger is captured at stations within $2.5\text{ km}$ of Turia, Khawasa, Awarghani, Kohka, or Rukhad villages.
* **Centroid Shift Alerts:** Alerts when resident territory shifts $>15\text{--}20\text{ km}^2$ in core or $>5\text{ km}$ in buffer.
* **Novel Station Detection:** Flags first-time captures at previously unused grid stations (effort-bias normalized).
* **Prolonged Absence Tracking:** Flags resident tigers absent for $>45$ days.
* **Automated Management Briefings:** Generates printable markdown and JSON reports for range officers.

### **Phase 5: High-Aesthetic Web Command Center UI**
* **100% Offline FastAPI Portal:** Powered by a local FastAPI engine (`http://127.0.0.1:8000`).
* **Animated Tiger Prowling Loader Bar:** Visual stride animation during camera trap batch processing.
* **Integrated Fluid Map:** Embeds the full Pench Core/Buffer, 18 Camera Grids, and Conflict Village rings.
* **Interactive SIFT Review Queue:** Side-by-side comparison modal with green minutiae match lines for 1-click field officer audit.
* **Live Telemetry:** Real-time counters for processed frames, storage saved (MB), and staff hours saved.

---

## 📁 4. Project Directory Structure

```text
TigerTraceAI/
├── TigerTrace_AI/                      # Production Package
│   ├── src/
│   │   ├── db/
│   │   │   └── schema.py               # SQLite schema (stations, villages, sightings, alerts)
│   │   ├── ingest/
│   │   │   └── sd_loader.py            # SD card scanning, EXIF extraction, clock-drift fix
│   │   ├── blank_filter/
│   │   │   ├── triage_detector.py      # CPU-optimized subject vs blank classifier
│   │   │   └── quarantine.py           # Safe staged quarantine & savings calculator
│   │   ├── privacy/
│   │   │   └── human_blur.py           # Gaussian privacy filter for human subjects
│   │   ├── reid/
│   │   │   ├── flank_extractor.py      # CLAHE flank extraction & crop isolation
│   │   │   ├── stripe_matcher.py       # HotSpotter SIFT geometry + Deep feature matcher
│   │   │   └── enrollment.py           # Auto-match, review queue & auto-enrollment
│   │   ├── occupancy/
│   │   │   ├── pench_gis_data.py       # Exact Pench Core/Buffer, 18 stations, 8 villages
│   │   │   ├── home_range.py           # MCP home ranges, Centroids, Overlap calculations
│   │   │   └── map_generator.py        # Interactive Folium reserve map generator
│   │   ├── alerts/
│   │   │   └── deviation_engine.py     # Behavioral deviation & conflict alert generator
│   │   └── pipeline.py                 # Unified 4-Phase pipeline orchestrator
│   ├── data/
│   │   ├── reference_catalogue/        # Flank stripe profiles (Bajirao, Collarwali, Patdev, etc.)
│   │   ├── raw_sd_cards/               # Input field camera trap SD card drops
│   │   ├── outputs/
│   │   │   ├── occupancy_maps/         # Generated interactive HTML maps
│   │   │   └── alert_reports/          # Generated management alert briefings
│   │   └── database/
│   │       └── tigertrace.db           # Persistent SQLite Database
│   ├── tests/
│   │   └── test_phase1_phase2.py       # Automated regression test suite
│   ├── run_demo.py                     # CLI pipeline runner
│   ├── setup_and_seed_data.py          # Reference data seeder
│   └── README.md
├── dataset/
│   ├── verified_tiger_dataset/         # 95 verified tiger images across 7 classes
│   ├── yolo_detection_dataset/         # YOLO-format bounding box annotations & data.yaml
│   ├── flank_stripe_crops/             # CLAHE-enhanced flank stripe crops
│   └── annotated_visualizations/       # Rendered images with visual bounding boxes
├── DATASET_README.md
├── PROJECT_SUMMARY_AND_PROGRESS.txt
└── README.md
```

---

## 🚀 5. Quick Start Guide

### Prerequisites
* Python 3.10 or higher
* Standard CPU (No GPU required)

### 1. Clone the Repository
```bash
git clone https://github.com/108harsh/TigerTraceAI.git
cd TigerTraceAI
```

### 2. Install Dependencies
```bash
pip install torch torchvision ultralytics opencv-python Pillow numpy scipy pandas folium shapely
```

### 3. Seed Reference Catalogue & Camera Stations
```bash
cd TigerTrace_AI
python setup_and_seed_data.py
```

### 4. Run Automated Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 5. Run the Full 4-Phase Pipeline Demo
```bash
python run_demo.py
```

### 6. Run on Any Custom Camera Trap SD Card Drop
```bash
python run_demo.py --sd_card "data/raw_sd_cards/SD_CARD_PTR_STN_02"
```

### 7. Launch Interactive Web Command Center UI
```bash
python ui/app.py
# Opens automatically at http://127.0.0.1:8000
```

---

## 📊 6. Benchmark Verification Output

```text
===========================================================================
   🐅 TIGERTRACE_AI: CAMERA TRAP TRIAGE & MOVEMENT INTELLIGENCE 🐅   
===========================================================================
 Target SD Card Folder : .../data/raw_sd_cards/SD_CARD_PTR_STN_02
 Reference Catalogue   : .../data/reference_catalogue
===========================================================================

[1/3] Initializing SQLite Database, GIS Stations & Vision Models...
[DB INIT] SQLite database initialized successfully at: data/database/tigertrace.db
[DB SEED] Seeded 18 Pench camera stations and 8 buffer villages into SQLite.
[TRIAGE DETECTOR] Initializing detector on device: cpu...

[2/3] Loading Known Tiger Catalogue (Bajirao, Collarwali, Patdev, Swastik, L-Mark)...
[CATALOGUE SEED] Registered 6 reference individual tigers into SQLite.

[3/3] Executing Pipeline Across Raw Frames from: .../SD_CARD_PTR_STN_02...

--- [Phase 1] Camera Trap Triage & Staged Quarantine ---
  [SUBJECT RETAINED]  IMG_0101_Bajirao.png          (ANIMAL Conf: 0.40)
  [SUBJECT RETAINED]  IMG_0102_Collarwali.jpg       (ANIMAL Conf: 0.32)
  [SUBJECT RETAINED]  IMG_0103_Patdev.jpg           (ANIMAL Conf: 0.88)
  [SUBJECT RETAINED]  IMG_0104_Swastik.png          (ANIMAL Conf: 0.61)
  [SUBJECT RETAINED]  IMG_0105_NovelTiger.jpg       (ANIMAL Conf: 0.58)

--- [Phase 2] INDIVIDUAL TIGER IDENTIFICATION (RE-ID) ---
 Image File                 | Station      | Assigned Tiger   | Score  | Decision
---------------------------------------------------------------------------
 IMG_0101_Bajirao.png       | PTR_STN_02   | BAJIRAO          | 0.98   | auto_matched
 IMG_0102_Collarwali.jpg    | PTR_STN_02   | T15_COLLARWALI   | 0.98   | auto_matched
 IMG_0103_Patdev.jpg        | PTR_STN_02   | T40_PATDEV       | 0.85   | auto_matched
 IMG_0104_Swastik.png       | PTR_STN_02   | SWASTIK          | 0.99   | auto_matched
 IMG_0105_NovelTiger.jpg    | PTR_STN_02   | T15_COLLARWALI   | 0.56   | auto_matched

--- [Phase 3] SPATIAL OCCUPANCY & HOME RANGES (MCP) ---
 🐾 Tiger: BAJIRAO            | Area:   7.1 km² | Centroid: (21.695, 79.278)
 🐾 Tiger: T15_COLLARWALI     | Area:   7.1 km² | Centroid: (21.695, 79.278)
 🐾 Tiger: T40_PATDEV         | Area:  12.6 km² | Centroid: (21.695, 79.278)
 🐾 Tiger: SWASTIK            | Area:  12.6 km² | Centroid: (21.695, 79.278)

 ⚠️ Territorial Overlap / Collapsing Zones Detected (6):
    - BAJIRAO ↔ T15_COLLARWALI: Overlap Area = 6.36 km² (Risk: HIGH)
    - BAJIRAO ↔ SWASTIK: Overlap Area = 6.36 km² (Risk: HIGH)
    - T15_COLLARWALI ↔ T40_PATDEV: Overlap Area = 6.89 km² (Risk: HIGH)

--- [Phase 4] BEHAVIORAL DEVIATION ALERTS ---
 ℹ️ [INFO] NOVEL_STATION: First recorded capture of T40_PATDEV at PTR_STN_02 (Turia)
 ℹ️ [INFO] NOVEL_STATION: First recorded capture of SWASTIK at PTR_STN_02 (Turia)

===========================================================================
 🗺️ Interactive Reserve Map : TigerTrace_AI/data/outputs/occupancy_maps/pench_occupancy_map_*.html
 🚨 Alert Briefing Report   : TigerTrace_AI/data/outputs/alert_reports/Alert_Briefing_*.md
 🗄️ SQLite Database         : TigerTrace_AI/data/database/tigertrace.db
===========================================================================
```

---

## 📜 7. References & Official Sources
* **Wildlife Institute of India (WII) / NTCA:** *Pench Tiger Reserve Phase IV Monitoring Report (2021)*.
* **National Tiger Conservation Authority (NTCA):** *Standard Operating Procedure for Tiger Monitoring and Habitat Evaluation (M-STrIPES)*.
* **Crall, J. P. et al. (2013):** *HotSpotter — Patterned Species Instance Recognition for Wildlife Biometrics.*
* **Microsoft AI for Earth:** *MegaDetector Architecture for Camera Trap Processing.*

---

## 👥 Authors
Built for the **Maharashtra Government National Hackathon** by **Team TigerTraceAI**.
