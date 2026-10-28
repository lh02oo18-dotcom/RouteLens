from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .geometry import iou


def load_caviar_annotations(
    path: str | Path,
    fps: float = 25.0,
    frame_offset: int = 1,
) -> list[dict[str, Any]]:
    """Load CAVIAR CVML boxes as RouteLens trajectory rows.

    CAVIAR frame numbers are zero based while RouteLens frame numbers are one
    based, hence the default offset of one.
    """
    root = ElementTree.parse(path).getroot()
    rows: list[dict[str, Any]] = []
    for frame in root.findall("frame"):
        frame_index = int(frame.attrib["number"]) + frame_offset
        for object_node in frame.findall("./objectlist/object"):
            box = object_node.find("box")
            if box is None:
                continue
            width = float(box.attrib["w"])
            height = float(box.attrib["h"])
            center_x = float(box.attrib["xc"])
            center_y = float(box.attrib["yc"])
            hypothesis = _best_hypothesis(object_node)
            rows.append(
                {
                    "frame_index": frame_index,
                    "timestamp_sec": round(frame_index / fps, 3),
                    "track_id": int(object_node.attrib["id"]),
                    "centroid_x": center_x,
                    "centroid_y": center_y,
                    "bbox_x1": center_x - width / 2.0,
                    "bbox_y1": center_y - height / 2.0,
                    "bbox_x2": center_x + width / 2.0,
                    "bbox_y2": center_y + height / 2.0,
                    "movement": _text(hypothesis, "movement"),
                    "role": _text(hypothesis, "role"),
                    "context": _text(hypothesis, "context"),
                    "situation": _text(hypothesis, "situation"),
                }
            )
    return sorted(rows, key=lambda row: (row["frame_index"], row["track_id"]))


def browser_reference_events(
    rows: list[dict[str, Any]],
    fps: float = 25.0,
    min_duration_sec: float = 10.0,
) -> list[dict[str, Any]]:
    """Convert contiguous official CAVIAR browser labels into loitering references."""
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("role") == "browser" or row.get("situation") == "browsing":
            grouped[int(row["track_id"])].append(row)

    events: list[dict[str, Any]] = []
    for track_id, track_rows in sorted(grouped.items()):
        track_rows.sort(key=lambda row: int(row["frame_index"]))
        for segment in _contiguous_segments(track_rows):
            first = segment[0]
            last = segment[-1]
            duration_sec = (int(last["frame_index"]) - int(first["frame_index"]) + 1) / fps
            if duration_sec < min_duration_sec:
                continue
            events.append(
                {
                    "event_type": "loitering",
                    "track_id": track_id,
                    "start_frame": int(first["frame_index"]),
                    "end_frame": int(last["frame_index"]),
                    "start_timestamp_sec": round(float(first["timestamp_sec"]), 3),
                    "end_timestamp_sec": round(float(last["timestamp_sec"]), 3),
                    "reference_source": "CAVIAR role=browser/situation=browsing",
                }
            )
    return events


def evaluate_tracking(
    predictions: list[dict[str, Any]],
    references: list[dict[str, Any]],
    iou_threshold: float = 0.5,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate boxes and track continuity on CAVIAR annotated frames.

    Matching is one-to-one greedy matching in descending IoU order. Predictions
    on frames without any CAVIAR annotation are excluded because the reference
    set is not exhaustive on those frames.
    """
    threshold = min(1.0, max(0.0, float(iou_threshold)))
    references_by_frame = _group_by_frame(references)
    predictions_by_frame = _group_by_frame(predictions)
    matches: list[dict[str, Any]] = []
    false_positives = 0
    false_negatives = 0

    for frame_index, frame_references in sorted(references_by_frame.items()):
        frame_predictions = predictions_by_frame.get(frame_index, [])
        frame_matches = _match_frame(frame_predictions, frame_references, threshold)
        matches.extend(frame_matches)
        false_positives += len(frame_predictions) - len(frame_matches)
        false_negatives += len(frame_references) - len(frame_matches)

    true_positives = len(matches)
    precision = _safe_ratio(true_positives, true_positives + false_positives)
    recall = _safe_ratio(true_positives, true_positives + false_negatives)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    mean_iou = _safe_ratio(sum(match["iou"] for match in matches), true_positives)
    centroid_rmse = (
        (sum(match["centroid_error_sq"] for match in matches) / true_positives) ** 0.5
        if true_positives
        else 0.0
    )

    reference_counts = Counter(int(row["track_id"]) for row in references)
    matched_counts = Counter(int(match["reference_track_id"]) for match in matches)
    track_coverages = [
        matched_counts[track_id] / count for track_id, count in reference_counts.items()
    ]
    identity_switches = _identity_switches(matches)
    metrics = {
        "evaluated_frames": len(references_by_frame),
        "reference_boxes": len(references),
        "prediction_boxes": sum(
            len(predictions_by_frame.get(frame_index, [])) for frame_index in references_by_frame
        ),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "mean_iou": round(mean_iou, 4),
        "centroid_rmse_px": round(centroid_rmse, 4),
        "reference_tracks": len(reference_counts),
        "prediction_tracks": len(
            {
                int(row["track_id"])
                for frame_index in references_by_frame
                for row in predictions_by_frame.get(frame_index, [])
            }
        ),
        "macro_track_coverage": round(
            _safe_ratio(sum(track_coverages), len(track_coverages)), 4
        ),
        "identity_switches": identity_switches,
        "identity_switches_per_1000_reference_boxes": round(
            _safe_ratio(identity_switches * 1000, len(references)), 4
        ),
        "iou_threshold": threshold,
        "matching_method": "greedy_descending_iou",
    }
    return metrics, matches


def prediction_to_reference_ids(matches: list[dict[str, Any]]) -> dict[int, int]:
    """Map each predicted track to the reference identity it overlaps most often."""
    counts: dict[int, Counter[int]] = defaultdict(Counter)
    for match in matches:
        counts[int(match["prediction_track_id"])][int(match["reference_track_id"])] += 1
    mapping: dict[int, int] = {}
    for prediction_id, reference_counts in counts.items():
        mapping[prediction_id] = min(
            reference_counts,
            key=lambda reference_id: (-reference_counts[reference_id], reference_id),
        )
    return mapping


def remap_event_track_ids(
    events: list[dict[str, Any]],
    mapping: dict[int, int],
) -> list[dict[str, Any]]:
    remapped: list[dict[str, Any]] = []
    for event in events:
        prediction_id = int(event.get("track_id", -1))
        if prediction_id not in mapping:
            continue
        row = dict(event)
        row["prediction_track_id"] = prediction_id
        row["track_id"] = mapping[prediction_id]
        remapped.append(row)
    return remapped


def _best_hypothesis(object_node: ElementTree.Element) -> ElementTree.Element | None:
    hypotheses = object_node.findall("./hypothesislist/hypothesis")
    if not hypotheses:
        return None
    return max(hypotheses, key=lambda node: float(node.attrib.get("evaluation", 0.0)))


def _text(node: ElementTree.Element | None, name: str) -> str | None:
    if node is None:
        return None
    child = node.find(name)
    return child.text.strip() if child is not None and child.text else None


def _contiguous_segments(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in rows:
        if current and int(row["frame_index"]) > int(current[-1]["frame_index"]) + 1:
            segments.append(current)
            current = []
        current.append(row)
    if current:
        segments.append(current)
    return segments


def _group_by_frame(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["frame_index"])].append(row)
    return grouped


def _match_frame(
    predictions: list[dict[str, Any]],
    references: list[dict[str, Any]],
    threshold: float,
) -> list[dict[str, Any]]:
    candidates: list[tuple[float, int, int]] = []
    for prediction_index, prediction in enumerate(predictions):
        for reference_index, reference in enumerate(references):
            overlap = iou(_bbox(prediction), _bbox(reference))
            if overlap >= threshold:
                candidates.append((overlap, prediction_index, reference_index))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))

    matched_predictions: set[int] = set()
    matched_references: set[int] = set()
    matches: list[dict[str, Any]] = []
    for overlap, prediction_index, reference_index in candidates:
        if prediction_index in matched_predictions or reference_index in matched_references:
            continue
        prediction = predictions[prediction_index]
        reference = references[reference_index]
        dx = float(prediction["centroid_x"]) - float(reference["centroid_x"])
        dy = float(prediction["centroid_y"]) - float(reference["centroid_y"])
        matches.append(
            {
                "frame_index": int(reference["frame_index"]),
                "prediction_track_id": int(prediction["track_id"]),
                "reference_track_id": int(reference["track_id"]),
                "iou": overlap,
                "centroid_error_sq": dx * dx + dy * dy,
            }
        )
        matched_predictions.add(prediction_index)
        matched_references.add(reference_index)
    return matches


def _bbox(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(round(float(row["bbox_x1"]))),
        int(round(float(row["bbox_y1"]))),
        int(round(float(row["bbox_x2"]))),
        int(round(float(row["bbox_y2"]))),
    )


def _identity_switches(matches: list[dict[str, Any]]) -> int:
    previous_prediction: dict[int, int] = {}
    switches = 0
    for match in sorted(
        matches,
        key=lambda item: (item["frame_index"], item["reference_track_id"]),
    ):
        reference_id = int(match["reference_track_id"])
        prediction_id = int(match["prediction_track_id"])
        if reference_id in previous_prediction and previous_prediction[reference_id] != prediction_id:
            switches += 1
        previous_prediction[reference_id] = prediction_id
    return switches


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
