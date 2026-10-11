# 🐅 NETRAVAN: Autonomous Wildlife Intelligence & Spatial Telemetry Platform
### *Central Wildlife Biometrics & Habitat Cartography — Tadoba-Andhari Tiger Reserve (TATR)*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TypeScript-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Target Landscape: Tadoba-Andhari](https://img.shields.io/badge/Landscape-Tadoba--Andhari%20Tiger%20Reserve%20(TATR)-brightgreen.svg)](https://mytadoba.org/)

---

## 🌿 1. Overview & Vision

**NETRAVAN** is an offline-first, enterprise-grade autonomous wildlife intelligence platform engineered for modern forest departments, conservation biologists, and field rangers. Deployed for the critical ecosystem of **Tadoba-Andhari Tiger Reserve (TATR)**, Maharashtra, NETRAVAN transforms raw camera-trap photo drops into actionable spatial biometrics, ethological behavior assessments, and predictive human-wildlife conflict mitigation in real time.

```text
[Raw Field Camera SD Drops]
         │
         ▼ (Stage 1: Multi-Trophic Triage & Edge Vision)
 [YOLOv8-Tadoba-Vision] ──► [Blank Frames] ──► [Quarantine Storage (Saves 80% Disk & Hours)]
         │
     (Identified)
         ├─► [Human Detected] ──► [Automated Gaussian Privacy Redaction]
         ▼
 (Stage 2: Biometric Stripe Re-Identification)
 [Automated Flank Crop + CLAHE Contrast Normalization]
         │
 [HotSpotter SIFT Keypoint Inliers + ResNet-50 Deep Feature Ensemble]
         │
         ├─► Confidence ≥ 0.95 ──► [Direct Individual Identification: Chota Dadhiyal, Maya, Matkasur...]
         ├─► 0.40 ≤ Conf < 0.95 ─► [Human-in-the-Loop Field Review Queue]
         └─► Conf < 0.40 ────────► [Propose New Individual Registration: TATR_T_XXX]
         │
         ▼
 (Stage 3: Scientific Ethogram & Behavioral Assessment)
 [Locomotion Biomechanics: Alert Standing (4-Point Stance) + Cervical Alignment]
 [Olfactory & Sensory Audit: Scent-Boundary Inspection + 45° Forward Pinnae Vigilance]
 [Physical Vigor: Body Condition Score (BCS 4.5/5.0) + Anthropogenic Stress Index]
         │
         ▼
 (Stage 4: Spatial GIS Telemetry & Movement Forecasting)
 [TATR Interactive Cartography: 24 Camera Stations + 21 Safari Gates + Core/Buffer Zones]
 [Continuous Linear Waypoint Interpolation + Scrubber Playback Animation]
 [Markov Chain Transition Matrix: 74.2% Probability Dispersal to CT-C4 (Pandharpauni)]
 [Human-Wildlife Conflict Boundary Warning: Moharli Settlement Buffer Clearance]
```

---

## ✨ 2. Key Capabilities & Technical Architecture

### 🔬 A. AI Recognition Studio & Stripe Biometrics
- **YOLOv8-Tadoba-Vision Detector**: High-precision offline object detection tuned for Indian carnivores and ungulates.
- **Biometric Flank Re-ID**: HotSpotter SIFT (Scale-Invariant Feature Transform) keypoint inliers combined with ResNet-50 cosine distance to identify individual tigers by unique stripe geometry.
- **Flank Orientation Guard**: Prevents erroneous left-to-right flank mismatches.
- **Privacy Redaction**: Automated facial/body Gaussian blur on human detections to protect forest staff and local communities.

### 📋 B. Scientific Ethogram & Field Behavioral Report
- **Posture & Biomechanics**: Automated stance diagnosis differentiating between alert standing (4-point ground contact), linear walking patrol, scent marking, and resting.
- **Cervical & Head Angle**: Diagnoses cranial elevation and horizontal gaze orientation (e.g. 12° upward pitch scanning over knee-high understory).
- **Olfactory & Territorial Signals**: Identifies scent-rub sampling, flehmen expressions, and border boundary inspection.
- **Aural & Ear Posture (Pinnae)**: Tracks 45° forward-facing acoustic vigilance toward vegetative corridors.
- **Caudal Dynamics (Tail)**: Evaluates tail carriage (e.g. low caudal with 15° terminal curl signifying calm territorial dominance).
- **Body Condition Scoring (BCS)**: Evaluates muscular definition, hydration, abdominal contour, and absence of territorial combat injuries.
- **One-Click Export**: Instant generation and download of formatted field reports (`.md` / PDF).

### 🗺️ C. Tadoba GIS Cartography & Animated Movement
- **Real Tadoba-Andhari Boundaries**: Accurate GeoJSON layers for TATR Core Zone (National Park) and Buffer Territory.
- **Infrastructure & Waterbodies**:
  - 21 Safari Tourism Gates (Moharli, Kolara, Navegaon, Khutwanda, Zari, Pangdi, etc.)
  - Key Water Reservoirs (Tadoba Lake, Kolsa Lake, Telia Dam, Irai Dam)
  - 24 Strategic Camera Trap Stations (`CT-NW1`, `CT-N1`, `CT-C1`, `CT-C4`, `CT-W1`, `CT-E1`, etc.)
- **Continuous Animated Waypoint Tracking**:
  - Smooth linear interpolation between timestamps (`getPositionAtTime`).
  - Interactive timeline scrubber with Play/Pause and speed multiplier (1x, 2x, 5x).
  - Active individual selector: **Maya (T-1)**, **Chhota Matka (T-3)**, **Matkasur (T-2)**, **T-54 (T-4)**, Leopards (**Ghost**, **Scarface**), Sloth Bear (**Baloo**).
  - Photo sighting nodes with enlarged camera trap inspection lightboxes.

### ⚡ D. Spatial Markov Movement Forecasting & Coexistence
- **Transition Probabilities**: Markov chain transition matrices forecasting the next likely camera station with quantitative probabilities (e.g. 74.2% toward Pandharpauni Grasslands `CT-C4`).
- **Settlement Proximity Alerts**: Real-time vector distance calculation to fringe villages (e.g. Moharli Buffer Settlement) for proactive human-wildlife conflict avoidance.

---

## 🛠️ 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend Web UI** | React 19, TypeScript, Vite, Tailwind CSS, Glassmorphic Design System, Leaflet GIS |
| **Backend API** | FastAPI, Uvicorn, Python 3.10+, SQLite3 Spatial Schema |
| **AI / Computer Vision** | Ultralytics YOLOv8, OpenCV (CLAHE, SIFT, Affine RANSAC), PyTorch, Torchvision ResNet-50 |
| **Spatial / Math** | SciPy, NumPy, GeoJSON, Minimum Convex Polygon (MCP), Markov Transition Chains |

---

## 🚀 4. Quickstart & Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ & npm
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/atharvajoshi189/Netravan.git
cd Netravan
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run SQLite database migration & Tadoba data seed
python scripts/migrate_tadoba_db.py

# Launch the FastAPI Backend Server
python Netravan_AI/ui/app.py
```
*The backend API will be available at:* `http://127.0.0.1:8000/`  
*API Swagger Documentation:* `http://127.0.0.1:8000/docs`

### 3. Frontend Web UI Setup
```bash
cd web_ui

# Install dependencies
npm install

# Start the Vite development server
npm run dev -- --host 127.0.0.1 --port 3000
```
*Access the Web UI in your browser at:* `http://localhost:3000/`

---

## 📂 5. Project Directory Structure

```text
Netravan/
├── Netravan_AI/                # Core AI Engine & Backend Server
│   ├── data/
│   │   ├── database/           # SQLite database (tigertrace.db)
│   │   ├── models/             # Trained YOLOv8 weights (best_yolov8.pt)
│   │   └── taxonomy/           # Canonical 17-class species taxonomy
│   ├── src/
│   │   ├── behavior/           # Movement predictor & Markov transition engine
│   │   ├── db/                 # SQLite schema & station seeding
│   │   ├── occupancy/          # GIS layers, home range, and MCP calculators
│   │   ├── reid/               # HotSpotter SIFT matcher & deep feature ensemble
│   │   └── triage/             # YOLOv8 species detector & privacy redaction
│   └── ui/
│       └── app.py              # FastAPI application & REST endpoints
├── web_ui/                     # Modern React 19 + TypeScript Frontend
│   ├── public/data/            # Tadoba GeoJSON, gates, cameras, animals, waterbodies
│   └── src/
│       ├── components/         # Glassmorphic UI & Scientific Ethogram Modal
│       ├── pages/              # AI Recognition Studio, Movement Map, Command Center
│       └── services/           # REST API client
├── scripts/                    # Database migrations and seed utilities
└── requirements.txt            # Python dependencies
```

---

## 📄 6. License & Acknowledgements

Developed for modern wildlife reserve management under the MIT License.  
Special thanks to the field researchers, forest guards, and data contributors working tirelessly across the **Tadoba-Andhari Tiger Reserve** landscape.
