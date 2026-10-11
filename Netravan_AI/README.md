# 🐅 TigerTrace_AI
### Automated Camera Trap Triage and Individual Tiger Intelligence System for Pench Tiger Reserve

Built for the Maharashtra Government National Hackathon.

---

## 🌟 Key Features

### **Phase 1: Camera Trap Triage & Privacy**
* **Blank Image Removal:** Automatically filters wind, rain, and moving vegetation frames using CPU-optimized object detection.
* **Safe Staged Quarantine:** Soft-deletes blanks with reversible restoration and calculates exact storage (MB/GB) and person-hours saved.
* **Human Privacy Blurring:** Detects humans/field staff and applies Gaussian blurring before storage.

### **Phase 2: Individual Stripe Re-ID & Database**
* **Flank Stripe Extraction:** Automatically crops the animal body with CLAHE contrast enhancement for infrared/shaded traps.
* **HotSpotter SIFT Stripe Matching:** Matches geometric stripe pattern minutiae (scale & rotation invariant) without requiring neural network training.
* **Decision Engine:** High-confidence auto-matching, ambiguous human-in-the-loop review queue with visual match lines, and auto-enrollment for new individuals (`PTR_T_XXX`).
* **Persistent SQLite Database:** Fully relational schema connecting individuals $\leftrightarrow$ camera stations $\leftrightarrow$ timestamps $\leftrightarrow$ GPS coordinates.

---

## 🚀 Quick Start

### 1. Seed Reference Catalogue & Data
```bash
python setup_and_seed_data.py
```

### 2. Run Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 3. Run Pipeline on a Raw SD Card Folder
```python
from src.pipeline import TigerTracePipeline

pipeline = TigerTracePipeline()
# Seed known tigers from reference catalogue
pipeline.seed_reference_catalogue("data/reference_catalogue")

# Process raw SD card drop
report = pipeline.process_sd_card_folder("data/raw_sd_cards/SD_CARD_PTR_STN_02")
print(report)
```

### Offline Map Note
The Pench occupancy map is configured to work without external tile providers. It renders reserve boundaries, stations, home ranges, and conflict overlays using a blank offline base so field laptops do not need internet access for the map layer.
