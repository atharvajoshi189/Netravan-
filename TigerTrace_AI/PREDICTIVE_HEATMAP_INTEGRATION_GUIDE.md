# 🐅 TigerTrace AI — Predictive Movement Heatmap & Behavioral Intelligence
## Complete Integration & Handover Guide (for Antigravity IDE)

This guide contains everything required to integrate the **Behavioral Movement Prediction & Time-Weighted KDE Heatmap** feature into any instance of **TigerTrace AI**.

---

## 📁 1. Files to Share / Copy

### 🆕 New Files to Send:
```text
TigerTrace_AI/
├── src/
│   └── behavior/
│       ├── __init__.py
│       └── movement_predictor.py      <-- Core KDE + Markov Chain movement predictor
└── tests/
    └── test_movement_predictor.py     <-- Unit test suite (5 test cases)
```

### ✏️ Existing Files with Updates:
```text
TigerTrace_AI/
├── src/
│   ├── occupancy/
│   │   └── map_generator.py           <-- Added Esri Satellite/OSM tiles + HeatMap layers
│   └── pipeline.py                    <-- Wired TigerMovementPredictor into Phase 3
└── ui/
    ├── app.py                         <-- Added /api/behavior_predictions route
    ├── templates/
    │   └── index.html                 <-- Added 🔮 Predictive Heatmaps tab & filter buttons
    └── static/
        ├── css/style.css              <-- Added .pred-card & glassmorphic styles
        └── js/app.js                  <-- Added loadBehaviorPredictions() & cards renderer
```

---

## 📂 2. Full Project Folder Structure

```text
TigerTrace_AI/
├── data/
│   ├── database/
│   │   └── tigertrace.db
│   ├── models/
│   │   ├── best_yolov8.pt
│   │   └── yolov8n.pt
│   ├── outputs/
│   │   ├── alert_reports/
│   │   └── occupancy_maps/
│   ├── raw_sd_cards/
│   └── reference_catalogue/
├── src/
│   ├── alerts/
│   │   └── deviation_engine.py
│   ├── behavior/                      <-- [NEW FOLDER]
│   │   ├── __init__.py                <-- [NEW FILE]
│   │   └── movement_predictor.py      <-- [NEW FILE]
│   ├── blank_filter/
│   │   ├── quarantine.py
│   │   └── triage_detector.py
│   ├── db/
│   │   └── schema.py
│   ├── ingest/
│   │   └── sd_loader.py
│   ├── occupancy/
│   │   ├── home_range.py
│   │   ├── map_generator.py           <-- [UPDATED]
│   │   └── pench_gis_data.py
│   ├── privacy/
│   │   └── human_blur.py
│   ├── reid/
│   │   ├── enrollment.py
│   │   ├── flank_extractor.py
│   │   └── stripe_matcher.py
│   └── pipeline.py                    <-- [UPDATED]
├── tests/
│   ├── test_movement_predictor.py     <-- [NEW FILE]
│   └── test_phase1_phase2.py
├── ui/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css              <-- [UPDATED]
│   │   └── js/
│   │       └── app.js                 <-- [UPDATED]
│   ├── templates/
│   │   └── index.html                 <-- [UPDATED]
│   └── app.py                         <-- [UPDATED]
└── PREDICTIVE_HEATMAP_INTEGRATION_GUIDE.md
```

---

## ⚙️ 3. Prerequisites & Dependencies

Ensure the following packages are installed in the Python environment:
```bash
pip install scipy numpy folium shapely fastapi uvicorn ultralytics opencv-python Pillow dill
```

---

## 🛠️ 4. Code Implementation Details

### Step 1: Create `src/behavior/__init__.py`
```python
from .movement_predictor import TigerMovementPredictor

__all__ = ["TigerMovementPredictor"]
```

---

### Step 2: Create `src/behavior/movement_predictor.py`
This module computes:
1. **Time-weighted Kernel Density Estimation (KDE)**: $w_i = 2^{-\Delta t / 30}$ (30-day half-life decay).
2. **First-Order Discrete Markov Chain**: Transition probability matrix between camera stations.
3. **Sliding Directional Trend**: Centroid displacement ($\Delta x, \Delta y$), 8-point compass heading, and buffer village convergence detection.

---

### Step 3: Update `src/occupancy/map_generator.py`
Add the `add_predictive_heatmap_layer` method and include real satellite & street view tiles:
1. Add `folium.TileLayer(tiles="OpenStreetMap", name="🗺️ Detailed Street Map (OpenStreetMap)", show=True)`
2. Add `folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery", name="🛰️ High-Res Satellite View (Esri Imagery)", show=False)`
3. For each tiger in `behavior_predictions`, add `folium.plugins.HeatMap` in toggleable `folium.FeatureGroup(name=f"🔮 Predictive Heatmap: {tiger_id}", show=False)`.
4. Add target bullseye markers for predicted next camera stations.

---

### Step 4: Update `src/pipeline.py`
1. Import `TigerMovementPredictor`:
   ```python
   from .behavior.movement_predictor import TigerMovementPredictor
   ```
2. Initialize in `__init__`:
   ```python
   self.movement_predictor = TigerMovementPredictor()
   ```
3. In `process_sd_card_folder()` Phase 3:
   ```python
   behavior_predictions = {}
   for tid, slist in tiger_sightings.items():
       behavior_predictions[tid] = self.movement_predictor.predict_tiger_movement(tid, slist)
   ```
4. Pass `behavior_predictions` into `self.map_generator.generate_interactive_reserve_map(...)`.

---

### Step 5: Update `ui/app.py`
Add the behavioral predictions endpoint:
```python
@app.get("/api/behavior_predictions")
async def get_behavior_predictions():
    """Returns predictive movement analytics for all resident tigers."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tiger_id, s.station_id, s.timestamp, st.latitude, st.longitude, st.zone, st.range_name
        FROM sightings s
        JOIN stations st ON s.station_id = st.station_id
        WHERE s.tiger_id IS NOT NULL AND s.tiger_id != 'UNMATCHED';
    """)
    rows = cur.fetchall()
    conn.close()

    tiger_sightings = {}
    for r in rows:
        tiger_sightings.setdefault(r["tiger_id"], []).append(dict(r))

    predictions = {}
    for tid, slist in tiger_sightings.items():
        predictions[tid] = pipeline.movement_predictor.predict_tiger_movement(tid, slist)

    return predictions
```

---

### Step 6: Update Frontend (`index.html`, `style.css`, `app.js`)
1. **`index.html`**:
   - Add `<li class="nav-item" data-tab="predictive-tab"><span>🔮</span> Predictive Heatmaps</li>` in the sidebar.
   - Add `<div id="predictive-tab" class="tab-pane">` containing filter buttons, card container `#predictive-cards-container`, and the map iframe `#predictive-map-iframe`.
2. **`style.css`**:
   - Add `.predictive-grid`, `.pred-card`, `.pred-chip`, `.map-frame-wrapper`.
3. **`app.js`**:
   - Add `loadBehaviorPredictions()`, `renderPredictiveCards(predictions, filterType)`, and `filterPredictiveCards()`.

---

## 🧪 5. Testing & Verification

Run the test suite to verify 100% test pass rate:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
Expected output:
```text
Ran 14 tests in ~5s
OK
```

---

## 🚀 6. Running the System

Start the FastAPI application:
```bash
python ui/app.py
```
Open **`http://127.0.0.1:8000`** in the browser.

### How to Demo to Evaluators:
1. Go to **🔮 Predictive Heatmaps** in the sidebar.
2. View the individual tiger cards showing **Markov Station Transitions** (with percentage odds) and **Directional Trajectory** (with compass headings & village warning alerts).
3. Switch to the map view, open the **Layer Control (top-right)**, switch to **🛰️ High-Res Satellite View**, and toggle any tiger's **🔮 Predictive Heatmap** to reveal the time-decayed KDE hotspot gradient!
