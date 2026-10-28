# Figure 1 contract

Core conclusion: Increasing detector capacity from YOLO11n to YOLO11s improves held-out CAVIAR tracking F1 for both ByteTrack and BoT-SORT, while all configurations remain faster than the 25 FPS source frame rate.

Results-level question: On the held-out real-video subset, does detector capacity or tracker choice contribute more to accuracy, and does the improved configuration remain practical on the test computer?

Figure archetype: quantitative grid.

Target output: Chinese research-report figure, double-column width, grayscale-print compatible.

Backend: Python with Matplotlib.

Final size: 180 mm × 76 mm.

Panel map:

- a: Per-sequence box F1 for two detector sizes and two trackers; primary evidence for generality across the two held-out sequences.
- b: Aggregate held-out F1 versus video-loop processing throughput; validation that the measured loop throughput remains above the 25 FPS source frame rate.

Evidence hierarchy:

- Hero evidence: per-sequence held-out F1.
- Validation evidence: aggregate speed-accuracy trade-off.
- Boundary result: event-level loitering F1 is zero for every configuration and is reported in the table and text instead of being hidden in a visually uninformative all-zero panel.

Statistics: one deterministic run per configuration on fixed videos; no random-seed variance or confidence interval is claimed.

Source data: `results/caviar-v1.1/heldout` and `results/caviar-v1.1/heldout-yolo11s` CSV outputs.

Reviewer risks: only two held-out sequences, staged behavior, non-exhaustive CAVIAR person boxes, no uncertainty estimate, and behavior-label semantics do not exactly equal the RouteLens geometric loitering rule.
