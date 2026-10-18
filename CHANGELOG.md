# Changelog

All notable RouteLens changes are recorded here. Upstream history is retained separately below.

## [Unreleased]

### Planned

- Real-video labeled evaluation and visual evidence cards.

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
