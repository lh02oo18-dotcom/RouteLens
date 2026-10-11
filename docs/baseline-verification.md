# RouteLens local baseline verification

Verified on 2026-10-11 before adding RouteLens-specific trajectory-mining and anomaly-explanation features.

## Environment

- Windows, Python 3.12.4
- NVIDIA GeForce RTX 4060 Laptop GPU (8 GB)
- PyTorch 2.14.1+cu126; CUDA available
- Upstream baseline commit: `126f5c5`
- Working branch: `feature/routelens-baseline`

The virtual environment is stored in `.venv`. Ultralytics runtime settings are redirected to the ignored project-local `.runtime` directory so the application does not depend on write access to a Windows user-profile directory.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Baseline result: all dependencies were consistent, all 8 tests passed, and Ruff reported no issues.

## GPU smoke test

The smoke-test video repeats the packaged Ultralytics `bus.jpg` asset for 90 frames. It validates the complete local path from video decoding through YOLO11n inference, ByteTrack tracking, annotation, metrics, and export. It is not a meaningful performance benchmark or anomaly-evaluation dataset.

```powershell
.\.venv\Scripts\python.exe CLI.py `
  --source data\videos\smoke.mp4 `
  --tracker bytetrack `
  --model yolo11n.pt `
  --device 0 `
  --max-frames 30 `
  --output-dir outputs\smoke `
  --save-video
```

Observed result:

- 30 frames processed
- 4 unique track IDs
- annotated MP4, frame metrics, trajectories, crossing events, and JSON summary exported
- no line crossing occurred, as expected for a repeated still-image test video
- reported 1.58 FPS includes model startup and should not be used as the real-video performance figure

The next validation milestone is to run a short real surveillance or road video, measure warm inference speed, and evaluate RouteLens anomaly rules against manually checked events.
