from people_counter.config_runtime import AnalyticsConfig
from people_counter.route_mining import mine_routes, resample_trajectory


def _track(track_id, y, x_offset=0.0):
    return [
        {
            "track_id": track_id,
            "frame_index": index + 1,
            "timestamp_sec": float(index),
            "centroid_x": x_offset + index * 10.0,
            "centroid_y": y,
        }
        for index in range(5)
    ]


def test_resampling_keeps_endpoints_and_equal_spacing():
    points = _track(1, y=4.0)

    sampled = resample_trajectory(points, sample_count=3)

    assert sampled == [(0.0, 4.0), (20.0, 4.0), (40.0, 4.0)]


def test_dbscan_finds_main_route_and_scores_distant_track():
    rows = (
        _track(1, y=0.0)
        + _track(2, y=1.0)
        + _track(3, y=2.0)
        + _track(9, y=80.0)
    )
    config = AnalyticsConfig(
        route_min_points=5,
        route_resample_points=8,
        route_dbscan_eps=0.05,
        route_dbscan_min_samples=3,
        route_deviation_threshold=0.5,
    )

    assignments, prototypes, summary, events = mine_routes(rows, config)

    assert summary["status"] == "ready"
    assert summary["cluster_count"] == 1
    assert summary["noise_track_count"] == 1
    assert len(prototypes) == 8
    distant = next(row for row in assignments if row["track_id"] == 9)
    assert distant["cluster_id"] == -1
    assert distant["nearest_cluster_id"] == 0
    assert distant["is_deviation"] is True
    assert [event["track_id"] for event in events] == [9]
    assert events[0]["event_type"] == "route_deviation"


def test_no_cluster_means_no_false_deviation_event():
    rows = _track(1, y=0.0) + _track(2, y=100.0)
    config = AnalyticsConfig(
        route_dbscan_eps=0.01,
        route_dbscan_min_samples=3,
        route_deviation_threshold=0.01,
    )

    assignments, prototypes, summary, events = mine_routes(rows, config)

    assert summary["status"] == "insufficient_cluster_support"
    assert summary["cluster_count"] == 0
    assert prototypes == []
    assert events == []
    assert all(row["is_deviation"] is False for row in assignments)
    assert all(row["deviation_score"] is None for row in assignments)


def test_short_and_static_tracks_are_excluded_with_reason_counts():
    short = _track(1, y=0.0)[:2]
    static = [
        {
            "track_id": 2,
            "frame_index": index,
            "timestamp_sec": float(index),
            "centroid_x": 3.0,
            "centroid_y": 4.0,
        }
        for index in range(5)
    ]

    assignments, _, summary, events = mine_routes(short + static, AnalyticsConfig())

    assert assignments == []
    assert events == []
    assert summary["input_track_count"] == 2
    assert summary["eligible_track_count"] == 0
    assert summary["static_track_count"] == 1


def test_route_mining_can_be_disabled():
    assignments, prototypes, summary, events = mine_routes(
        _track(1, y=0.0), AnalyticsConfig(route_mining_enabled=False)
    )

    assert assignments == []
    assert prototypes == []
    assert events == []
    assert summary["status"] == "disabled"
