from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from people_counter.config_runtime import AnalyticsConfig
from people_counter.evaluation import evaluate_events
from people_counter.route_mining import mine_routes


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic RouteLens parameter sweep.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/route_mining_demo"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows, references = _synthetic_dataset()
    results = []
    for eps in (0.03, 0.05, 0.08, 0.12):
        for threshold in (0.2, 0.5, 0.8):
            config = AnalyticsConfig(
                route_dbscan_eps=eps,
                route_dbscan_min_samples=3,
                route_deviation_threshold=threshold,
            )
            _, _, summary, events = mine_routes(rows, config)
            metrics = evaluate_events(events, references)
            results.append(
                {
                    "dbscan_eps": eps,
                    "deviation_threshold": threshold,
                    "cluster_count": summary["cluster_count"],
                    "noise_track_count": summary["noise_track_count"],
                    "predicted_events": len(events),
                    "true_positives": metrics["true_positives"],
                    "false_positives": metrics["false_positives"],
                    "false_negatives": metrics["false_negatives"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                }
            )

    csv_path = args.output_dir / "parameter_sweep.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    metadata = {
        "data_kind": "synthetic_demonstration_only",
        "claim_limit": "This output verifies the pipeline; it is not real-world accuracy evidence.",
        "track_count": len({row["track_id"] for row in rows}),
        "reference_event_count": len(references),
        "results_file": str(csv_path),
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))
    return 0


def _synthetic_dataset() -> tuple[list[dict], list[dict]]:
    rows = []
    for track_id, y in ((1, 0.0), (2, 1.0), (3, -1.0), (4, 2.0), (5, -2.0), (8, 20.0), (99, 80.0)):
        for index in range(5):
            rows.append(
                {
                    "track_id": track_id,
                    "frame_index": index + 1,
                    "timestamp_sec": float(index),
                    "centroid_x": index * 10.0,
                    "centroid_y": y,
                }
            )
    references = [
        {
            "event_type": "route_deviation",
            "track_id": 99,
            "start_timestamp_sec": 0.0,
            "end_timestamp_sec": 4.0,
        }
    ]
    return rows, references


if __name__ == "__main__":
    raise SystemExit(main())
