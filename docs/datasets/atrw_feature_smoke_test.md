# ATRW Pilot Step 5: Feature Extraction Smoke Test Report

**Project:** TigerTraceAI  
**Test Suite:** Step 5 — ATRW Feature Extraction Technical Smoke Test  
**Objective:** Verify that existing TigerTraceAI feature-extraction and similarity-matching components execute cleanly on the 13 approved ATRW crops without side-effects or regressions.  
**Constraint Adherence:** No models trained or fine-tuned; no animals enrolled; canonical manifest and production code untouched; zero accuracy benchmark claims made.

---

## 1. Component Inspection & Execution Environment

### 1.1 Inspected Components
- **`src/reid/flank_extractor.py` (`FlankExtractor`):**
  - Applies Luminance-channel CLAHE (Contrast Limited Adaptive Histogram Equalization, `clipLimit=3.0`, `tileGridSize=(8, 8)`) to enhance feline stripe bifurcation contrast.
  - Resizes crops to standardized target dimension $(384, 384, 3)$ using area interpolation.
- **`src/reid/stripe_matcher.py` (`StripeReIDMatcher`):**
  - **Minutiae Extractor:** OpenCV SIFT (`cv2.SIFT_create(nfeatures=1000)`), extracting 128-dimensional descriptor vectors at stripe edges and bifurcations.
  - **Deep Embedder:** PyTorch Torchvision `models.resnet50` with classification head replaced by `nn.Identity()`. Generates 2048-dimensional $L_2$-normalized feature vectors.
  - **Matcher:** In-memory FLANN matcher (Lowe's ratio test) + deep cosine similarity ensembled at $0.55 \times \text{SIFT} + 0.45 \times \text{Cosine}$. Zero database access, zero state modification.

### 1.2 Model Weights & Dependencies
- **PyTorch Version:** `2.10.0+cpu`
- **Torchvision Version:** `0.25.0+cpu`
- **Model Weights:** `ResNet50_Weights.DEFAULT` loaded directly from local PyTorch cache without network requests or external weight downloads.

---

## 2. Per-Image Feature Extraction Smoke Test Results

All 13 approved images from [atrw_pilot_manifest.csv](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/atrw_pilot_manifest.csv) were processed individually:

| # | Filename | Tiger Alias | ATRW ID | Original Dims ($W \times H$) | CLAHE Flank Crop | SIFT Keypoints | Deep Vector Shape | $L_2$ Norm | All Finite? | Runtime | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `000938.jpg` | `tiger_001` | 153 | $489 \times 259$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.260s | **PASS** |
| 2 | `002739.jpg` | `tiger_001` | 153 | $224 \times 173$ | $(384, 384, 3)$ | 604 | `(2048,)` float32 | 1.0000 | Yes | 0.054s | **PASS** |
| 3 | `003437.jpg` | `tiger_001` | 153 | $583 \times 428$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.095s | **PASS** |
| 4 | `003944.jpg` | `tiger_001` | 153 | $714 \times 440$ | $(384, 384, 3)$ | 1,001 | `(2048,)` float32 | 1.0000 | Yes | 0.103s | **PASS** |
| 5 | `000739.jpg` | `tiger_002` | 160 | $248 \times 170$ | $(384, 384, 3)$ | 548 | `(2048,)` float32 | 1.0000 | Yes | 0.049s | **PASS** |
| 6 | `002149.jpg` | `tiger_002` | 160 | $238 \times 203$ | $(384, 384, 3)$ | 746 | `(2048,)` float32 | 1.0000 | Yes | 0.053s | **PASS** |
| 7 | `000696.jpg` | `tiger_003` | 154 | $398 \times 211$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.059s | **PASS** |
| 8 | `001069.jpg` | `tiger_003` | 154 | $268 \times 167$ | $(384, 384, 3)$ | 926 | `(2048,)` float32 | 1.0000 | Yes | 0.057s | **PASS** |
| 9 | `001718.jpg` | `tiger_003` | 154 | $695 \times 407$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.097s | **PASS** |
| 10 | `003286.jpg` | `tiger_003` | 154 | $697 \times 469$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.106s | **PASS** |
| 11 | `000179.jpg` | `tiger_005` | 243 | $635 \times 390$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.089s | **PASS** |
| 12 | `000792.jpg` | `tiger_005` | 243 | $836 \times 502$ | $(384, 384, 3)$ | 1,001 | `(2048,)` float32 | 1.0000 | Yes | 0.125s | **PASS** |
| 13 | `002315.jpg` | `tiger_005` | 243 | $665 \times 433$ | $(384, 384, 3)$ | 1,000 | `(2048,)` float32 | 1.0000 | Yes | 0.100s | **PASS** |

### Summary Metrics:
- **Total Samples:** 13
- **Successful Extractions:** **13 / 13 (100%)**
- **Failures / Exceptions:** **0**
- **Degenerate or Zero Vectors:** **0**
- **All Values Finite:** **Yes (100%)**
- **Average Per-Image Extraction Latency:** ~88 ms (CPU)

---

## 3. Exploratory Pairwise Matching Diagnostics

> [!WARNING]
> **Exploratory Diagnostic Notice:**  
> The scores below represent exploratory sanity checks of the matcher's mathematical scoring pipeline on CPU. They **must not be interpreted as a statistically significant Rank-1 benchmark or scientific accuracy claim**, due to the small sample size (13 crops across 4 individuals) and temporal correlations in video bursts.

Pairwise comparisons were executed purely in-memory using `StripeReIDMatcher.compare_flanks`:

| Pair Category | Pair Count | Mean SIFT Score | Mean Cosine Score | Mean Ensembled Combined Score | Combined Score Range |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Same-Identity Pairs** | 16 | **0.3458** | **0.9053** | **0.5976** | $[0.4078, 0.9940]$ |
| **Different-Identity Pairs** | 62 | **0.1269** | **0.8706** | **0.4616** | $[0.3496, 0.8039]$ |

### Diagnostic Observations:
1. **SIFT Minutiae Separation:** SIFT stripe minutiae matching shows clear separation between same-individual pairs (mean: 0.3458) and different-individual pairs (mean: 0.1269).
2. **Generic Deep Feature Compression:** The off-the-shelf ImageNet-pretrained ResNet50 cosine scores are relatively compressed ($0.9053$ vs. $0.8706$) because general ImageNet features respond strongly to generic feline textures rather than fine-grained individual stripe bifurcations. This reinforces why TigerTraceAI's hybrid SIFT+Deep ensembling architecture is critical.

---

## 4. Regression Testing & Invariant Verification

Existing test suites were executed after smoke testing:
1. `tests/test_validate_manifest.py`: **10 / 10 passed (0.039s)**
2. `tests/test_enrollment_audit.py`: **10 / 10 passed (0.773s)**
3. `scripts/validate_dataset_manifest.py --manifest data/staging/atrw_pilot/atrw_pilot_manifest.csv --dataset-root data/staging/atrw_pilot --strict`: **PASSED (0 errors, 0 warnings)**

### Preserved State:
- Canonical manifest ([data/manifests/dataset_manifest.csv](file:///d:/TigerTraceAI-main/data/manifests/dataset_manifest.csv)): **Untouched**
- Production database & schema: **Untouched**
- Enrollment services: **Zero automated approvals or enrollments executed**
- Artifact JSON saved: [data/staging/atrw_pilot/feature_smoke_test.json](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/feature_smoke_test.json)
