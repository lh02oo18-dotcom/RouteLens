# Changelog

All notable RouteLens changes are recorded here. Upstream history is retained separately below.

## [Unreleased]

### Added

- RouteLens project identity, quality checklist, roadmap, decision record, security policy, and third-party notice.
- Reproducible Windows baseline verification with Python 3.12 and RTX 4060 CUDA inference.
- Explicit `lap` tracking dependency and project-local Ultralytics runtime configuration.

### Verified

- YOLO11n + ByteTrack processed a 30-frame smoke video and exported CSV, JSON, and annotated MP4 artifacts.
- Eight unit tests, Ruff, dependency consistency, and Streamlit HTTP health check passed locally.

### Planned

- Tag `v0.1.0` only after the public baseline Pull Request is merged and CI passes.
- Trajectory feature extraction, rule-based anomalies, route clustering, and evidence cards.

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
