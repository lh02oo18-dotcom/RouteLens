"""People counting, tracking, and video analytics package."""

import os
from pathlib import Path

# Keep third-party runtime settings inside the project instead of writing to a
# user profile. This makes local runs and CI reproducible on restricted hosts.
if "YOLO_CONFIG_DIR" not in os.environ:
    _runtime_config_dir = Path(__file__).resolve().parent.parent / ".runtime" / "ultralytics"
    _runtime_config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(_runtime_config_dir)

from .config_runtime import AppConfig, load_config  # noqa: E402
from .counter import SessionResult, VideoCounter  # noqa: E402

__all__ = ["AppConfig", "SessionResult", "VideoCounter", "load_config"]
