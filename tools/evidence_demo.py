from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from people_counter.evidence import generate_evidence_cards


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic RouteLens evidence-card demo.")
    parser.add_argument("--output-dir", default="outputs/evidence_demo")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory = [
        {
            "track_id": 1,
            "frame_index": index + 1,
            "timestamp_sec": index * 0.5,
            "centroid_x": 720 - index * 48,
            "centroid_y": 220 + (index % 2) * 12,
            "bbox_x1": 690 - index * 48,
            "bbox_y1": 155,
            "bbox_x2": 750 - index * 48,
            "bbox_y2": 285,
        }
        for index in range(7)
    ]
    events = [
        {
            "event_type": "reverse_direction",
            "track_id": 1,
            "start_timestamp_sec": 0.0,
            "end_timestamp_sec": 3.0,
            "start_frame": 1,
            "end_frame": 7,
            "metric_duration_sec": 3.0,
            "metric_distance_px": 288.0,
            "metric_mean_alignment": -1.0,
            "threshold_max_alignment": -0.5,
            "threshold_min_duration_sec": 1.0,
            "threshold_min_distance_px": 40.0,
            "evidence_reference": "trajectory:1:1-7",
        }
    ]
    cards, summary = generate_evidence_cards(
        source="synthetic-demo-no-source-frame",
        events=events,
        trajectories=trajectory,
        output_dir=output_dir,
    )
    manifest = {
        "metadata": {
            "synthetic": True,
            "purpose": "pipeline_and_presentation_fallback_only",
            "real_world_accuracy_claim": False,
        },
        "summary": summary,
        "cards": cards,
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (output_dir / "evidence_cards.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=sorted(cards[0]))
        writer.writeheader()
        writer.writerows(cards)

    print(json.dumps({"output_dir": str(output_dir), "cards": len(cards)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
