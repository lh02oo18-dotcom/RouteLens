from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUTPUT_DIR = Path("figures/report-diagrams")


def _configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
            "axes.unicode_minus": False,
        }
    )


def _box(ax, xy, width, height, title, lines=(), *, dark=False, dashed=False, title_size=13):
    face = "#252525" if dark else "#F2F2F2"
    edge = "#252525"
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face,
        edgecolor=edge,
        linewidth=2,
        linestyle="--" if dashed else "-",
    )
    ax.add_patch(patch)
    color = "white" if dark else "black"
    cx = xy[0] + width / 2
    ax.text(cx, xy[1] + height * 0.66, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=color)
    if lines:
        ax.text(cx, xy[1] + height * 0.31, "\n".join(lines), ha="center", va="center", fontsize=9.5, color=color, linespacing=1.2)
    return patch


def _arrow(ax, start, end, *, dashed=False):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.7,
            linestyle="--" if dashed else "-",
            color="#333333",
        )
    )


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(13.2, 5.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.05, 0.93, "RouteLens v1.1.0 分层架构与评价闭环", fontsize=22, fontweight="bold", ha="left")

    xs = [0.05, 0.23, 0.41, 0.59, 0.77]
    top = [
        ("视频输入", ("文件 / 摄像头",)),
        ("人员检测", ("YOLO11n / YOLO11s",)),
        ("目标跟踪", ("ByteTrack / BoT-SORT",)),
        ("统一轨迹", ("Track ID / 时空点",)),
        ("基础统计", ("计数 / 占用 / 越线",)),
    ]
    for i, (title, lines) in enumerate(top):
        _box(ax, (xs[i], 0.65), 0.15, 0.17, title, lines, dark=i in {1, 3})
        if i < len(top) - 1:
            _arrow(ax, (xs[i] + 0.15, 0.735), (xs[i + 1], 0.735))

    bottom = [
        (0.20, "轨迹特征", ("速度 / 方向 / 半径",), False),
        (0.39, "路线挖掘", ("重采样 / DBSCAN",), True),
        (0.58, "异常事件", ("逆行 / 徘徊 / 偏离",), False),
        (0.77, "证据卡", ("关键帧 / 指标 / 阈值",), True),
    ]
    for x, title, lines, dark in bottom:
        _box(ax, (x, 0.31), 0.16, 0.17, title, lines, dark=dark)
    _arrow(ax, (0.665, 0.65), (0.28, 0.48))
    for a, b in zip(bottom, bottom[1:], strict=False):
        _arrow(ax, (a[0] + 0.16, 0.395), (b[0], 0.395))

    _box(ax, (0.05, 0.07), 0.27, 0.13, "CAVIAR人工标注", ("框 / 身份 / 行为标签",), dashed=True)
    _box(ax, (0.42, 0.07), 0.38, 0.13, "评价与复现", ("P / R / F1 · 覆盖率 · ID切换 · FPS · 哈希",), dark=True)
    _arrow(ax, (0.32, 0.135), (0.42, 0.135), dashed=True)
    _arrow(ax, (0.85, 0.31), (0.72, 0.20), dashed=True)
    ax.text(0.95, 0.07, "实线：运行主路径\n虚线：评价证据链", ha="right", va="bottom", fontsize=10, color="#555555")
    fig.tight_layout()
    _save(fig, "architecture_v1.1.png")


def evidence_layers() -> None:
    fig, ax = plt.subplots(figsize=(13.2, 5.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.05, 0.91, "v1.1.0 可复核证据链", fontsize=23, fontweight="bold", ha="left")
    items = [
        (0.05, "工程质量", ("26项测试", "Ruff / pip check"), True),
        (0.28, "合成边界", ("12组参数", "规则与安全门"), False),
        (0.51, "端到端冒烟", ("30帧视频", "接口与导出"), False),
        (0.74, "真实数据试验", ("3,312人工框", "F1=0.3958 / 事件F1=0"), True),
    ]
    for i, (x, title, lines, dark) in enumerate(items):
        _box(ax, (x, 0.55), 0.19, 0.22, title, lines, dark=dark, title_size=14)
        if i < len(items) - 1:
            _arrow(ax, (x + 0.19, 0.66), (items[i + 1][0], 0.66))
    _box(ax, (0.15, 0.17), 0.32, 0.19, "证据支持", ("本机可运行 / 指标可复现 / 实时处理",), dark=False)
    _box(ax, (0.57, 0.17), 0.32, 0.19, "证据不支持", ("真实徘徊有效 / 跨场景泛化 / 生产准确率",), dashed=True)
    ax.text(0.52, 0.05, "证据层级决定结论强度；负结果保留在主结论中", ha="center", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, "evidence_chain_v1.1.png")


def timeline() -> None:
    fig, ax = plt.subplots(figsize=(13.2, 4.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.05, 0.89, "版本迭代与证据增长路线", fontsize=23, fontweight="bold", ha="left")
    xs = [0.12, 0.31, 0.50, 0.69, 0.88]
    labels = [
        ("v0.1.0", "检测/跟踪\n计数/导出"),
        ("v0.2.0", "轨迹特征\n逆行/徘徊"),
        ("v0.3.0", "DBSCAN路线\n偏离评价"),
        ("v1.0.0", "异常证据卡\nPages/Release"),
        ("v1.1.0", "CAVIAR试验\n真实指标/负结果"),
    ]
    ax.plot([xs[0], xs[-1]], [0.55, 0.55], color="#333333", linewidth=2)
    for i, (x, (version, detail)) in enumerate(zip(xs, labels, strict=True)):
        ax.scatter([x], [0.55], s=420, c="#222222" if i < 4 else "#777777", edgecolors="#222222", linewidths=2, zorder=3)
        ax.text(x, 0.74, version, ha="center", fontsize=16, fontweight="bold")
        ax.text(x, 0.35, detail, ha="center", va="center", fontsize=11, linespacing=1.15)
        ax.text(x, 0.19, "已验证", ha="center", fontsize=9.5, color="#555555")
    ax.text(0.95, 0.08, "截至 2026-10-23", ha="right", fontsize=10.5, color="#555555")
    fig.tight_layout()
    _save(fig, "timeline_v1.1.png")


def _save(fig, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(path)


def main() -> None:
    _configure()
    architecture()
    evidence_layers()
    timeline()


if __name__ == "__main__":
    main()
