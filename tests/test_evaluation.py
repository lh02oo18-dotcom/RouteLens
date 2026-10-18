from people_counter.evaluation import evaluate_events


def _event(track_id, start, end, event_type="route_deviation"):
    return {
        "event_type": event_type,
        "track_id": track_id,
        "start_timestamp_sec": start,
        "end_timestamp_sec": end,
    }


def test_event_evaluation_reports_tp_fp_and_fn():
    predictions = [_event(1, 1.0, 4.0), _event(9, 0.0, 2.0)]
    references = [_event(1, 2.0, 5.0), _event(2, 0.0, 2.0)]

    result = evaluate_events(predictions, references, min_temporal_iou=0.1)

    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5


def test_event_evaluation_requires_type_track_and_overlap():
    references = [_event(1, 0.0, 2.0)]
    predictions = [
        _event(1, 3.0, 4.0),
        _event(1, 0.0, 2.0, event_type="loitering"),
        _event(2, 0.0, 2.0),
    ]

    result = evaluate_events(predictions, references)

    assert result["true_positives"] == 0
    assert result["false_positives"] == 3
    assert result["false_negatives"] == 1
