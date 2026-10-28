# Iteration 4: licensed real-data evaluation

Version `1.1.0` adds an auditable CAVIAR evaluation path without changing the production analysis rules.

## Scope

- Download and verify three official CAVIAR MPEG/XML pairs by SHA-256.
- Parse CVML boxes, identities, and behaviour labels into RouteLens rows.
- Separate calibration (`Walk1`) from held-out testing (`Browse1`, `Browse_WhileWaiting2`).
- Compare YOLO11n/YOLO11s and ByteTrack/BoT-SORT under the same frozen protocol.
- Export per-sequence metrics, aggregate metrics, run metadata, and a grayscale paper figure.

## Acceptance evidence

- 26 unit tests, Ruff, and dependency checks pass locally.
- The held-out set contains 2,940 video frames, 2,118 labelled frames, and 3,312 reference boxes.
- Best held-out box F1 is 0.3958 for YOLO11s + BoT-SORT at 61.58 FPS.
- Event F1 is 0 because no configured geometric-loitering event matched the two label-derived references; this negative result is retained.
- Raw data and model weights remain outside Git; hashes, commands, configurations, results, and plotting code are versioned.

## Interpretation boundary

This iteration validates a small, scripted, low-resolution real-video subset. It does not establish cross-camera generalisation, natural anomaly prevalence, or production reliability.
