from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from people_counter.caviar import (
    browser_reference_events,
    evaluate_tracking,
    load_caviar_annotations,
    prediction_to_reference_ids,
    remap_event_track_ids,
)
from people_counter.config_runtime import load_config
from people_counter.counter import VideoCounter
from people_counter.evaluation import evaluate_events


def main() -> int:
    args = parse_args()
    manifest_rows = _read_manifest(args.manifest)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    result_rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []

    for manifest_row in manifest_rows:
        sequence = manifest_row["sequence"]
        if args.sequences and sequence not in args.sequences:
            continue
        references = load_caviar_annotations(
            manifest_row["annotation_path"],
            fps=float(manifest_row["fps"]),
        )
        reference_events = browser_reference_events(
            references,
            fps=float(manifest_row["fps"]),
            min_duration_sec=args.min_browser_duration,
        )
        for tracker in args.trackers:
            config = load_config(args.config)
            config.detector.model_path = args.model
            if args.confidence is not None:
                config.detector.confidence = args.confidence
            if args.image_size is not None:
                config.detector.image_size = args.image_size
            if args.device is not None:
                config.detector.device = args.device
            config.tracker.backend = tracker
            result = VideoCounter(manifest_row["video_path"], config=config).run(
                visualize=False,
                export=False,
            )
            tracking_metrics, matches = evaluate_tracking(
                result.trajectories,
                references,
                iou_threshold=args.iou_threshold,
            )
            mapping = prediction_to_reference_ids(matches)
            predicted_loitering = [
                event for event in result.anomaly_events if event["event_type"] == "loitering"
            ]
            remapped_events = remap_event_track_ids(predicted_loitering, mapping)
            event_metrics = evaluate_events(
                remapped_events,
                reference_events,
                min_temporal_iou=args.min_temporal_iou,
            )
            row = {
                "sequence": sequence,
                "tracker": tracker,
                "model": args.model,
                "processed_frames": result.summary["total_frames"],
                "processing_fps": result.summary["average_fps"],
                **tracking_metrics,
                "reference_loitering_events": len(reference_events),
                "predicted_loitering_events": len(predicted_loitering),
                "mapped_loitering_events": len(remapped_events),
                "event_true_positives": event_metrics["true_positives"],
                "event_false_positives": event_metrics["false_positives"],
                "event_false_negatives": event_metrics["false_negatives"],
                "event_precision": event_metrics["precision"],
                "event_recall": event_metrics["recall"],
                "event_f1": event_metrics["f1"],
            }
            result_rows.append(row)
            details.append(
                {
                    "sequence": sequence,
                    "tracker": tracker,
                    "summary": result.summary,
                    "tracking_metrics": tracking_metrics,
                    "event_metrics": event_metrics,
                    "reference_events": reference_events,
                    "predicted_events_remapped": remapped_events,
                    "prediction_to_reference_ids": mapping,
                }
            )
            print(
                f"{sequence}/{tracker}: box F1={tracking_metrics['f1']:.4f}, "
                f"event F1={event_metrics['f1']:.4f}, "
                f"FPS={result.summary['average_fps']:.2f}"
            )

    aggregate_rows = _aggregate(result_rows)
    _write_csv(output_dir / "per_sequence_metrics.csv", result_rows)
    _write_csv(output_dir / "aggregate_metrics.csv", aggregate_rows)
    _write_json(output_dir / "experiment_details.json", details)
    _write_json(
        output_dir / "run_metadata.json",
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "command_parameters": {
                key: str(value) if isinstance(value, Path) else value
                for key, value in vars(args).items()
            },
            "environment": _environment(),
            "model_sha256": _sha256(Path(args.model)),
            "manifest_sha256": _sha256(args.manifest),
        },
    )
    print(f"Wrote real-data experiment results to {output_dir}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RouteLens CAVIAR real-data experiment.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/research/caviar-pilot-manifest.csv"),
    )
    parser.add_argument("--config", type=Path, default=Path("config/caviar.yaml"))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--confidence", type=float)
    parser.add_argument("--image-size", type=int)
    parser.add_argument("--trackers", nargs="+", default=["bytetrack", "botsort"])
    parser.add_argument("--sequences", nargs="+")
    parser.add_argument("--device", default=None)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--min-temporal-iou", type=float, default=0.1)
    parser.add_argument("--min-browser-duration", type=float, default=10.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/caviar-v1.1"),
    )
    return parser.parse_args()


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for tracker in sorted({str(row["tracker"]) for row in rows}):
        selected = [row for row in rows if row["tracker"] == tracker]
        true_positives = sum(int(row["true_positives"]) for row in selected)
        false_positives = sum(int(row["false_positives"]) for row in selected)
        false_negatives = sum(int(row["false_negatives"]) for row in selected)
        precision = _safe_ratio(true_positives, true_positives + false_positives)
        recall = _safe_ratio(true_positives, true_positives + false_negatives)
        f1 = _safe_ratio(2 * precision * recall, precision + recall)
        event_tp = sum(int(row["event_true_positives"]) for row in selected)
        event_fp = sum(int(row["event_false_positives"]) for row in selected)
        event_fn = sum(int(row["event_false_negatives"]) for row in selected)
        event_precision = _safe_ratio(event_tp, event_tp + event_fp)
        event_recall = _safe_ratio(event_tp, event_tp + event_fn)
        event_f1 = _safe_ratio(
            2 * event_precision * event_recall,
            event_precision + event_recall,
        )
        reference_boxes = sum(int(row["reference_boxes"]) for row in selected)
        total_frames = sum(int(row["processed_frames"]) for row in selected)
        elapsed = sum(
            int(row["processed_frames"]) / float(row["processing_fps"])
            for row in selected
            if float(row["processing_fps"]) > 0
        )
        aggregates.append(
            {
                "tracker": tracker,
                "model": selected[0]["model"],
                "sequence_count": len(selected),
                "processed_frames": total_frames,
                "reference_boxes": reference_boxes,
                "prediction_boxes": sum(int(row["prediction_boxes"]) for row in selected),
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "mean_iou": _weighted_mean(selected, "mean_iou", "true_positives"),
                "centroid_rmse_px": _pooled_rmse(selected),
                "macro_track_coverage": round(
                    sum(float(row["macro_track_coverage"]) for row in selected) / len(selected),
                    4,
                ),
                "identity_switches": sum(int(row["identity_switches"]) for row in selected),
                "identity_switches_per_1000_reference_boxes": round(
                    _safe_ratio(
                        sum(int(row["identity_switches"]) for row in selected) * 1000,
                        reference_boxes,
                    ),
                    4,
                ),
                "processing_fps": round(_safe_ratio(total_frames, elapsed), 2),
                "reference_loitering_events": sum(
                    int(row["reference_loitering_events"]) for row in selected
                ),
                "predicted_loitering_events": sum(
                    int(row["predicted_loitering_events"]) for row in selected
                ),
                "event_true_positives": event_tp,
                "event_false_positives": event_fp,
                "event_false_negatives": event_fn,
                "event_precision": round(event_precision, 4),
                "event_recall": round(event_recall, 4),
                "event_f1": round(event_f1, 4),
            }
        )
    return aggregates


def _weighted_mean(rows: list[dict[str, Any]], value: str, weight: str) -> float:
    total_weight = sum(float(row[weight]) for row in rows)
    return round(
        _safe_ratio(
            sum(float(row[value]) * float(row[weight]) for row in rows),
            total_weight,
        ),
        4,
    )


def _pooled_rmse(rows: list[dict[str, Any]]) -> float:
    total_matches = sum(int(row["true_positives"]) for row in rows)
    squared_error = sum(
        float(row["centroid_rmse_px"]) ** 2 * int(row["true_positives"]) for row in rows
    )
    return round((_safe_ratio(squared_error, total_matches)) ** 0.5, 4)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _environment() -> dict[str, Any]:
    packages = {}
    for name in ("numpy", "opencv-contrib-python", "torch", "ultralytics", "lap"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
