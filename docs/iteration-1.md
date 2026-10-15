# Iteration 1: trajectory features and explainable rules

Date: 2026-10-15

## Goal and reuse boundary

The open-source baseline continues to provide YOLO person detection and multi-object tracking. This iteration starts at the exported centroid trajectory and adds RouteLens-owned, deterministic analysis. It does not change detector weights or claim that rule-based events are learned classifications.

## Added interface

`people_counter.trajectory_analysis.analyze_trajectories(rows, config)` accepts the existing trajectory-row format and returns one feature row per track and zero or more explainable anomaly-event rows.

Feature rows include duration, displacement, path length, net displacement ratio, mean and maximum speed, heading, turn angle, activity radius, missing-frame count, and duplicate-timestamp count. Distances use image pixels and speed uses pixels per second.

Event rows include the event type, track ID, time and frame range, measured values, thresholds, and a trajectory evidence reference. `VideoCounter` exports these rows as `trajectory_features.csv`, `anomaly_events.csv`, and `anomaly_events.json`.

## Rule definitions

### Reverse direction

The user supplies an expected scene direction vector. Each positive-duration movement segment is compared with it using cosine alignment. A reverse event is emitted only when consecutive conflicting segments exceed both `reverse_min_duration_sec` and `reverse_min_distance_px`. A single jittering frame therefore cannot create an event.

### Loitering

A track is marked as loitering only when duration is long enough, activity radius is small enough, and path length is long enough. The path-length condition prevents a completely stationary detection from being treated as meaningful movement.

## Reproducible example

```powershell
.\.venv\Scripts\python.exe -m tools.trajectory_demo
```

The synthetic example produces one sustained reverse-direction event and one loitering event, together with their feature evidence. Automated tests cover short tracks, missing frames, duplicate timestamps, a one-segment fluctuation, sustained reverse movement, loitering, invalid rows, and file export.

## Risks and limitations

- Pixel speed is not real-world speed; perspective calibration is required for metres per second.
- Thresholds are scene-specific and should be recorded with evaluation results.
- Tracker ID switches can split one person's trajectory or join different people.
- Reverse detection is disabled until an expected direction is configured.
- These rules are explainable heuristics. Route clustering and data-driven deviation detection remain planned for the next iteration.
