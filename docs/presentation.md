# Project presentation and demo outline

## Five-minute narrative

### 0:00–0:40 Problem

Traditional people-flow tools report counts and line crossings but cannot explain the main routes or why a trajectory is unusual. RouteLens turns detection and tracking output into explainable trajectory patterns and anomaly evidence.

### 0:40–1:20 Open-source reuse

Use the ADR interface table to show the reused YOLO, ByteTrack, video loop, and exporters, followed by RouteLens-specific trajectory features, clustering, events, and evidence cards. Preserve upstream attribution and avoid presenting foundation features as new work.

### 1:20–2:20 Incremental delivery

Show branches, Issues, Pull Requests, and Actions. Start with the runnable v0.1 baseline, then explain how v0.2, v0.3, and v1.0.0 introduce rule-based anomalies, data mining, and evidence cards. Use the progress log for one real problem-resolution example.

### 2:20–3:50 Live demo

1. Start Streamlit.
2. Upload a fixed short video.
3. Show detections, trajectories, and baseline metrics.
4. Show the route cluster assignments, deviation score, and anomaly list.
5. Open one evidence card and point to the keyframe, trajectory, metric and threshold.
6. Download CSV/JSON and explain how results can be audited.

### 3:50–4:30 Evaluation and limits

Describe the data source, manual labels, thresholds, precision/recall, occlusion, ID switches, and scene-transfer limitations. Do not present the static smoke test's 1.58 FPS as real-video performance.

### 4:30–5:00 Engineering quality

Show the quick start, license and notice, tests, CI, Release, and known issues, then finish with the public repository URL.

## Demo fallback

- Cache model weights before an offline presentation.
- Keep a verified 30–60 second video and parameter set.
- Keep exported annotated video, CSV, JSON, and evidence-card screenshots.
- If the UI fails, run the same pipeline through the CLI.
- If no GPU is available, switch to CPU and a shorter video.
