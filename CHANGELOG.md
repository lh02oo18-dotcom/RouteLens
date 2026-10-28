# Changelog

All notable RouteLens changes are recorded here. Upstream history is retained separately below.

## [Unreleased]

No unreleased changes.

## [1.1.0] - 2026-10-28

### Added

- Audited downloader and SHA-256 manifest for three official CAVIAR video/XML pairs.
- CVML annotation loader plus box, trajectory-continuity, and label-derived event evaluation.
- Calibration/held-out protocol comparing YOLO11n and YOLO11s with ByteTrack and BoT-SORT.
- Versioned real-data CSV/JSON results and a reproducible grayscale evaluation figure.

### Findings and boundaries

- YOLO11s + BoT-SORT achieved the best held-out box F1 (0.3958) while processing 61.58 FPS on the verified RTX 4060 environment.
- Both trackers remained above 60 FPS with YOLO11s; their F1 difference was small and changed by sequence.
- Two label-derived loitering references were not detected, so event F1 remained 0; the negative result and label-rule mismatch are documented instead of hidden.
- The three scripted, low-resolution sequences support a small real-data pilot, not cross-camera or production generalisation.

## [1.0.0] - 2026-10-22

### Added

- Anomaly evidence cards with a representative frame, target track overlay, metrics, thresholds, and portable manifest references.
- Explicit generated-canvas fallback for non-seekable sources, plus privacy blur propagation.
- Streamlit evidence gallery and deterministic `tools.evidence_demo` fallback.
- Static GitHub Pages project overview and deployment workflow.

### Stability and verification

- Evidence cards never claim a captured keyframe when the source cannot be read back.
- Synthetic evidence remains labeled as pipeline validation, not real-world accuracy.
- README, architecture, roadmap, demo outline, known issues, and release notes are synchronized for the stable milestone.

## [0.3.0] - 2026-10-18

### Added

- Distance-based trajectory resampling and shared scene normalization.
- Deterministic DBSCAN route clustering, route prototypes, and explainable deviation scores.
- Route assignments, prototypes, and mining-summary CSV/JSON exports plus Streamlit controls.
- Event-level precision/recall/F1 evaluation and a clearly labeled synthetic parameter sweep.

### Safety and verification

- Sessions without a supported route cluster never emit route-deviation events.
- Static and undersized tracks are excluded and counted in the route summary.
- Twenty-one unit tests, Ruff, dependency checks, and the synthetic sweep pass locally.
- Synthetic results verify the pipeline only; real-world accuracy remains unevaluated.

## [0.2.0] - 2026-10-15

### Added

- Per-track speed, heading, path, displacement ratio, turn-angle, activity-radius, and data-quality features.
- Sustained reverse-direction and multi-condition loitering rules with metrics and thresholds.
- Streamlit controls and tables plus CSV/JSON feature and anomaly exports.
- Reproducible synthetic trajectory example and deterministic boundary-case tests.

### Verified

- Fourteen unit tests cover baseline analytics, trajectory features, anomaly rules, and exports.

## [0.1.0] - 2026-10-11

### Added

- RouteLens project identity, quality checklist, roadmap, decision record, security policy, and third-party notice.
- Reproducible Windows baseline verification with Python 3.12 and RTX 4060 CUDA inference.
- Explicit `lap` tracking dependency and project-local Ultralytics runtime configuration.

### Verified

- YOLO11n + ByteTrack processed a 30-frame smoke video and exported CSV, JSON, and annotated MP4 artifacts.
- Eight unit tests, Ruff, dependency consistency, and Streamlit HTTP health check passed locally.

## Upstream 0.2.0

- Added configurable YOLO detector settings.
- Added tracker backend selection for CSRT, ByteTrack, and BoT-SORT.
- Added directional line-crossing analytics.
- Added current occupancy, IN/OUT, peak occupancy, FPS, and latency metrics.
- Added zone occupancy and trajectory exports.
- Added CSV/JSON export pipeline.
- Added Streamlit controls for model, tracker, line crossing, privacy blur, and outputs.
- Added argparse CLI.
- Added benchmark script.
- Added tests, linting configuration, CI workflow, Dockerfile, and Docker Compose.
- Removed the need to commit virtual environments, caches, videos, or model weights.
