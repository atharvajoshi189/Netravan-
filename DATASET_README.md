# Pench Tiger Reserve Image & Intelligence Dataset

Curated dataset designed for the Maharashtra Government Hackathon: **"Automated Camera Trap Triage and Individual Tiger Movement Intelligence System for Pench Tiger Reserve"**.

---

## 🐯 Labeled & Annotated Tiger Dataset (7 Classes)

The dataset is organized across **6 Identified Individual Tiger Groups + 1 General Group**:

| Class ID | Class Name | Prefix | Images / Annotations / Flank Crops | Description |
| :---: | :--- | :--- | :---: | :--- |
| **0** | **`T15_Collarwali`** | `T15_Collarwali_001..` | **10** | Queen of Pench / T-15 |
| **1** | **`T40_Patdev`** | `T40_Patdev_001..` | **7** | Resident tigress T-40 (Patdev) |
| **2** | **`T-74_L-Mark`** | `T74_LMark_001..` | **9** | Resident dominant male tiger T-74 / L-Mark |
| **3** | **`Bajirao`** | `Bajirao_001..` | **10** | Iconic dominant male tiger of Pench |
| **4** | **`Swastik`** | `Swastik_001..` | **7** | Iconic resident tiger with distinctive forehead marking |
| **5** | **`Karmajhiri_Core_Tigers`** | `Karmajhiri_Core_001..` | **16** | Resident core tigers captured in Karmajhiri / Turia zone |
| **6** | **`Pench_General_Tigers`** | `Pench_General_Tiger_001..` | **36** | Camera trap & reserve captures (un-enrolled reference catalogue) |
| **Total** | | | **95** | **100% Annotated & Flank-Cropped** |

---

## 📁 Dataset Directory Layout

```text
Pench_TIger_Images/
├── dataset/
│   ├── verified_tiger_dataset/       # Renamed images with local YOLO .txt bounding box files
│   │   ├── T15_Collarwali/           # (T15_Collarwali_001.jpg + .txt ...)
│   │   ├── T40_Patdev/               # (T40_Patdev_001.jpg + .txt ...)
│   │   ├── T-74_L-Mark/              # (T74_LMark_001.png + .txt ...)
│   │   ├── Bajirao/                  # (Bajirao_001.png + .txt ...)
│   │   ├── Swastik/                  # (Swastik_001.png + .txt ...)
│   │   ├── Karmajhiri_Core_Tigers/   # (Karmajhiri_Core_001.jpg + .txt ...)
│   │   ├── Pench_General_Tigers/     # (Pench_General_Tiger_001.jpg + .txt ...)
│   │   └── verified_tiger_manifest.json
│   │
│   ├── yolo_detection_dataset/       # Standard YOLO training format
│   │   ├── images/train/             # All 95 images
│   │   ├── labels/train/             # All 95 YOLO .txt label files (<class_id> <xc> <yc> <w> <h>)
│   │   └── data.yaml                 # YOLO data configuration with classes 0..6
│   │
│   ├── flank_stripe_crops/           # Extracted flank & body crops for Stripe Re-ID
│   │   ├── T15_Collarwali/           # Flank crops for Collarwali
│   │   ├── T40_Patdev/               # Flank crops for Patdev
│   │   ├── T-74_L-Mark/              # Flank crops for L-Mark
│   │   ├── Bajirao/                  # Flank crops for Bajirao
│   │   ├── Swastik/                  # Flank crops for Swastik
│   │   ├── Karmajhiri_Core_Tigers/   # Flank crops for Karmajhiri tigers
│   │   └── Pench_General_Tigers/     # Flank crops for general tigers
│   │
│   └── filtered_out_non_tigers/      # Isolated non-tiger images (maps, graphs, blanks, co-predators)
```

---

## 🛠️ Ready for Model Training
* **YOLO Object Detection**: Use [`dataset/yolo_detection_dataset/data.yaml`](file:///c:/Users/Lenovo/Desktop/Pench_TIger_Images/dataset/yolo_detection_dataset/data.yaml) for training YOLOv8/YOLOv11 to detect and classify individual Pench tigers.
* **Stripe Pattern Re-ID**: Use [`dataset/flank_stripe_crops/`](file:///c:/Users/Lenovo/Desktop/Pench_TIger_Images/dataset/flank_stripe_crops) with Triplet Loss / ResNet / HotSpotter feature extraction to match tigers across camera trap stations.
