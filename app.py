from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import pandas as pd
import streamlit as st

from people_counter.config_runtime import LineConfig, load_config
from people_counter.counter import VideoCounter

st.set_page_config(page_title="RouteLens", layout="wide")
st.title("RouteLens · 可解释人群轨迹分析")
st.caption("v1.0.0：从轨迹中发现通行模式，并用关键帧、轨迹和指标生成异常证据卡。")

config = load_config("config/default.yaml")

with st.sidebar:
    st.header("Input")
    source_mode = st.radio("Source", ["Upload video", "Webcam", "RTSP / URL"])
    uploaded_video = None
    rtsp_url = ""
    if source_mode == "Upload video":
        uploaded_video = st.file_uploader("Video file", type=["mp4", "avi", "mov", "mkv"])
    elif source_mode == "RTSP / URL":
        rtsp_url = st.text_input("Stream URL")

    st.header("Model")
    config.detector.model_path = st.text_input("YOLO model", config.detector.model_path)
    config.detector.confidence = st.slider("Confidence", 0.05, 0.95, config.detector.confidence, 0.05)
    config.detector.iou = st.slider("Detector IoU", 0.1, 0.95, config.detector.iou, 0.05)
    device = st.text_input("Device", config.detector.device or "")
    config.detector.device = device or None

    st.header("Tracking")
    config.tracker.backend = st.selectbox(
        "Tracker",
        ["csrt", "bytetrack", "botsort"],
        index=["csrt", "bytetrack", "botsort"].index(config.tracker.backend),
    )
    config.tracker.iou_threshold = st.slider("CSRT association IoU", 0.05, 0.95, config.tracker.iou_threshold, 0.05)
    config.tracker.max_misses = st.number_input("CSRT max misses", 1, 120, config.tracker.max_misses)

    st.header("Line Crossing")
    enable_line = st.checkbox("Enable IN / OUT line", value=bool(config.analytics.lines))
    if enable_line:
        default_line = config.analytics.lines[0] if config.analytics.lines else LineConfig()
        x1 = st.number_input("Line x1", value=default_line.start[0])
        y1 = st.number_input("Line y1", value=default_line.start[1])
        x2 = st.number_input("Line x2", value=default_line.end[0])
        y2 = st.number_input("Line y2", value=default_line.end[1])
        direction = st.selectbox(
            "IN direction",
            ["negative_to_positive", "positive_to_negative"],
            index=0 if default_line.in_direction == "negative_to_positive" else 1,
        )
        config.analytics.lines = [
            LineConfig(
                name="main",
                start=(int(x1), int(y1)),
                end=(int(x2), int(y2)),
                in_direction=direction,
            )
        ]
    else:
        config.analytics.lines = []

    with st.expander("RouteLens analytics", expanded=True):
        enable_reverse = st.checkbox(
            "Enable reverse-direction detection",
            value=config.analytics.expected_direction is not None,
            help="Set the expected scene direction. A reverse event requires sustained conflict.",
        )
        default_direction = config.analytics.expected_direction or (1.0, 0.0)
        direction_x = st.number_input("Expected direction X", value=float(default_direction[0]))
        direction_y = st.number_input("Expected direction Y", value=float(default_direction[1]))
        config.analytics.expected_direction = (
            (float(direction_x), float(direction_y)) if enable_reverse else None
        )
        config.analytics.reverse_min_duration_sec = st.number_input(
            "Reverse minimum duration (sec)",
            min_value=0.1,
            value=float(config.analytics.reverse_min_duration_sec),
        )
        config.analytics.reverse_min_distance_px = st.number_input(
            "Reverse minimum distance (px)",
            min_value=0.0,
            value=float(config.analytics.reverse_min_distance_px),
        )
        config.analytics.loitering_enabled = st.checkbox(
            "Enable loitering detection", value=config.analytics.loitering_enabled
        )
        config.analytics.loitering_min_duration_sec = st.number_input(
            "Loitering minimum duration (sec)",
            min_value=0.1,
            value=float(config.analytics.loitering_min_duration_sec),
        )
        config.analytics.loitering_max_radius_px = st.number_input(
            "Loitering maximum radius (px)",
            min_value=0.0,
            value=float(config.analytics.loitering_max_radius_px),
        )
        config.analytics.loitering_min_path_length_px = st.number_input(
            "Loitering minimum path length (px)",
            min_value=0.0,
            value=float(config.analytics.loitering_min_path_length_px),
        )
        config.analytics.route_mining_enabled = st.checkbox(
            "Enable route clustering", value=config.analytics.route_mining_enabled
        )
        config.analytics.route_dbscan_eps = st.number_input(
            "Route similarity radius",
            min_value=0.001,
            max_value=2.0,
            value=float(config.analytics.route_dbscan_eps),
            step=0.01,
            help="DBSCAN radius after scene-level normalization; smaller values form tighter routes.",
        )
        config.analytics.route_dbscan_min_samples = st.number_input(
            "Minimum tracks per route",
            min_value=2,
            max_value=100,
            value=int(config.analytics.route_dbscan_min_samples),
        )
        config.analytics.route_deviation_threshold = st.number_input(
            "Deviation score threshold",
            min_value=0.001,
            max_value=2.0,
            value=float(config.analytics.route_deviation_threshold),
            step=0.01,
        )

    st.header("Runtime")
    config.runtime.frame_skip = st.number_input("Frame skip", 1, 30, config.runtime.frame_skip)
    max_frames = st.number_input("Max frames (0 = all)", 0, 100000, 0)
    config.runtime.max_frames = int(max_frames) or None
    config.runtime.privacy_blur = st.checkbox("Privacy blur", value=config.runtime.privacy_blur)
    config.output.save_annotated_video = st.checkbox("Save annotated MP4", value=False)
    config.output.save_evidence_cards = st.checkbox(
        "Generate anomaly evidence cards",
        value=config.output.save_evidence_cards,
        help="Each card records a keyframe, trajectory, reason, metric and threshold.",
    )

    start = st.button("Run analysis", type="primary")

video_placeholder = st.empty()
metrics_placeholder = st.empty()
event_placeholder = st.empty()


def on_frame(frame, frame_result, tracks) -> None:
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
    metrics_placeholder.metric("Current occupancy", frame_result.current_occupancy)
    cols = event_placeholder.columns(4)
    cols[0].metric("IN", frame_result.total_entered)
    cols[1].metric("OUT", frame_result.total_exited)
    cols[2].metric("Peak", frame_result.peak_occupancy)
    cols[3].metric("FPS", f"{frame_result.fps:.1f}")


def resolve_source():
    if source_mode == "Webcam":
        return 0, None
    if source_mode == "RTSP / URL":
        return rtsp_url.strip(), None
    if uploaded_video is None:
        return None, None

    suffix = Path(uploaded_video.name).suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_video.read())
    tmp.close()
    return tmp.name, tmp.name


if start:
    source, temp_path = resolve_source()
    if source is None:
        st.warning("Choose a source before running.")
    else:
        try:
            with st.spinner("Processing video..."):
                result = VideoCounter(source=source, config=config).run(
                    stream_callback=on_frame,
                    export=True,
                )
            st.success("Analysis complete.")

            st.subheader("Session summary")
            st.json(result.summary)

            if result.frame_metrics:
                metrics_df = pd.DataFrame(result.frame_metrics)
                st.subheader("Occupancy over time")
                st.line_chart(metrics_df.set_index("timestamp_sec")["current_occupancy"])
                st.dataframe(metrics_df, use_container_width=True)

            if result.events:
                st.subheader("Crossing events")
                st.dataframe(pd.DataFrame(result.events), use_container_width=True)

            if result.trajectory_features:
                st.subheader("RouteLens trajectory features")
                st.dataframe(
                    pd.DataFrame(result.trajectory_features),
                    use_container_width=True,
                )

            st.subheader("RouteLens route mining")
            st.json(result.route_summary)
            if result.route_assignments:
                st.dataframe(
                    pd.DataFrame(result.route_assignments),
                    use_container_width=True,
                )
            else:
                st.info("No supported route cluster was available for this session.")

            st.subheader("RouteLens anomaly events")
            if result.anomaly_events:
                st.dataframe(pd.DataFrame(result.anomaly_events), use_container_width=True)
            else:
                st.info("No trajectory met the configured anomaly thresholds.")

            st.subheader("RouteLens evidence cards")
            st.json(result.evidence_summary)
            if result.evidence_cards:
                for card in result.evidence_cards:
                    image_path = Path(config.output.directory) / card["image_path"]
                    with st.expander(
                        f"{card['card_id']} · {card['event_type']} · Track {card['track_id']}",
                        expanded=True,
                    ):
                        if image_path.exists():
                            st.image(str(image_path), use_container_width=True)
                        st.json(card)
            else:
                st.info("No anomaly event was available for an evidence card.")

            if result.output_paths:
                st.subheader("Downloads")
                for name, path in result.output_paths.items():
                    file_path = Path(path)
                    if file_path.exists():
                        st.download_button(
                            label=f"Download {name}",
                            data=file_path.read_bytes(),
                            file_name=file_path.name,
                        )
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)
else:
    st.info("Configure a source and click Run analysis.")
