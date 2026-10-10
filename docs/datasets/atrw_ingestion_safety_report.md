# ATRW Pilot: Isolated End-to-End Ingestion and Enrollment Safety Test Report

**Execution Date / Time**: 2026-10-10 07:05:37 UTC  
**Environment**: Windows, Python 3.10, PyTorch (CPU-only), OpenCV 4.11.0, SQLite3  
**Report Artifact**: [`data/staging/atrw_pilot/ingestion_safety_test_report.json`](file:///d:/TigerTraceAI-main/data/staging/atrw_pilot/ingestion_safety_test_report.json)  
**Test Suite**: [`tests/test_atrw_ingestion_safety.py`](file:///d:/TigerTraceAI-main/tests/test_atrw_ingestion_safety.py)  

---

## 1. Executive Summary & Safety Declaration

An isolated test harness was designed and executed to verify the ingestion validation and Re-ID enrollment decision flow for the **13 approved ATRW pilot crops** without modifying or touching production state.

### Mandatory Safety Invariant Audit
All tests executed inside ephemeral sandbox SQLite databases created in temporary directories with explicit teardown. Cryptographic SHA-256 hashing was performed before and after the test execution across all production assets:

| Asset Name | Target Path | SHA-256 Baseline | SHA-256 Post-Test | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Production SQLite DB** | `TigerTrace_AI/data/database/tigertrace.db` | `72857a2627a34439708e2664e3457c4226e4bc6b82f684d0aff722907a3722ba` | `72857a2627a34439708e2664e3457c4226e4bc6b82f684d0aff722907a3722ba` | **Unchanged (0 writes)** |
| **Canonical Manifest** | `data/manifests/dataset_manifest.csv` | `c0a1589a08d8c8584725738f1c67c1b0ff76c9897b4b49fd6247de49691ec922` | `c0a1589a08d8c8584725738f1c67c1b0ff76c9897b4b49fd6247de49691ec922` | **Unchanged (0 writes)** |
| **ATRW Pilot Manifest** | `data/staging/atrw_pilot/atrw_pilot_manifest.csv` | `8c607f2ef8c1aa93fe9a8e0f63bfe92a6c8e390c4c4786d38e2d27f88e63da22` | `8c607f2ef8c1aa93fe9a8e0f63bfe92a6c8e390c4c4786d38e2d27f88e63da22` | **Unchanged (13 records)** |

> [!IMPORTANT]
> **No Model Training & No Probabilistic Calibration**:  
> No models were trained or fine-tuned. Feature comparison scores are raw exploratory distances and are never treated as calibrated probabilities. No new individual animal identity was automatically confirmed.

---

## 2. Test Execution & Scenario Verification

### Executed Command
```powershell
python -m unittest tests/test_atrw_ingestion_safety.py
```
**Output**: `Ran 8 tests in 0.839s — OK`

### Scenario Verification Matrix

| Scenario ID | Test Name | Target Condition | Decision State | Ingestion / DB Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `test_scenario_01_valid_approved_image_proceeds` | Approved crop with verified SHA-256 and review status | `PROCEEDED_TO_FEATURE_EXTRACTION` | Validated across all 13 pilot crops; extraction yielded `(384, 384, 3)` flank crop. | **PASSED** |
| **02** | `test_scenario_02_missing_or_mismatched_checksum_rejected` | Corrupted checksum or nonexistent file path | `INGESTION_REJECTED` | Pre-flight halted execution; 0 DB mutations; 0 feature extraction calls. | **PASSED** |
| **03** | `test_scenario_03_repeated_exact_image_hash_flagged_duplicate` | Exact SHA-256 collision in ingestion stream | `FLAGGED_DUPLICATE` | Collision flagged immediately; 0 catalogue pollution. Pilot manifest verified collision-free. | **PASSED** |
| **04** | `test_scenario_04_similarity_ambiguity_routes_to_human_review` | Intermediate similarity score ($0.35 \le s < 0.50$) | `REVIEW_REQUIRED` | Sighting marked `pending_review`; staged into `review_queue`; NO animal enrolled into `tigers`. | **PASSED** |
| **05** | `test_scenario_05_empty_catalogue_does_not_auto_enroll` | Query against empty animal catalogue ($0$ references) | `NEW_IDENTITY_CANDIDATE_PENDING` | `confidence=0.0`; staged into `review_queue`; 0 rows inserted into `tigers`. | **PASSED** |
| **06** | `test_scenario_06_potential_duplicate_blocks_approval` | High similarity candidate ($s = 0.65 \ge 0.30$) | `APPROVAL_BLOCKED_DUPLICATE_FLAGGED` | Enrollment halted (`possible_duplicate_flagged`). Approved only when explicit audited `force=True` override provided. | **PASSED** |
| **07** | `test_scenario_07_failed_feature_extraction_creates_no_identity` | 0-byte corrupt/unreadable crop fixture | `UNKNOWN_FEATURE_EXTRACTION_FAILED` | Decision `unknown`; reason `corrupt_or_unreadable_image`; sighting pending; 0 tigers enrolled. | **PASSED** |
| **08** | `test_scenario_08_unassigned_split_remains_unassigned` | Manifest partition check across all 13 approved records | `SPLIT_PRESERVED_UNASSIGNED` | All 13 pilot records verified with `split='unassigned'`; 0 samples in `train`, `test`, or `val`. | **PASSED** |

---

## 3. Structured Decision Audit Trail

Every triage action emits structured audit events recording the input sample ID, provenance source identity mapping, decision state, triage reason, and whether any database mutation occurred:

| Scenario | Input Sample ID | Source Identity Mapping | Decision State | Triage Rationale | Sandbox DB Mutated | Prod DB Mutated |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **01** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `PROCEEDED_TO_FEATURE_EXTRACTION` | `valid_checksum_and_verified_review_status` | No | **No** |
| **02** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `INGESTION_REJECTED` | `checksum_mismatch_detected_at_preflight` | No | **No** |
| **03** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `FLAGGED_DUPLICATE` | `exact_sha256_hash_collision_in_stream` | No | **No** |
| **04** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `REVIEW_REQUIRED` | `ambiguous_score_0.42_in_review_band` | Yes (Pending Queue) | **No** |
| **05** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `NEW_IDENTITY_CANDIDATE_PENDING` | `empty_catalogue_requires_explicit_approval` | Yes (Pending Queue) | **No** |
| **06** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `APPROVAL_BLOCKED_DUPLICATE_FLAGGED` | `score_0.65_ge_thresh_0.30` | No | **No** |
| **06 (Override)** | `atrw_pilot_0001` | `tiger_001` (ATRW 153) | `APPROVAL_CONFIRMED_AUDITED_OVERRIDE` | `audited_biologist_override_with_documented_verification` | Yes (Audited Enrollment) | **No** |
| **07** | `SYNTH_CORRUPT_CROP` | `synthetic_fixture` | `UNKNOWN_FEATURE_EXTRACTION_FAILED` | `corrupt_or_unreadable_image` | Yes (Pending Sighting) | **No** |
| **08** | `ALL_13_PILOT_SAMPLES` | `ALL_PILOT_IDENTITIES` | `SPLIT_PRESERVED_UNASSIGNED` | `unpartitioned_isolated_smoke_test_state` | No | **No** |

---

## 4. Regression & Multi-Suite Test Results

In addition to the new safety harness, existing test suites were executed to ensure complete backwards compatibility and pipeline integrity:

```powershell
python -m unittest tests/test_validate_manifest.py tests/test_enrollment_audit.py
```
**Results**:
- `tests/test_validate_manifest.py`: 10 passed (manifest validation, required columns, regex checks, checksum verification).
- `tests/test_enrollment_audit.py`: 10 passed (enrollment triage logic, duplicate blocking, human-in-the-loop review queue).
- **Total Combined Tests**: **28 tests passing across 3 suites with 0 failures and 0 errors**.

---

## 5. Limitations & Unresolved Safety Issues

1. **Synthetic & Heuristic Bounding Boxes in Staging Pilot**:
   The ATRW Re-ID train images are pre-extracted bounding crops. In `atrw_pilot_manifest.csv`, `bbox_coordinates` was populated with normalized coordinates `[0.0, 0.0, 1.0, 1.0]`. When transitioning to full-frame camera trap imagery, upstream automated detection and segmentation models must be rigorously evaluated before ingestion into the flank feature extractor.
2. **Deterministic Mock vs. Production Model Embeddings**:
   To ensure test determinism and prevent CPU/GPU variance or slow model weight downloads during unit tests, triage decisions in scenarios 4–6 utilized a controlled mock matcher (`ControlledDeterministicMatcher`). A live feature extraction smoke test on the real PyTorch backbone was verified in Step 5 (`docs/datasets/atrw_feature_smoke_test.md`), but live matching across real images will require calibrated biological validation.
3. **Flank Orientation Discrepancies**:
   Individual tigers cannot be matched across opposing flanks (left flank vs. right flank) via 2D stripe pattern matching. The pilot manifest maintains separate flank metadata, but cross-flank rejection must be strictly enforced at the matching engine layer before field deployment.
4. **No Claim of Field Readiness or Statistical Accuracy**:
   Passing these unit tests certifies architectural safety, sandbox isolation, and triage routing integrity. It does **NOT** establish accuracy on wild Indian tiger populations (e.g., Pench/Tadoba) or field readiness.
