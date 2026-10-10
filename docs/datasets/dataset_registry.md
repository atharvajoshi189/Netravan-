# Candidate Dataset Registry for Species-Agnostic Wildlife Monitoring

This registry catalogues candidate external wildlife datasets under consideration for the TigerTraceAI species-agnostic multi-species expansion and benchmarking framework.

> **Status Notice:**  
> Inclusion in this registry **does not imply endorsement, download, or approval for operational use**.  
> In accordance with project policy:
> - **None of these candidate datasets have been downloaded, ingested, or approved.**
> - All licensing, privacy terms, format specifications, and file sizes are provisional.
> - Any item not directly verified against official authoritative documentation is explicitly marked as `needs_verification`.

---

## 1. ATRW (Amur Tiger Re-identification in the Wild)

- **Intended Task**: Individual tiger detection, bounding box localization, pose keypoint estimation, and individual tiger re-identification (Re-ID).
- **Modality**: Video clips and still frame extractions (RGB imagery).
- **Availability of Individual IDs**: Available for the Re-ID benchmark subset (individual identity labels assigned to recognized Amur tigers).
- **Annotation Formats**: Plain text and JSON annotation formats containing bounding boxes, pose keypoints, and individual ID integers/strings (`needs_verification` for complete format specification across all splits).
- **Official URL**: [https://lila.science/datasets/atrw](https://lila.science/datasets/atrw)
- **Licensing / Access Restrictions**: Non-commercial academic research use; underlying terms subject to original dataset creators' terms of use (`needs_verification` for commercial reuse and redistribution permissions).
- **Documented Size**: Documented at ~8,076 video clips / images covering ~92 individual Amur tigers; total uncompressed archive size is `needs_verification`.
- **Limitations**:
  - Images were primarily acquired in semi-wild zoological park conditions (Heilongjiang Siberian Tiger Park), meaning background vegetation, lighting, and viewing angles differ from true remote camera trap conditions in tropical reserves like Pench.
  - Amur tigers (*Panthera tigris altaica*) possess heavier winter coats and different stripe density compared to Bengal tigers (*Panthera tigris tigris*).
  - High proportion of clean lateral flank viewpoints relative to random camera trap trigger angles.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## 2. LILA BC Hyena ID 2022

- **Intended Task**: Individual spotted hyena (*Crocuta crocuta*) re-identification and coat spot pattern biometric matching.
- **Modality**: Camera trap and field survey still photographs (RGB daylight and monochrome/infrared night captures).
- **Availability of Individual IDs**: Available (unique individual identifiers assigned to catalogued individual hyenas).
- **Annotation Formats**: Bounding box coordinates and individual identity tags; exact annotation schema (`COCO Camera Traps` vs custom JSON/CSV) is `needs_verification`.
- **Official URL**: [https://lila.science/datasets](https://lila.science/datasets)
- **Licensing / Access Restrictions**: `needs_verification` (Community conservation research dataset hosted on LILA BC; specific Creative Commons or custom research license requires verification).
- **Documented Size**: `needs_verification` for total image count, individual count, and byte volume.
- **Limitations**:
  - Pelage biometric pattern consists of non-linear spot distributions rather than continuous lateral stripes; stripe-based SIFT minutiae algorithms require adaptation or multi-feature ensembling for spot topologies.
  - High ratio of night-time flash/infrared illumination causing potential spot pattern washout.
  - Viewpoint variation across natural terrain includes significant head/scapula occlusion.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## 3. LILA BC Beluga ID 2022

- **Intended Task**: Individual beluga whale (*Delphinapterus leucas*) photo-identification and aquatic mark-recapture tracking.
- **Modality**: Surface and aerial wildlife photography (RGB images).
- **Availability of Individual IDs**: Available (individual whale identifiers based on dorsal ridge pigmentation, scarring, and skin markings).
- **Annotation Formats**: Image-level individual ID assignments, crop bounding boxes, and body landmark annotations (`needs_verification` for exact schema).
- **Official URL**: [https://lila.science/datasets](https://lila.science/datasets)
- **Licensing / Access Restrictions**: `needs_verification` (Marine mammal research contribution hosted via LILA; specific usage and attribution license requires verification).
- **Documented Size**: `needs_verification` for exact image count and archive size.
- **Limitations**:
  - Fully aquatic marine modality; images feature severe water refraction, surface wave reflections, specular glare, and variable turbidity.
  - Biometric features rely primarily on acquired physical scars, dorsal contour markings, and notch morphology rather than genetic coat patterns like feline stripes.
  - Fundamentally incompatible with terrestrial passive infrared camera trap triage and flank extraction models without specialized marine pre-processing.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## 4. Caltech Camera Traps (CCT)

- **Intended Task**: Automated wildlife detection, blank frame filtering (triage), and multi-species classification.
- **Modality**: Static passive infrared (PIR) motion-triggered camera trap still images (RGB and nighttime IR).
- **Availability of Individual IDs**: **Not available** (Annotations provide species labels, blank frame indicators, and bounding boxes, but individual animal identities are not tracked).
- **Annotation Formats**: COCO Camera Traps JSON format (`images`, `annotations`, `categories` with bounding boxes and species tags).
- **Official URL**: [https://lila.science/datasets/caltech-camera-traps](https://lila.science/datasets/caltech-camera-traps)
- **Licensing / Access Restrictions**: Community Data License Agreement (CDLA-Permissive) / Academic research license (`needs_verification` for exact version).
- **Documented Size**: ~243,100 images captured across 140 camera locations in the Southwestern United States (~130 GB uncompressed).
- **Limitations**:
  - Completely lacks individual re-identification labels; unsuitable for individual Re-ID benchmarking.
  - Geographic and faunal distribution covers North American species (deer, coyote, bobcat), not South Asian tropical wildlife (tiger, leopard, dhole, sloth bear).
  - Can serve as a benchmark for blank/animal triage filter robustness, but not for individual re-identification.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## 5. Wildlife Insights Public Downloads

- **Intended Task**: Large-scale species classification, deployment metadata analysis, blank filtering, and spatial-temporal biodiversity monitoring.
- **Modality**: Remote sensor camera trap images (RGB and IR) alongside deployment metadata tables.
- **Availability of Individual IDs**: **Not available** (Public downloads provide species-level taxonomies; individual identities are not labeled in public tiers).
- **Annotation Formats**: Tabular CSV / JSON following the Wildlife Insights Camera Trap Metadata Standard (files for `projects.csv`, `deployments.csv`, `images.csv`, `identifications.csv`).
- **Official URL**: [https://www.wildlifeinsights.org/get-started/download/public-downloads](https://www.wildlifeinsights.org/get-started/download/public-downloads)
- **Licensing / Access Restrictions**: Varies by project (commonly CC0, CC-BY, or CC-BY-NC); public downloads require adherence to Wildlife Insights Terms of Use; coordinates for sensitive and endangered taxa are intentionally generalized or obscured to prevent poaching.
- **Documented Size**: Multi-institutional global repository encompassing millions of records (`needs_verification` for specific download package byte size).
- **Limitations**:
  - No individual re-identification labels.
  - GPS coordinates for high-risk endangered species (including *Panthera tigris*) are intentionally fuzzed or withheld by data owners for conservation security.
  - Variable image resolution, camera models, trigger delays, and observer validation quality across contributing organizations.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## 6. Movebank Animal Movement Studies

- **Intended Task**: High-resolution animal movement trajectory modeling, home-range estimation, spatial occupancy, and behavioral step-selection analysis.
- **Modality**: GPS telemetry location fixes, Argos Doppler tracking, acceleration sensor streams, and environmental covariates (Tabular spatial-temporal time-series data; **non-visual modality**).
- **Availability of Individual IDs**: **Available** (Track records are explicitly linked to unique animal identifiers and transmitter tag IDs).
- **Annotation Formats**: Movebank tabular CSV / netCDF formats containing `timestamp`, `location-lat`, `location-long`, `individual-local-identifier`, `tag-local-identifier`, and sensor metrics.
- **Official URL**: [https://www.movebank.org/cms/movebank-content/access-data](https://www.movebank.org/cms/movebank-content/access-data)
- **Licensing / Access Restrictions**: Study-specific data sharing policies; studies range from CC0 open access to restricted access requiring direct PI authorization and formal data use agreements (`needs_verification` per study).
- **Documented Size**: Highly variable across thousands of registered studies (`needs_verification` for specific tiger/carnivore tracking repositories).
- **Limitations**:
  - Contains no camera trap visual imagery; modality is strictly spatial-temporal coordinate telemetry.
  - Telemetry fix intervals and GPS positional accuracy vary significantly by collar model, canopy density, and battery duty cycle.
  - Relocation studies on wild tigers require strict data confidentiality to safeguard animal locations against unauthorized disclosure.
- **Current Operational Status**: `needs_verification` / `candidate_only` (Not downloaded; not approved).

---

## Candidate Dataset Summary Matrix

| Dataset Candidate | Intended Task | Modality | Individual IDs | Annotation Format | Size Documented | License / Terms | Operational Status |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **ATRW** | Tiger Detection & Re-ID | RGB Video / Stills | **Yes** | Plain text / JSON | ~8,076 images, 92 IDs | Academic / non-commercial (`needs_verification`) | `candidate_only` |
| **LILA BC Hyena ID 2022** | Hyena Spot Re-ID | Camera Trap Stills | **Yes** | BBoxes + ID tags (`needs_verification`) | `needs_verification` | Open / Research (`needs_verification`) | `candidate_only` |
| **LILA BC Beluga ID 2022** | Beluga Photo-ID | Marine Surface RGB | **Yes** | Mark / ID annotations (`needs_verification`) | `needs_verification` | Research (`needs_verification`) | `candidate_only` |
| **Caltech Camera Traps** | Species Detection / Triage | Camera Trap Stills | **No** | COCO Camera Traps JSON | ~243k images (~130 GB) | CDLA-Permissive (`needs_verification`) | `candidate_only` |
| **Wildlife Insights Public** | Multi-Species Monitoring | Camera Trap Stills | **No** | WI Metadata Standard CSV | Millions of records (`needs_verification`) | CC0 / CC-BY / CC-BY-NC (Project dependent) | `candidate_only` |
| **Movebank Studies** | Spatial Movement Modeling | GPS Telemetry Tabular | **Yes** | Movebank Time-Series CSV | Variable by study (`needs_verification`) | Study-specific licenses (`needs_verification`) | `candidate_only` |

---

## Operational Verification Checklist

Before advancing any candidate dataset from `candidate_only` to `approved_for_evaluation`:
- [ ] Verify terms of service and license compatibility with TigerTraceAI offline field usage.
- [ ] Confirm absence of sensitive location disclosures for endangered species.
- [ ] Validate annotation schema compatibility against the standardized manifest specification (`data/manifests/dataset_manifest.csv`).
- [ ] Perform checksum SHA256 integrity verification upon archive retrieval.
- [ ] Inspect individual identity distribution to prevent class imbalance or split leakage.