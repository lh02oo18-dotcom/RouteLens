from pathlib import Path

from people_counter.caviar import (
    browser_reference_events,
    evaluate_tracking,
    load_caviar_annotations,
    prediction_to_reference_ids,
    remap_event_track_ids,
)


def test_caviar_loader_and_browser_event(tmp_path: Path):
    xml = """<?xml version="1.0"?>
    <dataset name="tiny">
      <frame number="0"><objectlist><object id="7"><box h="20" w="10" xc="50" yc="60"/>
        <hypothesislist><hypothesis evaluation="1"><movement>inactive</movement>
        <role>browser</role><context>browsing</context><situation>browsing</situation>
        </hypothesis></hypothesislist></object></objectlist></frame>
      <frame number="1"><objectlist><object id="7"><box h="20" w="10" xc="51" yc="60"/>
        <hypothesislist><hypothesis evaluation="1"><movement>inactive</movement>
        <role>browser</role><context>browsing</context><situation>browsing</situation>
        </hypothesis></hypothesislist></object></objectlist></frame>
    </dataset>"""
    path = tmp_path / "tiny.xml"
    path.write_text(xml, encoding="utf-8")

    rows = load_caviar_annotations(path, fps=2.0)
    events = browser_reference_events(rows, fps=2.0, min_duration_sec=1.0)

    assert rows[0]["frame_index"] == 1
    assert rows[0]["bbox_x1"] == 45.0
    assert rows[0]["bbox_y2"] == 70.0
    assert events == [
        {
            "event_type": "loitering",
            "track_id": 7,
            "start_frame": 1,
            "end_frame": 2,
            "start_timestamp_sec": 0.5,
            "end_timestamp_sec": 1.0,
            "reference_source": "CAVIAR role=browser/situation=browsing",
        }
    ]


def test_tracking_metrics_identity_mapping_and_event_remap():
    references = [
        _row(1, 10, 0, 0, 10, 10),
        _row(2, 10, 1, 0, 11, 10),
        _row(3, 10, 2, 0, 12, 10),
    ]
    predictions = [
        _row(1, 20, 0, 0, 10, 10),
        _row(2, 20, 1, 0, 11, 10),
        _row(3, 21, 2, 0, 12, 10),
        _row(3, 99, 50, 50, 60, 60),
    ]

    metrics, matches = evaluate_tracking(predictions, references, iou_threshold=0.5)
    mapping = prediction_to_reference_ids(matches)
    events = remap_event_track_ids(
        [{"event_type": "loitering", "track_id": 20}],
        mapping,
    )

    assert metrics["true_positives"] == 3
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 0.75
    assert metrics["recall"] == 1.0
    assert metrics["identity_switches"] == 1
    assert mapping == {20: 10, 21: 10}
    assert events[0]["track_id"] == 10
    assert events[0]["prediction_track_id"] == 20


def _row(frame, track, x1, y1, x2, y2):
    return {
        "frame_index": frame,
        "track_id": track,
        "bbox_x1": x1,
        "bbox_y1": y1,
        "bbox_x2": x2,
        "bbox_y2": y2,
        "centroid_x": (x1 + x2) / 2,
        "centroid_y": (y1 + y2) / 2,
    }
