from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

EVENT_LABELS = {
    "reverse_direction": "Reverse direction",
    "loitering": "Loitering",
    "route_deviation": "Route deviation",
}


def generate_evidence_cards(
    source: object,
    events: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    output_dir: str | Path,
    *,
    privacy_blur: bool = False,
    max_cards: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Render deterministic anomaly evidence cards and return a manifest.

    A seekable local video supplies the keyframe. Camera and network inputs fall
    back to a neutral canvas, while retaining the trajectory, metrics and source
    status so the output never implies that an unavailable frame was captured.
    """
    output_path = Path(output_dir)
    cards_dir = output_path / "evidence_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    for stale_card in cards_dir.glob("*.jpg"):
        stale_card.unlink()

    grouped = _group_trajectories(trajectories)
    local_source = _local_video_path(source)
    capture = cv2.VideoCapture(str(local_source)) if local_source is not None else None
    capture_ready = bool(capture is not None and capture.isOpened())

    cards: list[dict[str, Any]] = []
    try:
        for index, event in enumerate(events[: max(0, int(max_cards))], start=1):
            track_id = int(event.get("track_id", -1))
            track_rows = grouped.get(track_id, [])
            keyframe = _event_keyframe(event)
            frame = _read_frame(capture, keyframe) if capture_ready else None
            frame_source = "source_video" if frame is not None else "generated_canvas"
            canvas = render_evidence_card(
                event,
                track_rows,
                frame=frame,
                privacy_blur=privacy_blur,
            )
            card_id = f"E{index:03d}"
            event_type = str(event.get("event_type", "anomaly"))
            filename = f"{card_id}_{event_type}_track_{track_id}.jpg"
            image_path = cards_dir / filename
            if not cv2.imwrite(str(image_path), canvas):
                raise RuntimeError(f"Could not write evidence card: {image_path}")

            relative_path = image_path.relative_to(output_path).as_posix()
            event["evidence_card"] = relative_path
            cards.append(
                _manifest_row(
                    card_id,
                    event,
                    relative_path,
                    keyframe,
                    frame_source,
                    track_rows,
                )
            )
    finally:
        if capture is not None:
            capture.release()

    status = "ready" if cards else "no_anomaly_events"
    if events and not cards:
        status = "card_limit_reached"
    summary = {
        "status": status,
        "card_count": len(cards),
        "requested_event_count": len(events),
        "max_cards": max(0, int(max_cards)),
        "source_frame_available": capture_ready,
        "fallback_rule": "generated_canvas_when_source_frame_unavailable",
        "privacy_blur": bool(privacy_blur),
    }
    return cards, summary


def render_evidence_card(
    event: dict[str, Any],
    trajectory_rows: list[dict[str, Any]],
    *,
    frame: np.ndarray | None = None,
    privacy_blur: bool = False,
) -> np.ndarray:
    """Create one 1280x720 evidence card from an event and its trajectory."""
    if frame is not None and frame.size and privacy_blur:
        frame = cv2.GaussianBlur(frame, (31, 31), 0)
    scale = (
        (1280.0 / frame.shape[1], 720.0 / frame.shape[0])
        if frame is not None and frame.size
        else (1.0, 1.0)
    )
    canvas = _base_canvas(frame)
    keyframe = _event_keyframe(event)
    visible_rows = [
        row for row in trajectory_rows if int(row.get("frame_index", 0)) <= keyframe
    ] or trajectory_rows
    target_row = _nearest_row(trajectory_rows, keyframe)

    _draw_trajectory(canvas, visible_rows, scale)
    if target_row is not None:
        _draw_bbox(canvas, target_row, scale)

    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 520), (1280, 720), (18, 18, 18), -1)
    cv2.addWeighted(overlay, 0.9, canvas, 0.1, 0, canvas)

    event_type = str(event.get("event_type", "anomaly"))
    title = EVENT_LABELS.get(event_type, event_type.replace("_", " ").title())
    cv2.putText(canvas, title, (34, 568), cv2.FONT_HERSHEY_SIMPLEX, 1.15, (255, 255, 255), 2)
    cv2.putText(
        canvas,
        f"Track {event.get('track_id', '?')}  |  {_time_range(event)}  |  frame {keyframe}",
        (34, 606),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (205, 205, 205),
        2,
    )
    reason = _reason_text(event)
    cv2.putText(canvas, reason[:92], (34, 646), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (90, 220, 255), 2)
    cv2.putText(
        canvas,
        f"Evidence: {event.get('evidence_reference', 'trajectory unavailable')}",
        (34, 684),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (190, 190, 190),
        1,
    )
    cv2.putText(canvas, "RouteLens v1.0.0", (1050, 690), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (190, 190, 190), 1)
    return canvas


def _base_canvas(frame: np.ndarray | None) -> np.ndarray:
    if frame is None or frame.size == 0:
        canvas = np.full((720, 1280, 3), 235, dtype=np.uint8)
        cv2.putText(canvas, "Source frame unavailable", (390, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (80, 80, 80), 2)
        cv2.putText(canvas, "Trajectory evidence remains reproducible below.", (330, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (110, 110, 110), 2)
        return canvas
    return cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)


def _draw_trajectory(
    canvas: np.ndarray,
    rows: list[dict[str, Any]],
    scale: tuple[float, float],
) -> None:
    if len(rows) < 2:
        return
    points = np.array(
        [
            [
                int(float(row["centroid_x"]) * scale[0]),
                int(float(row["centroid_y"]) * scale[1]),
            ]
            for row in rows
        ],
        dtype=np.int32,
    )
    cv2.polylines(canvas, [points], False, (0, 210, 255), 4, cv2.LINE_AA)
    cv2.circle(canvas, tuple(points[-1]), 8, (0, 70, 255), -1, cv2.LINE_AA)


def _draw_bbox(
    canvas: np.ndarray,
    row: dict[str, Any],
    scale: tuple[float, float],
) -> None:
    keys = ("bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2")
    if not all(key in row for key in keys):
        return
    x1 = int(float(row["bbox_x1"]) * scale[0])
    y1 = int(float(row["bbox_y1"]) * scale[1])
    x2 = int(float(row["bbox_x2"]) * scale[0])
    y2 = int(float(row["bbox_y2"]) * scale[1])
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 70, 255), 3)


def _manifest_row(
    card_id: str,
    event: dict[str, Any],
    image_path: str,
    keyframe: int,
    frame_source: str,
    trajectory_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    row = {
        "card_id": card_id,
        "event_type": event.get("event_type"),
        "track_id": event.get("track_id"),
        "start_timestamp_sec": event.get("start_timestamp_sec"),
        "end_timestamp_sec": event.get("end_timestamp_sec"),
        "start_frame": event.get("start_frame"),
        "end_frame": event.get("end_frame"),
        "keyframe": keyframe,
        "frame_source": frame_source,
        "trajectory_point_count": len(trajectory_rows),
        "reason": _reason_text(event),
        "image_path": image_path,
        "trajectory_reference": event.get("evidence_reference"),
    }
    for key, value in event.items():
        if key.startswith(("metric_", "threshold_")):
            row[key] = value
    return row


def _reason_text(event: dict[str, Any]) -> str:
    metrics = [f"{key.removeprefix('metric_')}={value}" for key, value in event.items() if key.startswith("metric_")]
    thresholds = [f"{key.removeprefix('threshold_')}={value}" for key, value in event.items() if key.startswith("threshold_")]
    parts = metrics[:2] + thresholds[:2]
    return " | ".join(parts) if parts else "Event rule matched; inspect the trajectory reference."


def _event_keyframe(event: dict[str, Any]) -> int:
    start = int(event.get("start_frame", event.get("end_frame", 1)))
    end = int(event.get("end_frame", start))
    return max(1, round((start + end) / 2))


def _time_range(event: dict[str, Any]) -> str:
    start = float(event.get("start_timestamp_sec", 0.0))
    end = float(event.get("end_timestamp_sec", start))
    return f"{start:.2f}-{end:.2f} s"


def _group_trajectories(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        try:
            grouped[int(row["track_id"])].append(row)
        except (KeyError, TypeError, ValueError):
            continue
    return {
        track_id: sorted(items, key=lambda item: int(item.get("frame_index", 0)))
        for track_id, items in grouped.items()
    }


def _nearest_row(rows: list[dict[str, Any]], frame_index: int) -> dict[str, Any] | None:
    if not rows:
        return None
    return min(rows, key=lambda row: abs(int(row.get("frame_index", 0)) - frame_index))


def _local_video_path(source: object) -> Path | None:
    if not isinstance(source, (str, Path)):
        return None
    candidate = Path(source)
    return candidate if candidate.is_file() else None


def _read_frame(capture: cv2.VideoCapture | None, frame_index: int) -> np.ndarray | None:
    if capture is None:
        return None
    capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index - 1))
    ok, frame = capture.read()
    return frame if ok else None
