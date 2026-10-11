# Wildlife & Tadoba Prey Dataset Discovery Inventory

**Document Version:** 1.0.0  
**Target Landscape:** Central India (Tadoba-Andhari & Pench Tiger Reserves)  
**Taxonomy Scope:** 17 Classes (Tiger + 16 Prey Categories defined in `species_taxonomy.json`)

---

## 1. Executive Summary

This inventory evaluates public and institutional wildlife datasets to train a multi-species wildlife detector.

### Critical Takeaways
1. **No Single Silver Bullet:** No single public dataset provides bounding-box camera-trap annotations for all 16 Tadoba prey species. Central Indian endemic herbivores (`chital`, `nilgai`, `gaur`) are absent from North American/African-focused archives (like Snapshot Serengeti or Caltech Camera Traps).
2. **Optimal Real-World Strategy:**
   - **Backbone & General Wildlife Detection:** Pretrained on [MegaDetector v5a](https://github.com/agentmorris/MegaDetector) (YOLOv5/YOLOv8 architecture trained on millions of camera-trap bounding boxes across LILA BC).
   - **Central Indian Camera Traps:** Formal collaboration / model reuse with Wildlife Conservation Trust (WCT) Central India / Addax Data Science (1.1M images, 40 species in Pench/Tadoba).
   - **Public BBox Aggregation:** Combine WCS Camera Traps (LILA BC) + CamTrapAsia (Zenodo) + Kaggle Indian Wildlife subsets + CC-BY iNaturalist bounding boxes.

---

## 2. Candidate Datasets Inventory

### Dataset 1: Wildlife Conservation Trust (WCT) Central India / Addax Data Science
- **Source:** [Addax Data Science / WCT](https://addaxdatascience.com/sparrow/) & Zenodo Model Repository
- **License:** Pretrained models & Sparrow software open; raw image imagery restricted under MOU / Data Transfer Agreement (DTA) with Maharashtra & Madhya Pradesh Forest Departments.
- **Permitted Use:** Research and conservation monitoring with official institutional agreement.
- **Image Count:** **~1,100,000 camera-trap images** across 40 species in Pench, Tadoba, Melghat, and wildlife corridors.
- **Species Overlap with Taxonomy:**
  - `tiger` (Yes)
  - `sambar` (Yes)
  - `wild_boar` (Yes)
  - `chital` (Yes)
  - `cattle` (Yes)
  - `muntjac` (Yes)
  - `gaur` (Yes)
  - `nilgai` (Yes)
  - `sloth_bear` (Yes)
  - `indian_hare` (Yes)
  - `grey_langur` (Yes)
  - `peafowl` (Yes)
- **Bounding Boxes:** Yes (Used internally to train WCT's YOLO Central India model).
- **Individual Re-ID Labels:** Tigers have individual IDs; prey species do not.
- **Assessment:** The gold standard for Tadoba. However, raw imagery cannot be directly downloaded via public curl; weights or formal academic data sharing must be requested from WCT.

---

### Dataset 2: WCS Camera Traps (LILA BC)
- **Source:** [LILA BC - WCS Camera Traps](https://lila.science/datasets/wcs-camera-traps) / Azure Open Datasets
- **Download Method:** `azcopy` or HTTP archive download from LILA blob storage.
- **Archive Size:** ~1.4 million images (~1.3 TB raw full archive; subsets downloadable by site).
- **License:** Community Data License Agreement – Permissive (CDLA-Permissive-1.0) / CC-BY 4.0. Permitted for commercial and research use with attribution.
- **Bounding Boxes:** Yes. Over 170,000 bounding-box annotations formatted in COCO Camera Traps format.
- **Species Overlap with Taxonomy:**
  - `tiger` (Partial - Asian sites)
  - `wild_boar` (*Sus scrofa* - Strong)
  - `cattle` (*Bos taurus* - Strong)
  - `goat` (*Capra hircus* - Strong)
  - `muntjac` (*Muntiacus* spp. - Moderate)
  - `sambar` (*Rusa unicolor* - Moderate)
  - `buffalo` (*Bubalus* - Moderate)
- **Coverage Gaps:** Does not cover Indian endemic taxa: `chital` (Axis axis), `nilgai`, `gaur`, `sloth_bear`, `grey_junglefowl`.
- **Individual Re-ID Labels:** None.
- **Assessment:** Excellent public source for domestic prey (cattle, goat, buffalo) and wild boar/sambar, but must be complemented for Indian-specific deer and bovids.

---

### Dataset 3: CamTrapAsia (Zenodo / Ecology 2024)
- **Source:** [Zenodo DOI: 10.5281/zenodo.10787132](https://zenodo.org/records/10787132) & Publication in *Ecology* (2024).
- **Download Method:** Direct HTTPS download from Zenodo repository.
- **Archive Size:** ~12 GB (images + tabular event metadata).
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0). Permitted for open research.
- **Records:** 278,260 camera-trap detection events covering 371 Asian mammal species.
- **Species Overlap with Taxonomy:**
  - `tiger` (Yes)
  - `sambar` (Yes)
  - `muntjac` (Yes)
  - `gaur` (Yes)
  - `wild_boar` (Yes)
  - `grey_langur` (Yes)
- **Bounding Boxes:** No native tight bounding boxes in the main repository (contains sequence and image-level species presence labels).
- **Individual Re-ID Labels:** None.
- **Assessment:** Outstanding ground-truth species labels from tropical Asia; requires automated bounding-box generation using MegaDetector prior to training.

---

### Dataset 4: Amur Tiger Re-ID in the Wild (ATRW - LILA BC)
- **Source:** [LILA BC - ATRW](https://lila.science/datasets/atrw)
- **Download Method:** Direct HTTPS / Google Drive / LILA links (documented in `docs/datasets/atrw_download_checklist.md`).
- **Archive Size:** ~15 GB full dataset (~8,076 images).
- **License:** Academic non-commercial research use only (CVWC 2019 terms).
- **Species Overlap:** Single species (`tiger`, Class 0).
- **Bounding Boxes:** Yes (**9,493 tight tiger bounding boxes**).
- **Individual Re-ID Labels:** Yes (**357 individual identities**, 18,986 keypoints, flank views).
- **Assessment:** Approved for tiger detection and Re-ID research, already audited in Steps 10–14. Contains zero prey data.

---

### Dataset 5: iNaturalist Open Data (AWS Open Data / GBIF)
- **Source:** [AWS Open Data iNaturalist](https://registry.opendata.aws/inaturalist-open-data/) & GBIF API
- **Download Method:** AWS CLI (`aws s3 sync --no-sign-request`) or GBIF occurrence downloads.
- **Archive Size:** Modular / on-demand queries (can target 100–500 images per species).
- **License:** Filterable to CC0, CC-BY, and CC-BY-NC.
- **Species Overlap with Taxonomy:**
  - **100% taxonomic coverage:** Can query all 17 species including rare/endemic classes: `chital`, `nilgai`, `gaur`, `sloth_bear`, `grey_junglefowl`, `peafowl`, `flying_squirrel`, `grey_mongoose`.
- **Bounding Boxes:** Moderate — iNaturalist bounding-box projects exist on LILA; otherwise point coordinates / full images.
- **Limitation:** Handheld enthusiast daylight photos rather than infrared night camera traps.
- **Assessment:** Indispensable to close coverage gaps for Indian endemics and birds (`grey_junglefowl`, `peafowl`, `flying_squirrel`), but should be blended with real camera traps so the model learns nocturnal IR representations.

---

### Dataset 6: Kaggle Indian Wildlife Animal Detection Subsets
- **Source:** Kaggle (`indian-wildlife-dataset`, `wildlife-animal-detection`)
- **Download Method:** Kaggle API (`kaggle datasets download -d ...`)
- **Archive Size:** ~2 GB to 5 GB.
- **License:** CC0 / Open Database License.
- **Image Count:** ~3,000 images.
- **Species Overlap:** Covers Bengal Tiger, Chital (Spotted Deer), Sambar Deer, Wild Boar, Nilgai, Sloth Bear.
- **Bounding Boxes:** Yes (PASCAL VOC XML and YOLO annotations for ~1,500 images).
- **Assessment:** Useful bridge dataset for Indian ungulates and sloth bear bounding boxes.

---

## 3. Class Coverage Matrix (17 Classes)

| ID | Class Name | ATRW | WCS (LILA) | CamTrapAsia | iNaturalist | Kaggle India | Public Camera-Trap BBox Status |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| `0` | `tiger` | **YES** | Partial | Yes | Yes | Yes | **Full Public BBox Ready** |
| `1` | `sambar` | No | Partial | Yes | Yes | Yes | **Partial BBox Ready** |
| `2` | `wild_boar` | No | **YES** | Yes | Yes | Yes | **Full Public BBox Ready** |
| `3` | `chital` | No | No | No | Yes | **YES** | **GAP:** Needs Kaggle + iNat + MDv5 |
| `4` | `cattle` | No | **YES** | No | Yes | Yes | **Full Public BBox Ready** |
| `5` | `muntjac` | No | Partial | Yes | Yes | No | **Partial BBox Ready** |
| `6` | `gaur` | No | No | Yes | Yes | Partial | **GAP:** Needs CamTrapAsia pseudo-box |
| `7` | `nilgai` | No | No | No | Yes | **YES** | **GAP:** Needs Kaggle + iNat |
| `8` | `sloth_bear` | No | No | No | Yes | Partial | **GAP:** Needs Kaggle + iNat |
| `9` | `goat` | No | **YES** | No | Yes | Yes | **Full Public BBox Ready** |
| `10`| `indian_hare` | No | No | No | Yes | No | **GAP:** Severe camera-trap shortage |
| `11`| `buffalo` | No | **YES** | No | Yes | Yes | **Full Public BBox Ready** |
| `12`| `grey_junglefowl`| No | No | No | Yes | No | **GAP:** Severe camera-trap shortage |
| `13`| `peafowl` | No | No | No | Yes | Partial | **Partial:** iNat + Kaggle |
| `14`| `flying_squirrel`| No | No | No | Yes | No | **GAP:** Critical shortage (nocturnal arboreal) |
| `15`| `grey_langur` | No | No | Yes | Yes | Partial | **Partial:** CamTrapAsia + iNat |
| `16`| `grey_mongoose` | No | No | No | Yes | No | **GAP:** Small carnivore shortage |

---

## 4. Re-ID Feasibility Assessment

- **Tiger (Class 0):** Individual Re-ID is supported by stripe biometric patterns. 357 individuals available via ATRW; local Tadoba catalogue (e.g., BAJIRAO, T-108) configured in TigerTraceAI.
- **Prey Classes (Classes 1–16):**
  - **No individual biometric identification:** None of the public datasets provide individual animal identities for prey species.
  - **Biological feasibility:** Chital (spotted coats) have individual spot configurations theoretically usable for Re-ID, but no calibrated public dataset exists. Sambar, nilgai, wild boar, and gaur have uniform coats lacking invariant biometric stripe/spot patterns.
  - **Conclusion:** TigerTraceAI scope for prey classes remains **Species Detection & Counting**, while Individual Biometric Re-ID remains strictly reserved for `tiger`.
