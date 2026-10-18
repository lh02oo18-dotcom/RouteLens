from __future__ import annotations

import argparse
import json
from pathlib import Path

from people_counter.evaluation import evaluate_events


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RouteLens event JSON files.")
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--references", required=True, type=Path)
    parser.add_argument("--min-temporal-iou", type=float, default=0.1)
    args = parser.parse_args()

    predictions = _read_events(args.predictions)
    references = _read_events(args.references)
    metrics = evaluate_events(predictions, references, args.min_temporal_iou)
    print(json.dumps(metrics, indent=2))
    return 0


def _read_events(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("events")
    if not isinstance(data, list):
        raise ValueError(f"Expected an event list in {path}")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
