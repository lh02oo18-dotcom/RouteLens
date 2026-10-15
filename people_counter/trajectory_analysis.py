from __future__ import annotations

from collections import defaultdict
from math import acos, atan2, degrees, hypot, isfinite
from statistics import mean
from typing import Any

from .config_runtime import AnalyticsConfig


def analyze_trajectories(
    rows: list[dict[str, Any]], config: AnalyticsConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract per-track features and explainable rule-based anomaly events."""
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        normalized = _normalize_row(row)
        if normalized is not None:
            grouped[normalized["track_id"]].append(normalized)

    features: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for track_id in sorted(grouped):
        points = sorted(
            grouped[track_id],
            key=lambda item: (item["timestamp_sec"], item["frame_index"]),
        )
        feature = extract_trajectory_features(points)
        features.append(feature)
        if feature["point_count"] < max(1, config.anomaly_min_points):
            continue
        events.extend(_reverse_events(points, config))
        loitering = _loitering_event(feature, config)
        if loitering is not None:
            events.append(loitering)

    events.sort(
        key=lambda item: (
            item["start_timestamp_sec"],
            item["track_id"],
            item["event_type"],
        )
    )
    return features, events


def extract_trajectory_features(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Return deterministic geometric and temporal features for one normalized track."""
    if not points:
        raise ValueError("At least one trajectory point is required")

    track_id = int(points[0]["track_id"])
    start = points[0]
    end = points[-1]
    duration = max(0.0, end["timestamp_sec"] - start["timestamp_sec"])
    displacement = _distance(start, end)

    path_length = 0.0
    timed_distance = 0.0
    segment_speeds: list[float] = []
    vectors: list[tuple[float, float]] = []
    duplicate_timestamp_segments = 0
    for previous, current in zip(points, points[1:], strict=False):
        dx = current["centroid_x"] - previous["centroid_x"]
        dy = current["centroid_y"] - previous["centroid_y"]
        distance = hypot(dx, dy)
        path_length += distance
        if distance > 0:
            vectors.append((dx, dy))

        elapsed = current["timestamp_sec"] - previous["timestamp_sec"]
        if elapsed > 0:
            timed_distance += distance
            segment_speeds.append(distance / elapsed)
        else:
            duplicate_timestamp_segments += 1

    turn_angles = _turn_angles(vectors)
    center_x = mean(point["centroid_x"] for point in points)
    center_y = mean(point["centroid_y"] for point in points)
    activity_radius = max(
        hypot(point["centroid_x"] - center_x, point["centroid_y"] - center_y)
        for point in points
    )
    frame_span = max(1, end["frame_index"] - start["frame_index"] + 1)
    heading = (
        degrees(
            atan2(
                end["centroid_y"] - start["centroid_y"],
                end["centroid_x"] - start["centroid_x"],
            )
        )
        if displacement > 0
        else None
    )

    return {
        "track_id": track_id,
        "point_count": len(points),
        "start_frame": start["frame_index"],
        "end_frame": end["frame_index"],
        "observed_frame_span": frame_span,
        "missing_frame_count": max(0, frame_span - len(points)),
        "start_timestamp_sec": _rounded(start["timestamp_sec"]),
        "end_timestamp_sec": _rounded(end["timestamp_sec"]),
        "duration_sec": _rounded(duration),
        "displacement_px": _rounded(displacement),
        "path_length_px": _rounded(path_length),
        "net_displacement_ratio": _rounded(displacement / path_length)
        if path_length > 0
        else 0.0,
        "mean_speed_px_sec": _rounded(timed_distance / duration) if duration > 0 else 0.0,
        "max_speed_px_sec": _rounded(max(segment_speeds)) if segment_speeds else 0.0,
        "heading_deg": _rounded(heading) if heading is not None else None,
        "mean_turn_angle_deg": _rounded(mean(turn_angles)) if turn_angles else 0.0,
        "max_turn_angle_deg": _rounded(max(turn_angles)) if turn_angles else 0.0,
        "activity_radius_px": _rounded(activity_radius),
        "valid_speed_segments": len(segment_speeds),
        "duplicate_timestamp_segments": duplicate_timestamp_segments,
    }


def _reverse_events(
    points: list[dict[str, Any]], config: AnalyticsConfig
) -> list[dict[str, Any]]:
    expected = config.expected_direction
    if expected is None:
        return []
    expected_length = hypot(float(expected[0]), float(expected[1]))
    if expected_length <= 0:
        return []
    expected_unit = (float(expected[0]) / expected_length, float(expected[1]) / expected_length)

    events: list[dict[str, Any]] = []
    run: list[tuple[dict[str, Any], dict[str, Any], float, float]] = []

    def finish_run() -> None:
        if not run:
            return
        start, end = run[0][0], run[-1][1]
        duration = end["timestamp_sec"] - start["timestamp_sec"]
        distance = sum(item[3] for item in run)
        if (
            duration >= config.reverse_min_duration_sec
            and distance >= config.reverse_min_distance_px
        ):
            events.append(
                {
                    "event_type": "reverse_direction",
                    "track_id": start["track_id"],
                    "start_timestamp_sec": _rounded(start["timestamp_sec"]),
                    "end_timestamp_sec": _rounded(end["timestamp_sec"]),
                    "start_frame": start["frame_index"],
                    "end_frame": end["frame_index"],
                    "metric_duration_sec": _rounded(duration),
                    "metric_distance_px": _rounded(distance),
                    "metric_mean_alignment": _rounded(mean(item[2] for item in run)),
                    "threshold_max_alignment": config.reverse_cosine_threshold,
                    "threshold_min_duration_sec": config.reverse_min_duration_sec,
                    "threshold_min_distance_px": config.reverse_min_distance_px,
                    "evidence_reference": (
                        f"trajectory:{start['track_id']}:{start['frame_index']}-{end['frame_index']}"
                    ),
                }
            )

    for previous, current in zip(points, points[1:], strict=False):
        elapsed = current["timestamp_sec"] - previous["timestamp_sec"]
        dx = current["centroid_x"] - previous["centroid_x"]
        dy = current["centroid_y"] - previous["centroid_y"]
        distance = hypot(dx, dy)
        if elapsed <= 0 or distance <= 0:
            finish_run()
            run = []
            continue
        alignment = (dx * expected_unit[0] + dy * expected_unit[1]) / distance
        if alignment <= config.reverse_cosine_threshold:
            run.append((previous, current, alignment, distance))
        else:
            finish_run()
            run = []
    finish_run()
    return events


def _loitering_event(
    feature: dict[str, Any], config: AnalyticsConfig
) -> dict[str, Any] | None:
    if not config.loitering_enabled:
        return None
    if not (
        feature["duration_sec"] >= config.loitering_min_duration_sec
        and feature["activity_radius_px"] <= config.loitering_max_radius_px
        and feature["path_length_px"] >= config.loitering_min_path_length_px
    ):
        return None
    return {
        "event_type": "loitering",
        "track_id": feature["track_id"],
        "start_timestamp_sec": feature["start_timestamp_sec"],
        "end_timestamp_sec": feature["end_timestamp_sec"],
        "start_frame": feature["start_frame"],
        "end_frame": feature["end_frame"],
        "metric_duration_sec": feature["duration_sec"],
        "metric_activity_radius_px": feature["activity_radius_px"],
        "metric_path_length_px": feature["path_length_px"],
        "threshold_min_duration_sec": config.loitering_min_duration_sec,
        "threshold_max_radius_px": config.loitering_max_radius_px,
        "threshold_min_path_length_px": config.loitering_min_path_length_px,
        "evidence_reference": (
            f"trajectory:{feature['track_id']}:{feature['start_frame']}-{feature['end_frame']}"
        ),
    }


def _normalize_row(row: dict[str, Any]) -> dict[str, Any] | None:
    try:
        normalized = {
            "track_id": int(row["track_id"]),
            "frame_index": int(row["frame_index"]),
            "timestamp_sec": float(row["timestamp_sec"]),
            "centroid_x": float(row["centroid_x"]),
            "centroid_y": float(row["centroid_y"]),
        }
    except (KeyError, TypeError, ValueError):
        return None
    if not all(
        isfinite(normalized[key])
        for key in ("timestamp_sec", "centroid_x", "centroid_y")
    ):
        return None
    return normalized


def _turn_angles(vectors: list[tuple[float, float]]) -> list[float]:
    angles: list[float] = []
    for first, second in zip(vectors, vectors[1:], strict=False):
        first_length = hypot(*first)
        second_length = hypot(*second)
        cosine = (first[0] * second[0] + first[1] * second[1]) / (
            first_length * second_length
        )
        angles.append(degrees(acos(max(-1.0, min(1.0, cosine)))))
    return angles


def _distance(first: dict[str, Any], second: dict[str, Any]) -> float:
    return hypot(
        second["centroid_x"] - first["centroid_x"],
        second["centroid_y"] - first["centroid_y"],
    )


def _rounded(value: float) -> float:
    return round(float(value), 3)
