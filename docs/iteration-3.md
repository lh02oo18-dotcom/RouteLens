# Iteration 3: evidence cards and stable delivery

Version `1.0.0` adds a reviewable evidence layer without changing the anomaly rules.

## Evidence-card contract

Each anomaly card contains:

- event type and track ID;
- start/end time and the representative frame index;
- the tracked path and target bounding box;
- the rule metrics and thresholds that triggered the event;
- a trajectory reference and a portable image path.

For a seekable local video, RouteLens reads the middle frame of the event. Camera and
network streams may no longer be seekable after processing, so the card uses a neutral
canvas and records `frame_source=generated_canvas`. This fallback is explicit and never
pretends that a missing frame was captured. Privacy blur is also applied to the evidence
frame when it is enabled for the session.

## Reproducible fallback demo

```powershell
.\.venv\Scripts\python.exe -m tools.evidence_demo `
  --output-dir outputs\evidence_demo
```

The command creates `evidence_cards/`, `evidence_cards.csv`, and
`evidence_manifest.json`. The included event is synthetic and validates rendering and
export only; it is not a real-world accuracy result.

## Verification boundary

Unit tests cover keyframe selection, output dimensions, fallback status, manifest export,
and empty-event behavior. Real-video precision, recall, and F1 still require licensed
video, independent annotations, and a frozen evaluation configuration.
