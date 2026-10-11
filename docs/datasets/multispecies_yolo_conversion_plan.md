# Multi-Species Dataset Conversion and Validation Plan

## 1. Overview and Objective
This document outlines the conversion, validation, and quality-assurance pipeline to transform candidate wildlife camera-trap datasets into normalized YOLO detection format (`images/`, `labels/`, and `data.yaml`).

The target detector covers **17 classes** defined in [species_taxonomy.json](file:///d:/TigerTraceAI-main/TigerTrace_AI/data/taxonomy/species_taxonomy.json), comprising the apex predator (`tiger`, class 0) and the **16 Tadoba landscape prey species** (classes 1–16).

---

## 2. Source Formats to Normalized YOLO Conversion

### 2.1 Supported Ingestion Formats
1. **COCO Camera Traps (LILA BC Standard):**
   - Source: `annotations.json` containing `images`, `annotations`, `categories`.
   - Conversion: BBoxes in COCO format `[x_min, y_min, width, height]` in pixels are converted to normalized YOLO format:
     $$\bar{x}_{center} = \frac{x_{min} + \frac{width}{2}}{W_{img}}, \quad \bar{y}_{center} = \frac{y_{min} + \frac{height}{2}}{H_{img}}$$
     $$\bar{w} = \frac{width}{W_{img}}, \quad \bar{h} = \frac{height}{H_{img}}$$
2. **CamTrapAsia / Zenodo CSV Format:**
   - Source: Tabular event records with species IDs, camera site IDs, and linked JPEG archives.
   - Note: Where bounding boxes are absent (sequence-level class annotations), imagery requires human annotation or automated pseudo-labelling via MegaDetector v5a prior to training inclusion.
3. **PASCAL VOC / XML Format:**
   - Source: `<bndbox>` with `<xmin>`, `<ymin>`, `<xmax>`, `<ymax>`.
   - Converted directly to normalized center coordinates.

---

## 3. Camera-Trap Specific Validation Rules

Wildlife camera traps introduce specific domain artifacts that standard computer vision pipelines often mishandle. The validator enforces:

### 3.1 Spatial and Coordinate Validation
- **Coordinate Clamping:** Ensure $0.0 \le \bar{x}, \bar{y}, \bar{w}, \bar{h} \le 1.0$.
- **Boundary Clamping:** Check $0.0 \le (\bar{x} - \bar{w}/2)$ and $(\bar{x} + \bar{w}/2) \le 1.0$. Boxes extending slightly past frame edges due to annotation rounding are clamped to valid ranges.
- **Minimum Box Area:** Boxes smaller than $16 \times 16$ pixels (or $\bar{w} \cdot \bar{h} < 0.0001$) are flagged or discarded to avoid camera trap dust, insect triggers, or sensor hot pixels.
- **Aspect Ratio Checks:** Flag extreme aspect ratios ($w/h > 15$ or $h/w > 15$) for human manual inspection.

### 3.2 Temporal and Site Leakage Prevention (Crucial)
Camera traps typically record bursts of 3–5 frames within 2 seconds when an animal passes the PIR sensor.
- **The Pitfall:** If frames from the same burst or sequence are randomly assigned across `train` and `val`, the model memorizes the exact animal pose and background foliage, resulting in artificially inflated validation metrics (~99% mAP) that collapses in real field deployments.
- **The Rule:** Splitting **MUST** be grouped by `site_id` or `location_id` (or minimally by `sequence_id`):
  - **Train Split (70%):** Cameras located in designated sector zones.
  - **Val Split (15%):** Separate cameras within the reserve landscape.
  - **Holdout Test Split (15%):** Completely unseen camera stations to measure generalizability across novel vegetation and lighting.

### 3.3 Blank and Negative Sample Ratio
- In wildlife camera-trap surveys, 70–90% of frames are blanks (triggered by wind, shadows, or moving vegetation).
- **Inclusion Policy:** Include a controlled 10–15% ratio of confirmed blank frames in the training dataset (`.txt` label file exists but is empty). This teaches the YOLO background branch not to trigger false detections on blowing leaves or waving grass.

---

## 4. Class Mapping Protocol

Annotations must strictly map source category strings to canonical IDs in `species_taxonomy.json`:

| Canonical ID | Canonical Name | Common Provider Labels |
|---|---|---|
| `0` | `tiger` | `Panthera tigris`, `tiger`, `Bengal tiger` |
| `1` | `sambar` | `Rusa unicolor`, `Cervus unicolor`, `sambar` |
| `2` | `wild_boar` | `Sus scrofa`, `wild boar`, `wild pig` |
| `3` | `chital` | `Axis axis`, `chital`, `spotted deer` |
| `4` | `cattle` | `Bos taurus`, `Bos indicus`, `cow`, `bull`, `cattle` |
| `5` | `muntjac` | `Muntiacus muntjak`, `barking deer`, `Indian muntjac` |
| `6` | `gaur` | `Bos gaurus`, `Indian bison`, `gaur` |
| `7` | `nilgai` | `Boselaphus tragocamelus`, `blue bull`, `nilgai` |
| `8` | `sloth_bear` | `Melursus ursinus`, `sloth bear` |
| `9` | `goat` | `Capra hircus`, `domestic goat`, `goat` |
| `10` | `indian_hare` | `Lepus nigricollis`, `black-naped hare`, `Indian hare` |
| `11` | `buffalo` | `Bubalus bubalis`, `water buffalo`, `domestic buffalo` |
| `12` | `grey_junglefowl` | `Gallus sonneratii`, `grey junglefowl` |
| `13` | `peafowl` | `Pavo cristatus`, `Indian peafowl`, `peacock` |
| `14` | `flying_squirrel` | `Petaurista philippensis`, `Indian giant flying squirrel` |
| `15` | `grey_langur` | `Semnopithecus entellus`, `Hanuman langur`, `grey langur` |
| `16` | `grey_mongoose` | `Herpestes edwardsii`, `Indian grey mongoose` |

*Unmapped species* (e.g., leopards, elephants, birds not in diet chart) are ignored or routed to an optional background/auxiliary evaluation set; they must never be silently folded into prey classes.

---

## 5. Output YOLO Structure

Once verified and approved, datasets will be materialized into standard Ultralytics YOLO directory layout:

```text
TigerTrace_AI/data/multispecies_dataset/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### `data.yaml` Specification
```yaml
path: TigerTrace_AI/data/multispecies_dataset
train: images/train
val: images/val
test: images/test

nc: 17
names:
  0: tiger
  1: sambar
  2: wild_boar
  3: chital
  4: cattle
  5: muntjac
  6: gaur
  7: nilgai
  8: sloth_bear
  9: goat
  10: indian_hare
  11: buffalo
  12: grey_junglefowl
  13: peafowl
  14: flying_squirrel
  15: grey_langur
  16: grey_mongoose
```

---

## 6. Safeguards and Integration Protection
- **Step 9A Preservation:** Camera-trap human detections (villagers, forest guards, poachers) must trigger automated face/body blurring before any training visualization or export.
- **Step 9B Preservation:** Bounding box expansion margins (15% padding) used in the Re-ID pipeline remain decoupled from detector training coordinates. Detector is trained on tight ground-truth boxes.
- **Step 13 / 14 Preservation:** High-confidence detection of `tiger` routes crops to individual Re-ID, where decisions remain gated by Human Review Queue and `review_required` safeguards.
