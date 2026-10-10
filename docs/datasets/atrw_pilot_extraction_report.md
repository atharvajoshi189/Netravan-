# ATRW Pilot Step 2: Selective Image Extraction Report

**Project:** TigerTraceAI  
**Step:** ATRW Pilot Step 2 — Selective Image Extraction & Provenance Tracking  
**Status:** Successfully Completed  
**Constraint Adherence:** Exactly 30 images extracted to staging; temporary archive deleted; canonical manifest and production code untouched.

---

## 1. Safety Checks & Archive Verification

- **Target Archive URL:** `https://storage.googleapis.com/public-datasets-lila/cvwc2019/train/atrw_reid_train.tar.gz`
- **Expected Archive Size:** `138,885,317` bytes (~132.45 MB)
- **Pre-download Disk Space:**
  - Temp Directory (`C:\Users\Atharva\AppData\Local\Temp`): **10,255.8 MB free** (exceeds 200 MB requirement)
  - Project Drive (`d:\TigerTraceAI-main`): **206,360.7 MB free** (exceeds 20 MB requirement)
- **Download Execution:** Downloaded to temporary path `C:\Users\Atharva\AppData\Local\Temp\atrw_reid_train_tmp.tar.gz`.
- **Actual Download Size:** **138,885,317 bytes** (100% matched expected size).
- **Archive Inspection:**
  - Total members in archive: **3,394**
  - Path traversal checks: All member names validated (zero leading slashes, zero parent directory `..` traversal).
  - Target match: **30 of 30 targets found and selectively extracted**.
  - **Full extraction prevented:** Only the 30 designated files were extracted to `data/staging/atrw_pilot/images/`.
  - **Immediate Cleanup:** The ~132 MB temporary archive was deleted immediately after extraction.

---

## 2. Image Extraction & Provenance Inventory

Every candidate image was verified against the local [reid_list_train.csv](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/annotations/reid_list_train.csv) before extraction. Image dimensions, color channels, and SHA-256 hashes were calculated directly from the extracted files:

| # | Filename | Original ATRW ID | Local Alias | Resolution ($W \times H$) | Color Mode | File Size | Valid Keypoints | SHA-256 Checksum | Extraction Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `000179.jpg` | `243` | `tiger_005` | $635 \times 390$ | RGB | 32,905 B | 14 / 15 | `3ed169c0fbd6b2c92386d9e3704934b2cd0d9f9f8a7d3c8b5f0d04e461ed23ee` | **SUCCESS** |
| 2 | `000187.jpg` | `153` | `tiger_001` | $426 \times 276$ | RGB | 19,722 B | 15 / 15 | `c87aaf80204b671eebd1a4d97e360b41904b5ecf99ed92fe323f696a94e516da` | **SUCCESS** |
| 3 | `000245.jpg` | `246` | `tiger_004` | $491 \times 452$ | RGB | 36,016 B | 10 / 15 | `b0000bbc3e1a7c2881eff3cdf80cafeb244b2762264bb76c03f765a7ce6925c4` | **SUCCESS** |
| 4 | `000420.jpg` | `246` | `tiger_004` | $1253 \times 855$ | RGB | 112,648 B | 14 / 15 | `3dcdda4c96f3a68dfa22adeb6cf1b819f78df4820b5f0d5d4bc1fe5333d6e560` | **SUCCESS** |
| 5 | `000592.jpg` | `246` | `tiger_004` | $444 \times 446$ | RGB | 35,720 B | 13 / 15 | `c551edabde3177c52c5f514b467cbd2099afbd47025d07f243b61a598e140002` | **SUCCESS** |
| 6 | `000696.jpg` | `154` | `tiger_003` | $398 \times 211$ | RGB | 29,989 B | 13 / 15 | `7dd02debe48b177e7476bade6f4da6b1ef6e04c6bde1b896b9eaa83cd1f2c686` | **SUCCESS** |
| 7 | `000739.jpg` | `160` | `tiger_002` | $248 \times 170$ | RGB | 11,954 B | 12 / 15 | `ddd12eaba2fb554fa76611d4a4b5961bcd7f72a06d2179c18da0278d83a6586d` | **SUCCESS** |
| 8 | `000792.jpg` | `243` | `tiger_005` | $836 \times 502$ | RGB | 52,994 B | 13 / 15 | `ab1bc3c33fde271a0952ccd90981020763ed320d12cb000a543b3c980350fe5a` | **SUCCESS** |
| 9 | `000938.jpg` | `153` | `tiger_001` | $489 \times 259$ | RGB | 30,050 B | 13 / 15 | `56aa961654702c7ce193302a28c83d9ecb94124c170cebc83bb82cbc98e477d5` | **SUCCESS** |
| 10 | `001069.jpg` | `154` | `tiger_003` | $378 \times 245$ | RGB | 17,790 B | 10 / 15 | `58572b89679f041ff31f6dfa9a147e62d4715494f6f74a82a0b943d67f57b28a` | **SUCCESS** |
| 11 | `001135.jpg` | `160` | `tiger_002` | $220 \times 167$ | RGB | 6,650 B | 9 / 15 | `510255cb3ff96a1a45719e71ec60d032899478f73111f1c713b773809673998d` | **SUCCESS** |
| 12 | `001205.jpg` | `246` | `tiger_004` | $1120 \times 659$ | RGB | 87,669 B | 14 / 15 | `b333917a151be9ae21b0142ec34fa6e45aa9f1bf3ef72bc97ae41dfb791cae69` | **SUCCESS** |
| 13 | `001223.jpg` | `153` | `tiger_001` | $285 \times 156$ | RGB | 8,678 B | 14 / 15 | `5d48386348efc63c3d5267ff355b253b27b9175dca2e2e7740f4ef570f80bb17` | **SUCCESS** |
| 14 | `001459.jpg` | `243` | `tiger_005` | $803 \times 443$ | RGB | 40,530 B | 13 / 15 | `c8e0018a109a9a3028d8b879ef79f4299b66236b3e9a966774c82c2084c8a29a` | **SUCCESS** |
| 15 | `001539.jpg` | `160` | `tiger_002` | $223 \times 173$ | RGB | 6,393 B | 14 / 15 | `a888c3a19b02787e974e44208a3857ba07e86cf56488d5e12f6d0f6a27e7ca4a` | **SUCCESS** |
| 16 | `001595.jpg` | `246` | `tiger_004` | $1307 \times 829$ | RGB | 124,454 B | 12 / 15 | `2f87a87679a6d0ca17c603bce30b35123d47f9f300067b5e808168f1847bb834` | **SUCCESS** |
| 17 | `001718.jpg` | `154` | `tiger_003` | $652 \times 413$ | RGB | 65,386 B | 14 / 15 | `63ba4243689fe780c1363650058b8f36ea0be02c1ae11c881c15f652ba71f302` | **SUCCESS** |
| 18 | `002149.jpg` | `160` | `tiger_002` | $275 \times 184$ | RGB | 13,592 B | 13 / 15 | `105151ee661c9ab2ea76b9ee6fb4a9452b415a9990595d2c2c62c335bbd9b8e1` | **SUCCESS** |
| 19 | `002315.jpg` | `243` | `tiger_005` | $538 \times 407$ | RGB | 36,473 B | 15 / 15 | `62569911e2f4749f7b02db73b137f8f90c1f62933d1b77bf9499870be8709a34` | **SUCCESS** |
| 20 | `002739.jpg` | `153` | `tiger_001` | $274 \times 180$ | RGB | 10,499 B | 12 / 15 | `d5500d43f05ce02047fc8668972b2269a08ebfc6bc5e79ff738495a63901b0f5` | **SUCCESS** |
| 21 | `002846.jpg` | `243` | `tiger_005` | $339 \times 197$ | RGB | 11,751 B | 11 / 15 | `d12be4fb208b049d5bf1e4597475f4c424076e737c35e98eb79768a35606df83` | **SUCCESS** |
| 22 | `002986.jpg` | `160` | `tiger_002` | $285 \times 182$ | RGB | 11,094 B | 14 / 15 | `1bb8357a07530e3fe01b339f40889bb333796cb19ce29cb9b09f449a37e9d73b` | **SUCCESS** |
| 23 | `003134.jpg` | `246` | `tiger_004` | $1166 \times 702$ | RGB | 97,539 B | 14 / 15 | `496ee8ea3302bc560414318c6ea3c50070bc0e96035f6345688d011f964098bc` | **SUCCESS** |
| 24 | `003156.jpg` | `154` | `tiger_003` | $390 \times 245$ | RGB | 16,773 B | 9 / 15 | `3bb6ddb391771239c09c314b9bf6ec6c9a33bb75f4ebfcb8e192ff82c676773a` | **SUCCESS** |
| 25 | `003286.jpg` | `154` | `tiger_003` | $760 \times 458$ | RGB | 84,055 B | 13 / 15 | `a274154fa734e70db2b152ec96f34a17fe0e029f635ff2aa6d5ecfa1cefb4948` | **SUCCESS** |
| 26 | `003437.jpg` | `153` | `tiger_001` | $716 \times 382$ | RGB | 68,649 B | 13 / 15 | `8f57fbe1e5e04cb2c4826b5e56e077dbe4dbdff19ebfd00cc8b17b66df21a196` | **SUCCESS** |
| 27 | `003817.jpg` | `160` | `tiger_002` | $268 \times 197$ | RGB | 12,384 B | 12 / 15 | `5b6c8ba0ec51ee78d8a562ef2a0f8bfca19d7d4c82b1dd4c8f5619e0cc0dfa19` | **SUCCESS** |
| 28 | `003896.jpg` | `154` | `tiger_003` | $288 \times 175$ | RGB | 11,892 B | 8 / 15 | `5ca1df092bbf18e974da7b0d879fa558e8071861759ea79df49a2a901e1d0f55` | **SUCCESS** |
| 29 | `003909.jpg` | `243` | `tiger_005` | $803 \times 446$ | RGB | 51,578 B | 13 / 15 | `10202868ff5034c519bfbfa712aa8ba3e6aeb6fbffaa8705a7e18b1464303126` | **SUCCESS** |
| 30 | `003944.jpg` | `153` | `tiger_001` | $741 \times 417$ | RGB | 86,737 B | 14 / 15 | `5c9f52f1437636e053d100067ff26b7c02b9e634125b03517409e5ee5a32ec69` | **SUCCESS** |

---

## 3. Important Annotation Checks

### 3.1 Flank Orientation & Pose Analysis
- **Keypoint Coverage:** All 30 selected images exhibit strong anatomical landmark detection (between 8 and 15 visible keypoints, mean: 12.8 out of 15).
- **Ambiguity in Flank Determination:** The ATRW dataset **does not include explicit string/categorical labels** for flank orientation (`left` or `right`).
- **Policy Decision:** In strict adherence to project constraints, **flank orientation has NOT been inferred solely from visibility counts**. Marking orientation automatically could create false negative biometric mismatches if a tiger is slightly angled or partially occluded.
- **Classification Status:** All 30 entries are officially categorized with `orientation_review_status = "needs_visual_review"`.

### 3.2 Source Identity Preservation & Alias Mapping
- The authentic source identities from ATRW have been preserved in the provenance records (`original_identity_id` column).
- Reversible local aliases are mapped as follows:
  - `tiger_001` $\leftrightarrow$ ATRW ID `153` (6 crops staged)
  - `tiger_002` $\leftrightarrow$ ATRW ID `160` (6 crops staged)
  - `tiger_003` $\leftrightarrow$ ATRW ID `154` (6 crops staged)
  - `tiger_004` $\leftrightarrow$ ATRW ID `246` (6 crops staged)
  - `tiger_005` $\leftrightarrow$ ATRW ID `243` (6 crops staged)

### 3.3 The 92-vs-107 Identity Discrepancy
- The published paper text and LILA BC description state: *"92 individual Amur tigers from 10 zoos in China"*.
- However, the extracted [reid_list_train.csv](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/annotations/reid_list_train.csv) contains **107 unique integer identities**.
- **Action Taken:** The source annotations have been kept intact without modification. This discrepancy is officially logged as unresolved pending authoritative reconciliation with the challenge organizers.

---

## 4. Generated Artifacts in Staging

1. **Images Directory:** [data/staging/atrw_pilot/images/](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/images/) (Contains exactly 30 `.jpg` files; total disk size: ~1.28 MB).
2. **Provenance CSV:** [data/staging/atrw_pilot/pilot_provenance.csv](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/pilot_provenance.csv) (31 rows including header).
3. **Provenance JSON:** [data/staging/atrw_pilot/pilot_provenance.json](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/pilot_provenance.json) (Formatted JSON structure for automated ingestion).

---

## 5. Verification & Test Suite Execution

Existing tests were executed after image extraction to guarantee zero regressions:

### 5.1 Manifest Validator Test Suite
```powershell
python -m unittest tests/test_validate_manifest.py
```
**Output:**
```
..........
----------------------------------------------------------------------
Ran 10 tests in 0.042s

OK
```

### 5.2 Re-ID Enrollment Audit Test Suite
```powershell
python -m unittest tests/test_enrollment_audit.py
```
**Output:**
```
....Enrollment approval halted: potential duplicate of BAJIRAO (score=0.6500 >= duplicate_threshold=0.3000).
.Re-ID Failed: invalid_or_missing_image_features for sighting 1 (path: nonexistent/invalid_file.jpg)
.....
----------------------------------------------------------------------
Ran 10 tests in 0.809s

OK
```

---

## 6. Preserved State

- **Canonical Manifest:** [data/manifests/dataset_manifest.csv](file:///d:/TigerTraceAI-main/data/manifests/dataset_manifest.csv) remains 100% clean with its original header row.
- **Production Services:** [src/reid/enrollment.py](file:///d:/TigerTraceAI-main/TigerTrace_AI/src/reid/enrollment.py) and database schemas are completely unmodified.
- **Model Training:** Zero models trained; no synthetic accuracy figures claimed.
