import pytest

from people_counter.config_runtime import AnalyticsConfig
from people_counter.trajectory_analysis import analyze_trajectories


def _row(track_id, frame, timestamp, x, y=0.0):
    return {
        "track_id": track_id,
        "frame_index": frame,
        "timestamp_sec": timestamp,
        "centroid_x": x,
        "centroid_y": y,
    }


def test_extracts_straight_trajectory_features():
    rows = [_row(7, index + 1, float(index), index * 3.0) for index in range(4)]

    features, events = analyze_trajectories(rows, AnalyticsConfig(loitering_enabled=False))

    assert events == []
    assert features == [
        {
            "track_id": 7,
            "point_count": 4,
            "start_frame": 1,
            "end_frame": 4,
            "observed_frame_span": 4,
            "missing_frame_count": 0,
            "start_timestamp_sec": 0.0,
            "end_timestamp_sec": 3.0,
            "duration_sec": 3.0,
            "displacement_px": 9.0,
            "path_length_px": 9.0,
            "net_displacement_ratio": 1.0,
            "mean_speed_px_sec": 3.0,
            "max_speed_px_sec": 3.0,
            "heading_deg": 0.0,
            "mean_turn_angle_deg": 0.0,
            "max_turn_angle_deg": 0.0,
            "activity_radius_px": 4.5,
            "valid_speed_segments": 3,
            "duplicate_timestamp_segments": 0,
        }
    ]


def test_short_track_duplicate_timestamps_and_missing_frames_are_deterministic():
    rows = [
        _row(1, 1, 0.0, 0.0),
        _row(1, 4, 1.0, 3.0),
        _row(1, 5, 1.0, 6.0),
        _row(2, 9, 2.0, 4.0, 5.0),
    ]

    features, _ = analyze_trajectories(rows, AnalyticsConfig(loitering_enabled=False))

    first, second = features
    assert first["path_length_px"] == 6.0
    assert first["mean_speed_px_sec"] == 3.0
    assert first["max_speed_px_sec"] == 3.0
    assert first["duplicate_timestamp_segments"] == 1
    assert first["missing_frame_count"] == 2
    assert second["duration_sec"] == 0.0
    assert second["heading_deg"] is None
    assert second["mean_speed_px_sec"] == 0.0


def test_reverse_direction_requires_sustained_conflict():
    sustained = [
        _row(1, 1, 0.0, 10.0),
        _row(1, 2, 1.0, 7.0),
        _row(1, 3, 2.0, 4.0),
    ]
    fluctuation = [
        _row(2, 1, 0.0, 0.0),
        _row(2, 2, 0.5, -3.0),
        _row(2, 3, 1.0, 3.0),
    ]
    config = AnalyticsConfig(
        expected_direction=(1.0, 0.0),
        anomaly_min_points=3,
        reverse_cosine_threshold=-0.5,
        reverse_min_duration_sec=1.5,
        reverse_min_distance_px=5.0,
        loitering_enabled=False,
    )

    _, events = analyze_trajectories(sustained + fluctuation, config)

    assert len(events) == 1
    assert events[0]["event_type"] == "reverse_direction"
    assert events[0]["track_id"] == 1
    assert events[0]["metric_duration_sec"] == 2.0
    assert events[0]["metric_mean_alignment"] == -1.0


def test_loitering_combines_duration_radius_and_path_length():
    rows = [
        _row(3, 1, 0.0, 0.0, 0.0),
        _row(3, 2, 1.0, 2.0, 0.0),
        _row(3, 3, 2.0, 2.0, 2.0),
        _row(3, 4, 3.0, 0.0, 2.0),
        _row(3, 5, 4.0, 0.0, 0.0),
        _row(3, 6, 5.0, 2.0, 0.0),
        _row(3, 7, 6.0, 2.0, 2.0),
    ]
    config = AnalyticsConfig(
        anomaly_min_points=5,
        loitering_min_duration_sec=5.0,
        loitering_max_radius_px=2.0,
        loitering_min_path_length_px=10.0,
    )

    _, events = analyze_trajectories(rows, config)

    assert len(events) == 1
    assert events[0]["event_type"] == "loitering"
    assert events[0]["metric_duration_sec"] == 6.0
    assert events[0]["metric_path_length_px"] == pytest.approx(12.0)


def test_invalid_rows_are_ignored():
    rows = [
        _row(1, 1, 0.0, 0.0),
        {"track_id": 1, "frame_index": 2},
        _row(1, 3, float("nan"), 2.0),
    ]

    features, events = analyze_trajectories(rows, AnalyticsConfig(loitering_enabled=False))

    assert features[0]["point_count"] == 1
    assert events == []
