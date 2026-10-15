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
        anomaly_events=[{"event_type": "reverse_direction", "track_id": 1}],
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
