from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from people_counter.caviar import evaluate_tracking, load_caviar_annotations
from people_counter.config_runtime import load_config
from people_counter.counter import VideoCounter


def main() -> int:
    args = parse_args()
    manifest = _manifest_row(args.manifest, args.sequence)
    references = load_caviar_annotations(
        manifest["annotation_path"],
        fps=float(manifest["fps"]),
    )
    rows: list[dict[str, Any]] = []
    for image_size in args.image_sizes:
        for confidence in args.confidences:
            config = load_config(args.config)
            config.detector.model_path = args.model
            config.detector.device = args.device
            config.detector.image_size = image_size
            config.detector.confidence = confidence
            config.tracker.backend = args.tracker
            result = VideoCounter(manifest["video_path"], config=config).run(
                visualize=False,
                export=False,
            )
            metrics, _ = evaluate_tracking(
                result.trajectories,
                references,
                iou_threshold=args.iou_threshold,
            )
            row = {
                "sequence": args.sequence,
                "tracker": args.tracker,
                "model": args.model,
                "image_size": image_size,
                "confidence": confidence,
                "processing_fps": result.summary["average_fps"],
                **metrics,
            }
            rows.append(row)
            print(
                f"size={image_size}, conf={confidence:.2f}: "
                f"P={metrics['precision']:.4f}, R={metrics['recall']:.4f}, "
                f"F1={metrics['f1']:.4f}, FPS={result.summary['average_fps']:.2f}"
            )

    best = max(
        rows,
        key=lambda row: (
            float(row["f1"]),
            float(row["precision"]),
            -int(row["image_size"]),
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    choice_path = args.output.with_name("calibration_choice.json")
    choice_path.write_text(json.dumps(best, indent=2), encoding="utf-8")
    print(
        f"Selected image_size={best['image_size']}, confidence={best['confidence']} "
        f"from calibration F1={best['f1']}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate RouteLens on one CAVIAR sequence.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/research/caviar-pilot-manifest.csv"),
    )
    parser.add_argument("--config", type=Path, default=Path("config/caviar.yaml"))
    parser.add_argument("--sequence", default="Walk1")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--tracker", default="bytetrack")
    parser.add_argument("--device", default="0")
    parser.add_argument("--image-sizes", nargs="+", type=int, default=[640, 960])
    parser.add_argument(
        "--confidences",
        nargs="+",
        type=float,
        default=[0.05, 0.10, 0.15, 0.25],
    )
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/caviar-v1.1/calibration_metrics.csv"),
    )
    return parser.parse_args()


def _manifest_row(path: Path, sequence: str) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["sequence"] == sequence:
                return row
    raise ValueError(f"Sequence {sequence!r} was not found in {path}")


if __name__ == "__main__":
    raise SystemExit(main())
