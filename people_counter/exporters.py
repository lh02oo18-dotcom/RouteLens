from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .config_runtime import OutputConfig


class SessionExporter:
    def __init__(self, config: OutputConfig):
        self.config = config
        self.output_dir = Path(config.directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        frame_metrics: list[dict[str, Any]],
        events: list[dict[str, Any]],
        trajectories: list[dict[str, Any]],
        trajectory_features: list[dict[str, Any]],
        route_assignments: list[dict[str, Any]],
        route_prototypes: list[dict[str, Any]],
        route_summary: dict[str, Any],
        anomaly_events: list[dict[str, Any]],
        evidence_cards: list[dict[str, Any]],
        evidence_summary: dict[str, Any],
        summary: dict[str, Any],
    ) -> dict[str, str]:
        paths: dict[str, str] = {}
        if self.config.save_frame_metrics_csv:
            paths["frame_metrics_csv"] = str(
                self._write_csv("frame_metrics.csv", frame_metrics)
            )
        if self.config.save_events_csv:
            paths["events_csv"] = str(self._write_csv("crossing_events.csv", events))
        if self.config.save_trajectories_csv:
            paths["trajectories_csv"] = str(
                self._write_csv("trajectories.csv", trajectories)
            )
        if self.config.save_trajectory_features_csv:
            paths["trajectory_features_csv"] = str(
                self._write_csv("trajectory_features.csv", trajectory_features)
            )
        if self.config.save_route_assignments_csv:
            paths["route_assignments_csv"] = str(
                self._write_csv("route_assignments.csv", route_assignments)
            )
        if self.config.save_route_prototypes_csv:
            paths["route_prototypes_csv"] = str(
                self._write_csv("route_prototypes.csv", route_prototypes)
            )
        if self.config.save_route_summary_json:
            paths["route_summary_json"] = str(
                self._write_json("route_summary.json", route_summary)
            )
        if self.config.save_anomaly_events_csv:
            paths["anomaly_events_csv"] = str(
                self._write_csv("anomaly_events.csv", anomaly_events)
            )
        if self.config.save_anomaly_events_json:
            paths["anomaly_events_json"] = str(
                self._write_json("anomaly_events.json", anomaly_events)
            )
        if self.config.save_evidence_cards_csv:
            paths["evidence_cards_csv"] = str(
                self._write_csv("evidence_cards.csv", evidence_cards)
            )
        if self.config.save_evidence_manifest_json:
            paths["evidence_manifest_json"] = str(
                self._write_json(
                    "evidence_manifest.json",
                    {"summary": evidence_summary, "cards": evidence_cards},
                )
            )
        if self.config.save_summary_json:
            paths["summary_json"] = str(self._write_json("summary.json", summary))
        return paths

    def _write_csv(self, filename: str, rows: list[dict[str, Any]]) -> Path:
        path = self.output_dir / filename
        if not rows:
            path.write_text("", encoding="utf-8")
            return path

        fieldnames = sorted({key for row in rows for key in row.keys()})
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _write_json(self, filename: str, data: Any) -> Path:
        path = self.output_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
