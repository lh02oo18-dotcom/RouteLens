from __future__ import annotations

import json

from people_counter.config_runtime import AnalyticsConfig
from people_counter.trajectory_analysis import analyze_trajectories


def point(track_id: int, frame: int, timestamp: float, x: float, y: float) -> dict:
    return {
        "track_id": track_id,
        "frame_index": frame,
        "timestamp_sec": timestamp,
        "centroid_x": x,
        "centroid_y": y,
    }


def main() -> None:
    rows = [
        point(1, 1, 0.0, 120.0, 100.0),
        point(1, 2, 1.0, 90.0, 100.0),
        point(1, 3, 2.0, 60.0, 100.0),
        point(2, 1, 0.0, 200.0, 200.0),
        point(2, 2, 1.0, 220.0, 200.0),
        point(2, 3, 2.0, 220.0, 220.0),
        point(2, 4, 3.0, 200.0, 220.0),
        point(2, 5, 4.0, 200.0, 200.0),
        point(2, 6, 5.0, 220.0, 200.0),
    ]
    config = AnalyticsConfig(
        expected_direction=(1.0, 0.0),
        anomaly_min_points=3,
        reverse_min_duration_sec=1.5,
        reverse_min_distance_px=40.0,
        loitering_min_duration_sec=4.0,
        loitering_max_radius_px=20.0,
        loitering_min_path_length_px=80.0,
    )
    features, events = analyze_trajectories(rows, config)
    print(json.dumps({"features": features, "events": events}, indent=2))


if __name__ == "__main__":
    main()
