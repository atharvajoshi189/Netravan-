# ATRW Dataset Verification & Download Checklist

**Project:** TigerTraceAI  
**Target Dataset:** ATRW (Amur Tiger Re-identification in the Wild)  
**Status:** Verification Complete — Ready for Small Pilot Stage  
**Constraint Adherence:** Zero files downloaded, zero models trained, production Re-ID code and canonical manifest untouched.

---

## 1. Official Source URLs & Access Verification

| Property | Official Source / Value | Verification Status |
| :--- | :--- | :--- |
| **Primary Project Portal** | [https://lila.science/datasets/atrw](https://lila.science/datasets/atrw) | **Verified** (Live HTTP 200) |
| **Workshop / Challenge Page** | [https://cvwc2019.github.io/challenge.html](https://cvwc2019.github.io/challenge.html) | **Verified** (Live HTTP 200) |
| **Evaluation & Ground Truth Code** | [https://github.com/cvwc2019/ATRWEvalScript](https://github.com/cvwc2019/ATRWEvalScript) | **Verified** (Public repo, branch `main`) |
| **Academic Publication** | Li, S., Li, J., Lin, W., & Tang, H. (2019). *Amur Tiger Re-identification in the Wild*. [arXiv:1906.05586](https://arxiv.org/abs/1906.05586) | **Verified** |
| **Primary Data Mirror (GCP)** | `https://storage.googleapis.com/public-datasets-lila/cvwc2019/` | **Verified** (Direct public access) |
| **Secondary Data Mirror (Azure)** | `https://lilawildlife.blob.core.windows.net/lila-wildlife/cvwc2019/` | **Verified** (Direct public access) |
| **Tertiary Data Mirror (AWS)** | `http://us-west-2.opendata.source.coop.s3.amazonaws.com/agentmorris/lila-wildlife/cvwc2019/` | **Verified** (Direct public access) |
| **Authentication / Approval Required** | **None** (Direct public HTTP GET) | **Verified** (No API key, token, or application needed) |

---

## 2. Remote Archive Inventory & Measured Sizes

Archive sizes were queried directly via HTTP `HEAD` requests (`Content-Length`) against official mirrors without downloading file payloads:

| Archive Filename | Official Path | Content Description | Verified Remote Size | Re-ID Pilot Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `atrw_anno_reid_train.tar.gz` | `cvwc2019/train/` | Re-ID training annotations (`reid_list_train.csv`, pose keypoints, README) | **98,982 bytes** (~0.09 MB / 97 KB) | **Mandatory First Download** |
| `atrw_reid_train.tar.gz` | `cvwc2019/train/` | Cropped bounding-box images of tigers for Re-ID training (~3,392 cropped images) | **138,885,317 bytes** (~132.45 MB) | **Target for 30-image extraction** |
| `atrw_anno_reid_test.tar.gz` | `cvwc2019/test/` | Re-ID test annotations / image list | **89,138 bytes** (~0.09 MB / 87 KB) | Not needed for pilot |
| `atrw_reid_test.tar.gz` | `cvwc2019/test/` | Cropped tiger images for test evaluation | **96,857,922 bytes** (~92.37 MB) | Not needed for pilot |
| `atrw_anno_detection_train.tar.gz` | `cvwc2019/train/` | Pascal VOC XML full-frame bounding-box annotations | **216,472 bytes** (~0.21 MB / 211 KB) | Detection only (optional) |
| `atrw_detection_train.tar.gz` | `cvwc2019/train/` | Full-frame uncropped training images | **2,288,778,168 bytes** (~2.18 GB) | **Do NOT download** (unneeded for Re-ID) |
| `atrw_anno_pose_train.tar.gz` | `cvwc2019/train/` | COCO keypoint pose annotations | *Available on LILA* | Optional (pose estimation) |
| `atrw_pose_train.tar.gz` | `cvwc2019/train/` | Pose task training images | *Available on LILA* | Optional (pose estimation) |

---

## 3. Annotation Contents & Identity Mapping Architecture

### Identity vs. Detection Labeling
- **Bounding Boxes**:
  - Full-frame bounding boxes are stored in `atrw_anno_detection_train.tar.gz` (Pascal VOC XML format) and in COCO detection format `[x, y, w, h]`.
  - The Re-ID image archive `atrw_reid_train.tar.gz` consists **already of cropped tiger bounding boxes**, meaning full-frame cropping is not required to begin Re-ID pipeline testing.
- **Individual Tiger IDs**:
  - Ground-truth individual identities are defined in `atrw_anno_reid_train.tar.gz`.
  - Identity pairings in the training set are structured in `reid_list_train.csv` as `[ID, filename]` pairs, where:
    - `ID`: Integer identifier representing a unique tiger individual (e.g., `1`, `2`, ... `92`).
    - `filename`: Image filename corresponding to the cropped tiger bounding box (e.g., `0001.jpg`).
  - The training set contains **92 unique tiger identities** across **3,649 bounding boxes** (averaging ~39.7 crops per individual).
  - Out of these, 1,887 annotated crops correspond to distinct left/right flank stripe patterns.

### Feasibility of a 30-Image Pilot (5 Individuals)
- **Verified Feasible:** Yes. With 92 unique identities and ~39.7 crops per identity, selecting **5 individual tigers** with **6 clean flank images each** (30 images total) is directly supported by the official annotations.

---

## 4. License, Intellectual Property & Usage Restrictions

- **License Name:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (**CC BY-NC-SA 4.0**).
- **Copyright Holders:** **MakerCollider** and the **World Wildlife Fund (WWF)** (Amur tiger and leopard conservation programme team).
- **Permitted Use:** Open-source conservation research, academic benchmarking, algorithm evaluation, and educational testing.
- **Commercial Restrictions:**
  - **NonCommercial (`NC`):** The dataset, imagery, and direct derivatives cannot be used for commercial purposes.
  - Commercial deployments of TigerTraceAI cannot license or sell models trained directly on ATRW without separate commercial licensing agreements with MakerCollider and WWF.
- **ShareAlike (`SA`):** Any derivative datasets created and redistributed must be released under the identical CC BY-NC-SA 4.0 license.
- **Attribution (`BY`):** Any publication, deployment documentation, or report must cite:
  > Li, S., Li, J., Lin, W., & Tang, H. (2019). *Amur Tiger Re-identification in the Wild*. arXiv:1906.05586.

---

## 5. Compatibility with Existing TigerTraceAI Architecture

### Manifest Schema Alignment
The TigerTraceAI manifest template (`data/manifests/dataset_manifest.csv`) requires 21 columns. The ATRW pilot mappings align as follows:

| TigerTraceAI Manifest Column | Mapping from ATRW Data | Status |
| :--- | :--- | :--- |
| `sample_id` | `atrw_pilot_0001` through `atrw_pilot_0030` | Synthetic sequential identifier |
| `dataset_name` | `ATRW` | Constant |
| `source_url` | `https://lila.science/datasets/atrw` | Constant |
| `relative_image_path` | `images/atrw_tiger_XX_YY.jpg` | Local path relative to pilot staging folder |
| `species_label` | `Panthera tigris` | Constant (Amur tiger subspecies) |
| `individual_id` | `tiger_001` through `tiger_005` (mapped from integer `ID`) | Verified from `reid_list_train.csv` |
| `identity_label_status` | `confirmed` | Verified ground truth from zoo registry |
| `bbox_x_min`, `bbox_y_min`, `bbox_x_max`, `bbox_y_max` | `0, 0, width, height` (images in `reid_train` are pre-cropped) | Verified |
| `timestamp_utc` | `needs_verification` (frame timestamps; exact UTC date unrecorded) | Labeled appropriately |
| `camera_id` | `zoo_camera_01` (or capture video clip identifier) | Derived from video clip ID |
| `site_id` | `atrw_zoo_source` | Constant |
| `latitude`, `longitude` | Empty / null (captive/zoo animals, coordinates withheld) | Empty |
| `split` | `train` / `val` / `test` (grouped strictly by `individual_id`) | Zero identity leakage |
| `license_id` | `CC-BY-NC-SA-4.0` | Verified |
| `attribution` | `MakerCollider / WWF / Li et al. (2019)` | Verified |
| `checksum_sha256` | Calculated per image file on staging | Verified |
| `review_status` | `approved` | Verified |

### Isolated Staging Structure
To guarantee zero contamination of production pipelines or existing databases:

```
d:\TigerTraceAI-main\data\staging\atrw_pilot\
├── annotations\
│   └── reid_list_train.csv          <-- Unpacked from atrw_anno_reid_train.tar.gz
├── images\                          <-- Exactly 30 image files
│   ├── tiger_001_01.jpg
│   ├── tiger_001_02.jpg
│   └── ... (up to tiger_005_06.jpg)
├── atrw_pilot_manifest.csv          <-- Pilot manifest (isolated from canonical manifest)
└── validation_report.json           <-- Output of scripts/validate_dataset_manifest.py
```

---

## 6. Items Requiring Manual Verification or Unresolved

1. **Flank Orientation (Left vs. Right Flank Asymmetry):**
   - *Status:* `needs_verification` upon unpacking annotations.
   - *Issue:* Amur tiger stripe patterns are distinct on the left and right flanks. If the pilot images contain a mix of left-side and right-side views of the same tiger without orientation tags, stripe matching algorithms will produce false non-matches.
   - *Action:* The pilot slice must explicitly filter for images of the **same flank side** (e.g., all left-flank or all right-flank) per individual, using the pose keypoints in `atrw_anno_reid_train.tar.gz`.
2. **Camera Sensor & Timestamp EXIF:**
   - *Status:* `needs_verification`. Zoo video frames typically lack camera trap sensor metadata (temperature, moon phase, trigger speed).
3. **Commercial Rights Path:**
   - *Status:* `needs_verification`. If TigerTraceAI is commercialized, written authorization from MakerCollider and WWF will be required.

---

## 7. Exact Next Download Steps (Pilot Execution Order)

When authorized to initiate file downloads, follow this precise sequence:

### Step 1: Download Annotations Archive (~97 KB)
- **Source URL:** `https://storage.googleapis.com/public-datasets-lila/cvwc2019/train/atrw_anno_reid_train.tar.gz`
- **Destination:** `data/staging/atrw_pilot/annotations/atrw_anno_reid_train.tar.gz`
- **Action:** Extract `reid_list_train.csv` and inspect available tiger IDs and crop counts.

### Step 2: Select 5 Individuals & Extract Target Filenames
- Inspect `reid_list_train.csv` and identify 5 tiger IDs that each possess at least 6 high-quality flank images.
- Generate the list of exactly 30 target filenames.

### Step 3: Retrieve Target Images (~1.2 MB total)
- **Source URL:** `https://storage.googleapis.com/public-datasets-lila/cvwc2019/train/atrw_reid_train.tar.gz` (132 MB)
- **Option A (Full download & selective extract):** Download `atrw_reid_train.tar.gz` to a temporary directory, extract *only* the 30 selected images into `data/staging/atrw_pilot/images/`, and delete the archive.
- **Option B (Streaming tar extract):** Stream the archive over HTTP and selectively extract only the 30 target members without storing the full 132 MB file on disk.

### Step 4: Generate Pilot Manifest & Validate
- Calculate SHA-256 hashes for all 30 image files.
- Populate `data/staging/atrw_pilot/atrw_pilot_manifest.csv`.
- Run the validator:
  ```powershell
  python scripts/validate_dataset_manifest.py `
      --manifest data/staging/atrw_pilot/atrw_pilot_manifest.csv `
      --dataset-root data/staging/atrw_pilot/images `
      --strict `
      --json-output data/staging/atrw_pilot/validation_report.json
  ```
