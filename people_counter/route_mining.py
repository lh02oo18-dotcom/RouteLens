from __future__ import annotations

from collections import defaultdict, deque
from math import hypot, isfinite, sqrt
from statistics import mean
from typing import Any

from .config_runtime import AnalyticsConfig

UNVISITED = -99
NOISE = -1


def mine_routes(
    rows: list[dict[str, Any]], config: AnalyticsConfig
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
]:
    """Discover common routes and return explainable deviation results.

    Trajectories are resampled by travelled distance, normalized with shared scene
    bounds, and clustered with a small deterministic DBSCAN implementation.  No
    deviation is emitted unless at least one supported route cluster exists.
    """
    parameters = {
        "min_points": max(2, int(config.route_min_points)),
        "resample_points": max(2, int(config.route_resample_points)),
        "dbscan_eps": max(0.0, float(config.route_dbscan_eps)),
        "dbscan_min_samples": max(1, int(config.route_dbscan_min_samples)),
        "deviation_threshold": max(0.0, float(config.route_deviation_threshold)),
    }
    if not config.route_mining_enabled:
        return [], [], _summary("disabled", parameters), []

    grouped = _group_rows(rows)
    eligible: dict[int, list[dict[str, Any]]] = {}
    resampled: dict[int, list[tuple[float, float]]] = {}
    static_tracks = 0
    for track_id in sorted(grouped):
        points = grouped[track_id]
        if len(points) < parameters["min_points"]:
            continue
        sampled = resample_trajectory(points, parameters["resample_points"])
        if _path_length(sampled) <= 0:
            static_tracks += 1
            continue
        eligible[track_id] = points
        resampled[track_id] = sampled

    if not resampled:
        summary = _summary("insufficient_trajectories", parameters)
        summary.update(
            {
                "input_track_count": len(grouped),
                "eligible_track_count": 0,
                "static_track_count": static_tracks,
            }
        )
        return [], [], summary, []

    bounds = _scene_bounds(resampled)
    vectors = {
        track_id: _normalize_path(points, bounds)
        for track_id, points in resampled.items()
    }
    track_ids = sorted(vectors)
    labels = _dbscan(
        [vectors[track_id] for track_id in track_ids],
        eps=parameters["dbscan_eps"],
        min_samples=parameters["dbscan_min_samples"],
    )
    clusters = sorted({label for label in labels if label != NOISE})
    prototypes = _cluster_prototypes(track_ids, vectors, labels, bounds)
    prototype_vectors = {
        cluster_id: _mean_vector(
            [vectors[track_id] for track_id, label in zip(track_ids, labels, strict=True) if label == cluster_id]
        )
        for cluster_id in clusters
    }

    assignments: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for track_id, label in zip(track_ids, labels, strict=True):
        nearest_cluster_id, deviation_score = _nearest_prototype(
            vectors[track_id], prototype_vectors, preferred=label
        )
        has_reference_route = nearest_cluster_id is not None
        is_deviation = bool(
            has_reference_route
            and deviation_score is not None
            and deviation_score >= parameters["deviation_threshold"]
        )
        points = eligible[track_id]
        assignment = {
            "track_id": track_id,
            "cluster_id": label,
            "is_noise": label == NOISE,
            "nearest_cluster_id": nearest_cluster_id,
            "point_count": len(points),
            "deviation_score": _rounded(deviation_score),
            "deviation_threshold": parameters["deviation_threshold"],
            "is_deviation": is_deviation,
            "evidence_reference": (
                f"trajectory:{track_id}:{points[0]['frame_index']}-{points[-1]['frame_index']}"
            ),
        }
        assignments.append(assignment)
        if is_deviation:
            events.append(_deviation_event(assignment, points))

    status = "ready" if clusters else "insufficient_cluster_support"
    summary = _summary(status, parameters)
    summary.update(
        {
            "input_track_count": len(grouped),
            "eligible_track_count": len(track_ids),
            "static_track_count": static_tracks,
            "cluster_count": len(clusters),
            "clustered_track_count": sum(label != NOISE for label in labels),
            "noise_track_count": sum(label == NOISE for label in labels),
            "deviation_event_count": len(events),
            "normalization_bounds_px": bounds,
        }
    )
    return assignments, prototypes, summary, events


def resample_trajectory(
    points: list[dict[str, Any]], sample_count: int
) -> list[tuple[float, float]]:
    """Resample one ordered trajectory at equal travelled-distance intervals."""
    if not points:
        raise ValueError("At least one trajectory point is required")
    sample_count = max(2, int(sample_count))
    xy = [(float(point["centroid_x"]), float(point["centroid_y"])) for point in points]
    cumulative = [0.0]
    for previous, current in zip(xy, xy[1:], strict=False):
        cumulative.append(cumulative[-1] + hypot(current[0] - previous[0], current[1] - previous[1]))
    total = cumulative[-1]
    if total <= 0:
        return [xy[0]] * sample_count

    sampled: list[tuple[float, float]] = []
    segment = 0
    for index in range(sample_count):
        target = total * index / (sample_count - 1)
        while segment < len(cumulative) - 2 and cumulative[segment + 1] < target:
            segment += 1
        start_distance = cumulative[segment]
        end_distance = cumulative[segment + 1]
        ratio = 0.0 if end_distance <= start_distance else (target - start_distance) / (end_distance - start_distance)
        start, end = xy[segment], xy[segment + 1]
        sampled.append(
            (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            )
        )
    return sampled


def _group_rows(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        try:
            normalized = {
                "track_id": int(row["track_id"]),
                "frame_index": int(row["frame_index"]),
                "timestamp_sec": float(row["timestamp_sec"]),
                "centroid_x": float(row["centroid_x"]),
                "centroid_y": float(row["centroid_y"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        if not all(
            isfinite(normalized[key])
            for key in ("timestamp_sec", "centroid_x", "centroid_y")
        ):
            continue
        grouped[normalized["track_id"]].append(normalized)
    return {
        track_id: sorted(points, key=lambda point: (point["timestamp_sec"], point["frame_index"]))
        for track_id, points in grouped.items()
    }


def _scene_bounds(paths: dict[int, list[tuple[float, float]]]) -> dict[str, float]:
    all_points = [point for path in paths.values() for point in path]
    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
    }


def _normalize_path(
    path: list[tuple[float, float]], bounds: dict[str, float]
) -> list[float]:
    width = max(bounds["max_x"] - bounds["min_x"], 1.0)
    height = max(bounds["max_y"] - bounds["min_y"], 1.0)
    vector: list[float] = []
    for x, y in path:
        vector.extend(((x - bounds["min_x"]) / width, (y - bounds["min_y"]) / height))
    return vector


def _dbscan(vectors: list[list[float]], eps: float, min_samples: int) -> list[int]:
    labels = [UNVISITED] * len(vectors)
    neighborhoods = [
        [candidate for candidate in range(len(vectors)) if _route_distance(vector, vectors[candidate]) <= eps]
        for vector in vectors
    ]
    cluster_id = 0
    for point_index in range(len(vectors)):
        if labels[point_index] != UNVISITED:
            continue
        neighbors = neighborhoods[point_index]
        if len(neighbors) < min_samples:
            labels[point_index] = NOISE
            continue
        labels[point_index] = cluster_id
        queue = deque(neighbors)
        queued = set(neighbors)
        while queue:
            neighbor = queue.popleft()
            if labels[neighbor] == NOISE:
                labels[neighbor] = cluster_id
            if labels[neighbor] != UNVISITED:
                continue
            labels[neighbor] = cluster_id
            if len(neighborhoods[neighbor]) >= min_samples:
                for candidate in neighborhoods[neighbor]:
                    if candidate not in queued:
                        queue.append(candidate)
                        queued.add(candidate)
        cluster_id += 1
    return labels


def _cluster_prototypes(
    track_ids: list[int],
    vectors: dict[int, list[float]],
    labels: list[int],
    bounds: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    width = max(bounds["max_x"] - bounds["min_x"], 1.0)
    height = max(bounds["max_y"] - bounds["min_y"], 1.0)
    for cluster_id in sorted({label for label in labels if label != NOISE}):
        members = [
            vectors[track_id]
            for track_id, label in zip(track_ids, labels, strict=True)
            if label == cluster_id
        ]
        prototype = _mean_vector(members)
        for point_index in range(len(prototype) // 2):
            normalized_x = prototype[point_index * 2]
            normalized_y = prototype[point_index * 2 + 1]
            rows.append(
                {
                    "cluster_id": cluster_id,
                    "member_count": len(members),
                    "point_index": point_index,
                    "normalized_x": _rounded(normalized_x),
                    "normalized_y": _rounded(normalized_y),
                    "centroid_x_px": _rounded(bounds["min_x"] + normalized_x * width),
                    "centroid_y_px": _rounded(bounds["min_y"] + normalized_y * height),
                }
            )
    return rows


def _nearest_prototype(
    vector: list[float],
    prototypes: dict[int, list[float]],
    preferred: int,
) -> tuple[int | None, float | None]:
    if not prototypes:
        return None, None
    if preferred in prototypes:
        return preferred, _route_distance(vector, prototypes[preferred])
    distances = [(_route_distance(vector, prototype), cluster_id) for cluster_id, prototype in prototypes.items()]
    distance, cluster_id = min(distances)
    return cluster_id, distance


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    return [mean(values) for values in zip(*vectors, strict=True)]


def _route_distance(first: list[float], second: list[float]) -> float:
    point_count = max(1, len(first) // 2)
    squared = sum((a - b) ** 2 for a, b in zip(first, second, strict=True))
    return sqrt(squared / point_count)


def _path_length(path: list[tuple[float, float]]) -> float:
    return sum(
        hypot(current[0] - previous[0], current[1] - previous[1])
        for previous, current in zip(path, path[1:], strict=False)
    )


def _deviation_event(
    assignment: dict[str, Any], points: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "event_type": "route_deviation",
        "track_id": assignment["track_id"],
        "start_timestamp_sec": _rounded(points[0]["timestamp_sec"]),
        "end_timestamp_sec": _rounded(points[-1]["timestamp_sec"]),
        "start_frame": points[0]["frame_index"],
        "end_frame": points[-1]["frame_index"],
        "metric_deviation_score": assignment["deviation_score"],
        "threshold_min_deviation_score": assignment["deviation_threshold"],
        "nearest_cluster_id": assignment["nearest_cluster_id"],
        "dbscan_cluster_id": assignment["cluster_id"],
        "dbscan_is_noise": assignment["is_noise"],
        "evidence_reference": assignment["evidence_reference"],
    }


def _summary(status: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": status,
        "method": "distance_resampling_shared_bounds_dbscan",
        "parameters": parameters,
        "safety_rule": "no_deviation_without_supported_route_cluster",
        "input_track_count": 0,
        "eligible_track_count": 0,
        "static_track_count": 0,
        "cluster_count": 0,
        "clustered_track_count": 0,
        "noise_track_count": 0,
        "deviation_event_count": 0,
    }


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)
