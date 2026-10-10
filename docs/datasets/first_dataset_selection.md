# TigerTraceAI — Dataset Source Verification & First Dataset Selection Report

**Document Version:** 1.0.0  
**Context:** Species-Agnostic Wildlife Re-ID & Camera Trap Intelligence (Pench Tiger Reserve & Multi-Species Landscape)  
**Status:** Evaluation & Recommendation Phase (Zero Data Downloaded; Zero Models Trained)  

---

## 1. Executive Summary & Objective

The objective of this assessment is to evaluate six candidate public datasets and recommend the single most suitable, lawfully accessible dataset for integrating the first small pilot into TigerTraceAI's individual-animal re-identification (Re-ID) pipeline.

### Core Strategic Findings
1. **Object Detection vs. Individual Re-ID Distinction:** Large camera-trap repositories such as **Caltech Camera Traps (CCT)** and **Wildlife Insights** provide immense value for *Phase 1 blank filtering and species-level detection*, but are **fundamentally unsuitable for Re-ID** because they lack ground-truth individual animal identities.
2. **Telemetry vs. Visual Re-ID Distinction:** **Movebank** provides valuable individual movement trajectories for *Phase 3 spatial occupancy*, but contains **zero visual imagery**, making it inapplicable to visual stripe/pelage matching.
3. **Primary Recommendation:** **ATRW (Amur Tiger Re-identification in the Wild)** is ranked **#1** as the first integration pilot. It is the only public benchmark providing verified individual tiger identities, bounding boxes, and flank images under open academic licensing (CC BY-NC-SA 4.0) with direct unauthenticated HTTP downloads.
4. **Secondary Multi-Species Follow-Up:** **LILA BC Hyena ID 2022** is ranked **#2** as the ideal second pilot to validate the species-agnostic biometric matching architecture beyond tigers.
5. **Tadoba / Pench Status:** We currently do not have a verified, openly licensed Tadoba-specific dataset. Ground-truth field testing for Pench remains anchored to the verified offline reference catalog in `dataset/verified_tiger_dataset`.

---

## 2. Technical Distinction: Object Detection vs. Individual-Animal Re-ID

A critical failure mode in wildlife computer vision projects is conflating **detection datasets** with **re-identification datasets**:

```
+--------------------------------------------------------------------------------------------------+
|                                OBJECT DETECTION & CLASSIFICATION                                 |
|                               (e.g., Caltech Camera Traps, Wildlife Insights)                     |
+--------------------------------------------------------------------------------------------------+
|  Input:   Camera trap frame                                                                       |
|  Output:  Bounding box [x_min, y_min, x_max, y_max] + Class: "tiger" (or "leopard", "blank")      |
|  Ground Truth: Species category ID only. Every tiger in the forest shares category = "tiger".   |
|  Limitation: Cannot train or evaluate whether Frame A and Frame B depict the same individual.     |
+--------------------------------------------------------------------------------------------------+

                                                VS.

+--------------------------------------------------------------------------------------------------+
|                                  INDIVIDUAL-ANIMAL RE-IDENTIFICATION                             |
|                                    (e.g., ATRW, Hyena ID 2022, Beluga ID 2022)                   |
+--------------------------------------------------------------------------------------------------+
|  Input:   Cropped flank / biometric coat patch of a detected animal                              |
|  Output:  Specific Identity Key: "BAJIRAO" vs "T15_COLLARWALI" (or "UNKNOWN_CANDIDATE_01")        |
|  Ground Truth: Unique animal ID persistent across multiple camera locations and timestamps.      |
|  Requirement: Disjoint individual splits (preventing identity leakage across train and test).     |
+--------------------------------------------------------------------------------------------------+
```

Integrating an object-detection dataset into a Re-ID pipeline produces empty or non-unique identity labels (`species=tiger, individual_id=UNKNOWN`), making it impossible to evaluate rank-1 accuracy, mAP, or HotSpotter SIFT stripe matching.

---

## 3. Comprehensive Verification of Candidate Sources

All facts below were verified against authoritative data from LILA BC (lila.science), Wildlife Insights, and Movebank documentation.

### Candidate 1: ATRW (Amur Tiger Re-identification in the Wild)
- **Official Source URL**: [https://lila.science/datasets/atrw](https://lila.science/datasets/atrw)
- **Individual-Animal Identity Labels**: **Verified Present.** Over 3,600 bounding boxes in the training set are explicitly annotated with individual tiger IDs covering 92 individual Amur tigers (*Panthera tigris altaica*).
- **Image & Annotation Accessibility**: **Verified Accessible.** Direct public download links hosted on Azure / LILA BC without login gates or paywalls.
- **Species & Modality**: Amur tiger (*Panthera tigris altaica*); high-resolution RGB video frame clips and still photographs.
- **License & Usage Restrictions**: **CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International). Underlying image rights credited to MakerCollider and World Wildlife Fund (WWF).
- **Registration / Approval Requirements**: None. Direct unauthenticated HTTP downloads.
- **Suitability for Individual Re-ID**: **Highest (Direct Tiger Match).** Directly tests flank stripe biometric extraction, RootSIFT keypoint minutiae, and deep embedding cosine matching without modifying any algorithms.
- **Limitations & Unverified Items**:
  - *Subspecies difference*: Amur tigers inhabit temperate zones with thicker coats, lighter coloration, and different stripe density compared to Central Indian Bengal tigers (*Panthera tigris tigris*).
  - *Capture environment*: Footage was captured in semi-wild zoological enclosures in China (Harbin, etc.) rather than dense tropical forest canopy.
  - *Test set Re-ID labels*: The public benchmark challenge holds out ground-truth IDs for the formal test set; however, the training set provides ~3,600 labeled instances across 92 individuals, which is more than sufficient for our pilot.

---

### Candidate 2: LILA BC Hyena ID 2022
- **Official Source URL**: [https://lila.science/datasets/hyena-id-2022](https://lila.science/datasets/hyena-id-2022)
- **Individual-Animal Identity Labels**: **Verified Present.** Contains 3,104 images of spotted hyenas (*Crocuta crocuta*) with individual identities for 256 unique animals.
- **Image & Annotation Accessibility**: **Verified Accessible.** Public direct downloads available via Google Cloud Platform (GCP), Amazon AWS, and Microsoft Azure public storage buckets (~3 GB uncompressed).
- **Species & Modality**: Spotted hyena (*Crocuta crocuta*); remote field camera traps and field survey RGB photographs from Botswana (Botswana Predator Conservation Trust / Wild Me).
- **License & Usage Restrictions**: **Community Data License Agreement – Permissive (CDLA-Permissive)**. Permits open academic and operational research use with standard attribution.
- **Registration / Approval Requirements**: None. Direct public download.
- **Suitability for Individual Re-ID**: **High (Multi-Species Spot Pattern).** Ideal for testing whether the Re-ID pipeline generalizes beyond tigers to non-stripe pelage patterns (coat spot clusters).
- **Limitations & Unverified Items**:
  - Pelage biometric is spot-based rather than stripe-based; SIFT stripe bifurcation minutiae may yield lower inlier counts than lateral tiger stripes unless spot centroids are extracted.
  - Full archive is ~3 GB; must be subsampled for a minimal lightweight pilot.

---

### Candidate 3: LILA BC Beluga ID 2022
- **Official Source URL**: [https://lila.science/datasets/beluga-id-2022](https://lila.science/datasets/beluga-id-2022)
- **Individual-Animal Identity Labels**: **Verified Present.** Contains 5,902 pre-cropped images covering 788 individual beluga whales (*Delphinapterus leucas*), collected in Cook Inlet, Alaska (Where's Whale-do? challenge).
- **Image & Annotation Accessibility**: **Verified Accessible.** Direct downloads via GCP/AWS/Azure (~563 MB train split, ~117 MB test split).
- **Species & Modality**: Beluga whale (*Delphinapterus leucas*); marine surface and boat-based wildlife photography.
- **License & Usage Restrictions**: **CDLA-Permissive**.
- **Registration / Approval Requirements**: None. Direct download.
- **Suitability for Individual Re-ID**: **Moderate for Aquatic Re-ID; Low Relevance for TigerTraceAI.**
- **Limitations & Unverified Items**:
  - Non-terrestrial marine modality; subject to water refraction, specular wave reflection, and surface spray.
  - Biometric features rely on dorsal ridge shape, pigmentation scars, and notch morphology rather than terrestrial fur patterns.

---

### Candidate 4: Caltech Camera Traps (CCT)
- **Official Source URL**: [https://lila.science/datasets/caltech-camera-traps](https://lila.science/datasets/caltech-camera-traps)
- **Individual-Animal Identity Labels**: **Verified ABSENT.** Images are labeled at the **species level only** (e.g., raccoon, opossum, coyote, bobcat, blank). Individual animal identities are not tracked.
- **Image & Annotation Accessibility**: Accessible (~130 GB) via LILA BC.
- **Species & Modality**: Motion-activated camera traps (PIR) in Southwestern United States.
- **License & Usage Restrictions**: **CDLA-Permissive**.
- **Registration / Approval Requirements**: None.
- **Suitability for Individual Re-ID**: **UNSUITABLE for Re-ID.** Excellent for Phase 1 blank frame triage validation, but cannot evaluate individual re-identification.

---

### Candidate 5: Wildlife Insights Public Downloads
- **Official Source URL**: [https://www.wildlifeinsights.org/get-started/download/public-downloads](https://www.wildlifeinsights.org/get-started/download/public-downloads)
- **Individual-Animal Identity Labels**: **Verified ABSENT in Public Downloads.** Public download packages provide species-level identifications and deployment metadata. Individual animal re-identification is not included in the public catalog tiers.
- **Image & Annotation Accessibility**: Requires account creation and authenticated platform sign-in. Coordinates for sensitive and endangered species are fuzzed (~11 km) to safeguard against poaching.
- **Species & Modality**: Global terrestrial camera traps (multi-continent).
- **License & Usage Restrictions**: Varies by contributing institution (CC0, CC-BY, CC-BY-NC) + Wildlife Insights Terms of Use.
- **Registration / Approval Requirements**: Account registration required.
- **Suitability for Individual Re-ID**: **UNSUITABLE for Re-ID.**

---

### Candidate 6: Movebank Animal Movement Studies
- **Official Source URL**: [https://www.movebank.org/cms/movebank-content/access-data](https://www.movebank.org/cms/movebank-content/access-data)
- **Individual-Animal Identity Labels**: **Verified Present** in tabular form (`individual-local-identifier`, collar tag ID).
- **Image & Annotation Accessibility**: **Non-Visual Modality.** Movebank stores GPS coordinates, Argos Doppler fixes, and acceleration sensor time-series; it does **not store camera trap imagery**.
- **Species & Modality**: Multi-species GPS telemetry and sensor logs (Tabular spatial data).
- **License & Usage Restrictions**: Study-specific (ranges from CC0 to restricted access requiring principal investigator authorization).
- **Registration / Approval Requirements**: Requires accepting study-specific Data Use Agreements.
- **Suitability for Individual Re-ID**: **UNSUITABLE for Visual Re-ID.** Highly valuable for Phase 3 Markov movement transition and KDE spatial modeling, but completely inapplicable to visual stripe matching.

---

## 4. Candidate Ranking Matrix for First Pilot Integration

| Rank | Candidate Dataset | Task Match (Re-ID) | Individual IDs | Modality Match | Access & Licensing | Pilot Size Feasibility | Multi-Species Value | Overall Score (out of 10) | Recommendation |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **ATRW (Amur Tiger)** | **Exact (Tiger Re-ID)** | **Yes (92 IDs)** | **RGB Stills/Frames** | **CC BY-NC-SA 4.0 (Direct)** | **High (Can subsample ~50 images)** | High (Baseline Feline) | **9.6 / 10** | **SELECTED FOR PILOT 1** |
| **2** | **LILA BC Hyena ID 2022** | **Strong (Spot Re-ID)** | **Yes (256 IDs)** | **Camera Trap Stills** | **CDLA-Permissive (Direct)** | **Moderate (~3 GB archive)** | **Highest (Carnivore multi-species)** | **8.7 / 10** | **RECOMMENDED FOR PILOT 2** |
| **3** | **LILA BC Beluga ID 2022** | Moderate (Aquatic ID) | Yes (788 IDs) | Marine Surface RGB | CDLA-Permissive (Direct) | High (~680 MB total) | Low (Marine outlier) | **5.5 / 10** | Deferred (Non-terrestrial) |
| **4** | **Caltech Camera Traps** | None (Detection Only) | **No** | Camera Trap Stills | CDLA-Permissive (Direct) | Low (~130 GB total) | Low (North America only) | **3.0 / 10** | Unsuitable for Re-ID |
| **5** | **Wildlife Insights Public** | None (Detection Only) | **No** | Camera Trap Stills | Account required / Fuzzed GPS | Low (Multi-gigabyte tiers) | Moderate (Global) | **2.2 / 10** | Unsuitable for Re-ID |
| **6** | **Movebank Telemetry** | None (Telemetry Only) | Yes (GPS collar tags) | **Non-visual Tabular** | Study-specific agreements | Variable by study | High (Movement only) | **1.8 / 10** | Inapplicable to Visual Re-ID |

---

## 5. Ranking Rationale

### Why ATRW is Ranked #1 for the First Pilot
1. **Target Species Alignment**: TigerTraceAI's core biometric algorithms—HotSpotter RootSIFT flank minutiae extraction and CLAHE contrast equalization—were designed specifically for feline flank stripe bifurcations. ATRW provides ground-truth individual tiger stripe patterns that directly validate our feature extractors without requiring domain transfer.
2. **Immediate Lawful & Technical Accessibility**: The dataset is hosted on LILA BC with unauthenticated, direct HTTP/Azure storage links under an open non-commercial academic license (CC BY-NC-SA 4.0).
3. **Subsampling Flexibility**: Because training annotations are provided as a simple CSV list of `[ID, filename]` pairs, we can construct an ultra-compact pilot slice of **5 to 10 tigers (~30 to 50 images)** without downloading or parsing gigabytes of irrelevant data.
4. **Zero Code Changes Required**: The ATRW annotations directly map into our standardized `dataset_manifest.csv` schema (`species_label="Panthera tigris"`, `individual_id=ATRW_ID`, `identity_label_status="confirmed_known"`).

### Why Hyena ID 2022 is Ranked #2 for Subsequent Expansion
1. **True Remote Field Camera Traps**: Sourced directly from Botswana remote field stations, capturing real-world jungle/savannah motion blur, dust, nocturnal infrared lighting, and natural camera angles.
2. **Species-Agnostic Validation**: Once tiger stripe matching is validated on ATRW, Hyena ID 2022 provides the exact test bed required to expand TigerTraceAI to non-stripe coat patterns (spots/rosettes, directly applicable to Indian leopards, *Panthera pardus*, and spotted hyaenas).

---

## 6. Small Pilot Integration Plan (Isolated, Safe & Subsampled)

To uphold the constraint against large bulk downloads and synthetic data, the recommended first integration pilot must be strictly staged as follows:

```
+----------------------------------------------------------------------------------------------------+
|                                    PILOT 1 INTEGRATION WORKFLOW                                     |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Step 1: Protocol Approval]                                                                       |
|      Formal sign-off on downloading a curated subsample (5 individual tigers, ~30 images total).   |
|                                                                                                    |
|  [Step 2: Subsampled Retrieval]                                                                    |
|      Target only 5 distinct tiger IDs from ATRW training set (e.g., IDs 1, 2, 3, 4, 5).            |
|      Store in isolated staging folder: data/staging/atrw_pilot/                                    |
|                                                                                                    |
|  [Step 3: Checksum & Provenance Audit]                                                             |
|      Compute SHA-256 for all pilot images. Confirm zero file corruption.                           |
|      Record license_id="CC-BY-NC-SA-4.0", attribution="MakerCollider / WWF / ATRW Benchmark".      |
|                                                                                                    |
|  [Step 4: Identity-Disjoint Split Partitioning]                                                    |
|      STRICT IDENTITY PARTITIONING TO PREVENT LEAKAGE:                                              |
|        - Tigers 1, 2, 3 -> 'train' split                                                           |
|        - Tiger 4        -> 'val' split                                                             |
|        - Tiger 5        -> 'test' split                                                            |
|      No individual ID may span multiple splits!                                                    |
|                                                                                                    |
|  [Step 5: Manifest Population & Validation]                                                        |
|      Write pilot entries to data/manifests/atrw_pilot_manifest.csv                                 |
|      Execute: python scripts/validate_dataset_manifest.py --manifest ... --dataset-root ...        |
|      Confirm: 0 errors, 0 split leakage warnings.                                                  |
|                                                                                                    |
|  [Step 6: Biometric Ingestion & Human Review Protocol]                                             |
|      Run Re-ID enrollment engine on pilot crops.                                                   |
|      Verify:                                                                                       |
|        - Identical images -> 'matched'                                                             |
|        - Ambiguous/occluded images -> 'review_required' staged in review_queue                     |
|        - Novel individuals -> 'new_identity_candidate' requiring explicit approval.               |
+----------------------------------------------------------------------------------------------------+
```

### Safety Principles Enforced:
- The canonical production manifest (`data/manifests/dataset_manifest.csv`) remains untouched (header-only).
- The pilot uses a dedicated test manifest (`data/manifests/atrw_pilot_manifest.csv`) to avoid polluting core records.
- No model weights are modified or retrained.

---

## 7. Next Manual Action Required Before Downloading Data

Before executing any network downloads, the following single manual confirmation is required:

> **Action Required:** Confirm approval to download the **curated ATRW pilot slice** (5 individual tiger identities, ~30 images, ~15 MB total payload) from LILA BC into `data/staging/atrw_pilot/` under CC BY-NC-SA 4.0 academic research terms.
