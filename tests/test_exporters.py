import json

from people_counter.config_runtime import OutputConfig
from people_counter.exporters import SessionExporter


def test_exporter_writes_route_lens_feature_and_event_artifacts(tmp_path):
    exporter = SessionExporter(OutputConfig(directory=str(tmp_path)))

    paths = exporter.export(
        frame_metrics=[],
        events=[],
        trajectories=[],
        trajectory_features=[{"track_id": 1, "duration_sec": 2.0}],
        route_assignments=[{"track_id": 1, "cluster_id": 0}],
        route_prototypes=[{"cluster_id": 0, "point_index": 0}],
        route_summary={"status": "ready", "cluster_count": 1},
        anomaly_events=[{"event_type": "reverse_direction", "track_id": 1}],
        evidence_cards=[{"card_id": "E001", "image_path": "evidence_cards/E001.jpg"}],
        evidence_summary={"status": "ready", "card_count": 1},
        summary={"anomaly_events": 1},
    )

    assert "track_id" in (tmp_path / "trajectory_features.csv").read_text(encoding="utf-8")
    assert "reverse_direction" in (tmp_path / "anomaly_events.csv").read_text(
        encoding="utf-8"
    )
    assert json.loads((tmp_path / "anomaly_events.json").read_text(encoding="utf-8")) == [
        {"event_type": "reverse_direction", "track_id": 1}
    ]
    assert paths["anomaly_events_json"].endswith("anomaly_events.json")
    assert "cluster_id" in (tmp_path / "route_assignments.csv").read_text(
        encoding="utf-8"
    )
    assert json.loads((tmp_path / "route_summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "ready"
    manifest = json.loads((tmp_path / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert manifest["summary"]["card_count"] == 1
    assert manifest["cards"][0]["card_id"] == "E001"
