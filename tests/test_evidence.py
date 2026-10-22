import cv2
import numpy as np

from people_counter.evidence import generate_evidence_cards, render_evidence_card


def _event():
    return {
        "event_type": "reverse_direction",
        "track_id": 7,
        "start_timestamp_sec": 1.0,
        "end_timestamp_sec": 3.0,
        "start_frame": 10,
        "end_frame": 30,
        "metric_duration_sec": 2.0,
        "metric_distance_px": 60.0,
        "threshold_min_duration_sec": 1.0,
        "evidence_reference": "trajectory:7:10-30",
    }


def _trajectory():
    return [
        {
            "track_id": 7,
            "frame_index": frame,
            "timestamp_sec": frame / 10,
            "centroid_x": 50 + frame * 2,
            "centroid_y": 80,
            "bbox_x1": 40 + frame * 2,
            "bbox_y1": 50,
            "bbox_x2": 70 + frame * 2,
            "bbox_y2": 110,
        }
        for frame in (10, 20, 30)
    ]


def test_render_evidence_card_has_stable_canvas():
    frame = np.full((360, 640, 3), 180, dtype=np.uint8)

    card = render_evidence_card(_event(), _trajectory(), frame=frame)

    assert card.shape == (720, 1280, 3)
    assert int(card[640, 40].mean()) < 100


def test_generate_evidence_cards_uses_explicit_fallback(tmp_path):
    events = [_event()]

    cards, summary = generate_evidence_cards(
        source="not-a-local-video",
        events=events,
        trajectories=_trajectory(),
        output_dir=tmp_path,
    )

    image_path = tmp_path / cards[0]["image_path"]
    assert image_path.exists()
    assert cv2.imread(str(image_path)).shape == (720, 1280, 3)
    assert cards[0]["frame_source"] == "generated_canvas"
    assert summary["source_frame_available"] is False
    assert events[0]["evidence_card"].endswith(".jpg")


def test_no_events_produces_empty_manifest(tmp_path):
    cards_dir = tmp_path / "evidence_cards"
    cards_dir.mkdir()
    (cards_dir / "stale.jpg").write_bytes(b"stale")

    cards, summary = generate_evidence_cards(
        source=0,
        events=[],
        trajectories=[],
        output_dir=tmp_path,
    )

    assert cards == []
    assert summary["status"] == "no_anomaly_events"
    assert not (cards_dir / "stale.jpg").exists()
