from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def require_matplotlib_panel_alignment(
    fig: Any,
    *,
    axes: list[Any],
    panel_ids: list[str],
    row_groups: list[list[str]],
    json_out: str,
    overlay_svg: str | None = None,
    tolerance_pt: float = 1.5,
    gutter_tolerance_pt: float = 1.5,
    require_panel_labels: bool = True,
    strict: bool = True,
) -> dict[str, Any]:
    """Audit a Matplotlib panel row and persist a small, portable QA record.

    This project only needs row-edge alignment and panel-label checks. Keeping the
    audit local makes ``python -m tools.plot_caviar_results`` reproducible from a
    fresh clone without relying on an unpublished helper module.
    """
    if len(axes) != len(panel_ids):
        raise ValueError("axes and panel_ids must have the same length")
    if len(set(panel_ids)) != len(panel_ids):
        raise ValueError("panel_ids must be unique")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    points_per_pixel = 72.0 / fig.dpi
    panels: dict[str, dict[str, Any]] = {}
    findings: list[dict[str, Any]] = []

    for panel_id, axis in zip(panel_ids, axes, strict=True):
        bounds = [
            float(value * points_per_pixel)
            for value in axis.get_window_extent(renderer).extents
        ]
        labels = [text.get_text().strip() for text in axis.texts]
        has_label = panel_id in labels
        panels[panel_id] = {"bbox_pt": bounds, "panel_label": panel_id if has_label else None}
        if require_panel_labels and not has_label:
            findings.append(
                {"severity": "fail", "check": "panel_label", "panel": panel_id}
            )

    for group_index, group in enumerate(row_groups, start=1):
        unknown = [panel_id for panel_id in group if panel_id not in panels]
        if unknown:
            raise ValueError(f"unknown panel ids in row group: {unknown}")
        if len(group) < 2:
            continue
        bottoms = [panels[panel_id]["bbox_pt"][1] for panel_id in group]
        tops = [panels[panel_id]["bbox_pt"][3] for panel_id in group]
        bottom_delta = max(bottoms) - min(bottoms)
        top_delta = max(tops) - min(tops)
        if bottom_delta > tolerance_pt or top_delta > tolerance_pt:
            findings.append(
                {
                    "severity": "fail",
                    "check": "row_alignment",
                    "row": group_index,
                    "bottom_delta_pt": round(bottom_delta, 4),
                    "top_delta_pt": round(top_delta, 4),
                }
            )

    failed = sum(item["severity"] == "fail" for item in findings)
    report = {
        "schema_version": 1,
        "applicable": True,
        "auditable": True,
        "verdict": "PASS" if failed == 0 else "FAIL",
        "backend": "python-matplotlib",
        "summary": {"fail": failed, "comparisons": len(row_groups)},
        "tolerances": {
            "alignment_pt": tolerance_pt,
            "gutter_pt": gutter_tolerance_pt,
        },
        "layout": {
            "figure": {
                "width_pt": float(fig.get_figwidth() * 72),
                "height_pt": float(fig.get_figheight() * 72),
            },
            "panels": [
                {"id": panel_id, **panels[panel_id]} for panel_id in panel_ids
            ],
            "row_groups": row_groups,
        },
        "findings": findings,
    }

    output_path = Path(json_out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if overlay_svg:
        _write_overlay(Path(overlay_svg), report)
    if strict and failed:
        raise RuntimeError(f"panel alignment audit failed: {findings}")
    return report


def _write_overlay(path: Path, report: dict[str, Any]) -> None:
    width = report["layout"]["figure"]["width_pt"]
    height = report["layout"]["figure"]["height_pt"]
    rectangles: list[str] = []
    for panel in report["layout"]["panels"]:
        left, bottom, right, top = panel["bbox_pt"]
        rectangles.append(
            f'<rect x="{left:.3f}" y="{height - top:.3f}" '
            f'width="{right - left:.3f}" height="{top - bottom:.3f}" '
            'fill="none" stroke="#d62728" stroke-width="0.75"/>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}pt" '
        f'height="{height:.3f}pt" viewBox="0 0 {width:.3f} {height:.3f}">\n'
        + "\n".join(rectangles)
        + "\n</svg>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
