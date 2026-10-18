from __future__ import annotations

from typing import Any


def evaluate_events(
    predictions: list[dict[str, Any]],
    references: list[dict[str, Any]],
    min_temporal_iou: float = 0.1,
) -> dict[str, Any]:
    """Compute one-to-one event precision, recall and F1.

    A match requires the same event type and track ID plus sufficient temporal
    overlap.  Invalid rows remain unmatched, so they cannot silently improve a
    score.
    """
    threshold = min(1.0, max(0.0, float(min_temporal_iou)))
    unmatched_references = set(range(len(references)))
    matches: list[dict[str, Any]] = []
    false_positive_indices: list[int] = []

    for prediction_index, prediction in enumerate(predictions):
        candidates: list[tuple[float, int]] = []
        for reference_index in unmatched_references:
            reference = references[reference_index]
            if not _same_identity(prediction, reference):
                continue
            overlap = _temporal_iou(prediction, reference)
            if overlap is not None and overlap >= threshold:
                candidates.append((overlap, reference_index))
        if not candidates:
            false_positive_indices.append(prediction_index)
            continue
        overlap, reference_index = max(candidates, key=lambda item: (item[0], -item[1]))
        unmatched_references.remove(reference_index)
        matches.append(
            {
                "prediction_index": prediction_index,
                "reference_index": reference_index,
                "temporal_iou": round(overlap, 4),
            }
        )

    true_positives = len(matches)
    false_positives = len(false_positive_indices)
    false_negatives = len(unmatched_references)
    precision = _safe_ratio(true_positives, true_positives + false_positives)
    recall = _safe_ratio(true_positives, true_positives + false_negatives)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "min_temporal_iou": threshold,
        "matches": matches,
        "false_positive_indices": false_positive_indices,
        "false_negative_indices": sorted(unmatched_references),
    }


def _same_identity(first: dict[str, Any], second: dict[str, Any]) -> bool:
    try:
        return (
            str(first["event_type"]) == str(second["event_type"])
            and int(first["track_id"]) == int(second["track_id"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def _temporal_iou(first: dict[str, Any], second: dict[str, Any]) -> float | None:
    try:
        first_start = float(first["start_timestamp_sec"])
        first_end = float(first["end_timestamp_sec"])
        second_start = float(second["start_timestamp_sec"])
        second_end = float(second["end_timestamp_sec"])
    except (KeyError, TypeError, ValueError):
        return None
    if first_end < first_start or second_end < second_start:
        return None
    intersection = max(0.0, min(first_end, second_end) - max(first_start, second_start))
    union = max(first_end, second_end) - min(first_start, second_start)
    if union == 0:
        return 1.0 if first_start == second_start else 0.0
    return intersection / union


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
