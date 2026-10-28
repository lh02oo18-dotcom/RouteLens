from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import ScaledTranslation

from tools.audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
plt.rcParams["svg.hashsalt"] = "routelens-v1.1"
plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["legend.frameon"] = False

ROOT = Path("results/caviar-v1.1")
OUT = Path("figures/real-data-evaluation/figure1_real_data_comparison")

MODEL_LABELS = {"yolo11n.pt": "YOLO11n", "yolo11s.pt": "YOLO11s"}
TRACKER_LABELS = {"bytetrack": "ByteTrack", "botsort": "BoT-SORT"}
SEQUENCE_LABELS = {
    "Browse1": "Browse1",
    "Browse_WhileWaiting2": "Browse waiting",
}


def main() -> int:
    per_sequence = _read_metrics(
        [
            (ROOT / "heldout/per_sequence_metrics.csv", "YOLO11n"),
            (ROOT / "heldout-yolo11s/per_sequence_metrics.csv", "YOLO11s"),
        ]
    )
    aggregate = _read_metrics(
        [
            (ROOT / "heldout/aggregate_metrics.csv", "YOLO11n"),
            (ROOT / "heldout-yolo11s/aggregate_metrics.csv", "YOLO11s"),
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    _write_source_data(per_sequence, aggregate)

    fig = plt.figure(figsize=(7.0866, 2.9921))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.32)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    methods = [
        ("YOLO11n", "bytetrack"),
        ("YOLO11n", "botsort"),
        ("YOLO11s", "bytetrack"),
        ("YOLO11s", "botsort"),
    ]
    colors = ["#E6E6E6", "#BFBFBF", "#737373", "#262626"]
    x = np.arange(len(SEQUENCE_LABELS))
    bar_width = 0.18
    for index, ((model, tracker), color) in enumerate(zip(methods, colors, strict=True)):
        values = [
            _value(per_sequence, model, tracker, sequence, "f1")
            for sequence in SEQUENCE_LABELS
        ]
        positions = x + (index - 1.5) * bar_width
        bars = ax_a.bar(
            positions,
            values,
            width=bar_width,
            color=color,
            edgecolor="black",
            linewidth=0.7,
            label=f"{model} + {TRACKER_LABELS[tracker]}",
        )
        for bar, value in zip(bars, values, strict=True):
            ax_a.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.012,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=6,
            )
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(list(SEQUENCE_LABELS.values()))
    ax_a.set_ylim(0, 0.60)
    ax_a.set_ylabel("Box F1 at IoU 0.50")
    ax_a.set_title("Held-out sequence performance", fontsize=8, pad=5)
    ax_a.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=0)
    ax_a.legend(loc="upper left", ncol=2, fontsize=5.8, handlelength=1.8, columnspacing=0.8)

    marker_by_tracker = {"bytetrack": "o", "botsort": "s"}
    fill_by_model = {"YOLO11n": "white", "YOLO11s": "#3F3F3F"}
    label_offsets = {
        ("YOLO11n", "bytetrack"): (10, -7),
        ("YOLO11n", "botsort"): (10, 5),
        ("YOLO11s", "bytetrack"): (10, -7),
        ("YOLO11s", "botsort"): (10, 5),
    }
    for model, tracker in methods:
        fps = _value(aggregate, model, tracker, None, "processing_fps")
        f1 = _value(aggregate, model, tracker, None, "f1")
        ax_b.scatter(
            fps,
            f1,
            s=34,
            marker=marker_by_tracker[tracker],
            facecolor=fill_by_model[model],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        dx, dy = label_offsets[(model, tracker)]
        ax_b.annotate(
            f"{model.replace('YOLO', '')} + {TRACKER_LABELS[tracker]}",
            (fps, f1),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=5.8,
            ha="left",
            va="center",
        )
    ax_b.axvline(25, color="#737373", linestyle="--", linewidth=0.8)
    ax_b.text(27, 0.270, "Real-time 25 FPS", fontsize=5.8, color="#4D4D4D")
    ax_b.set_xlim(20, 88)
    ax_b.set_ylim(0.25, 0.43)
    ax_b.set_xlabel("Processing speed (FPS)")
    ax_b.set_ylabel("Aggregate box F1")
    ax_b.set_title("Accuracy-throughput trade-off", fontsize=8, pad=5)

    _panel_label(ax_a, "a")
    _panel_label(ax_b, "b")
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.18, top=0.84)
    require_matplotlib_panel_alignment(
        fig,
        axes=[ax_a, ax_b],
        panel_ids=["a", "b"],
        row_groups=[["a", "b"]],
        json_out=str(OUT) + ".alignment.json",
        overlay_svg=str(OUT) + ".alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
    )
    svg_path = Path(str(OUT) + ".svg")
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.03)
    _normalise_svg(svg_path)
    fig.savefig(
        str(OUT) + ".pdf",
        bbox_inches="tight",
        pad_inches=0.03,
        metadata={"CreationDate": None, "ModDate": None},
    )
    fig.savefig(str(OUT) + ".png", dpi=600, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(str(OUT) + ".tiff", dpi=600, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return 0


def _read_metrics(sources: list[tuple[Path, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path, model in sources:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["display_model"] = model
                rows.append(row)
    return rows


def _value(
    rows: list[dict[str, str]],
    model: str,
    tracker: str,
    sequence: str | None,
    field: str,
) -> float:
    for row in rows:
        if row["display_model"] != model or row["tracker"] != tracker:
            continue
        if sequence is not None and row.get("sequence") != sequence:
            continue
        return float(row[field])
    raise KeyError((model, tracker, sequence, field))


def _write_source_data(
    per_sequence: list[dict[str, str]],
    aggregate: list[dict[str, str]],
) -> None:
    path = OUT.parent / "figure1_source_data.csv"
    fields = ["scope", "sequence", "model", "tracker", "precision", "recall", "f1", "fps"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for scope, rows in (("sequence", per_sequence), ("aggregate", aggregate)):
            for row in rows:
                writer.writerow(
                    {
                        "scope": scope,
                        "sequence": row.get("sequence", "Aggregate"),
                        "model": row["display_model"],
                        "tracker": TRACKER_LABELS[row["tracker"]],
                        "precision": row["precision"],
                        "recall": row["recall"],
                        "f1": row["f1"],
                        "fps": row["processing_fps"],
                    }
                )


def _panel_label(ax, label: str) -> None:
    offset = ScaledTranslation(-12 / 72, 4 / 72, ax.figure.dpi_scale_trans)
    ax.text(
        0,
        1,
        label,
        transform=ax.transAxes + offset,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def _normalise_svg(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
