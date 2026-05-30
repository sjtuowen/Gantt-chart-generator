from pathlib import Path
from io import BytesIO
import importlib.util
import os
import shutil
import subprocess
import sys

import matplotlib.dates as mdates
from matplotlib import font_manager
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

try:
    from .gantt_label_layout import LABEL_INSIDE, get_task_label_position
except ImportError:
    from gantt_label_layout import LABEL_INSIDE, get_task_label_position


SUPPORTED_FORMATS = {"png", "pdf"}
EXPORT_TIMEOUT_SECONDS = 8
CHROME_COMMANDS = (
    "chrome",
    "chrome.exe",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chromium.exe",
)
CJK_FONT_NAMES = (
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "WenQuanYi Micro Hei",
    "Arial Unicode MS",
)


def get_cjk_font_properties() -> font_manager.FontProperties:
    for font_name in CJK_FONT_NAMES:
        try:
            font_path = font_manager.findfont(
                font_manager.FontProperties(family=font_name),
                fallback_to_default=False,
            )
            return font_manager.FontProperties(fname=font_path)
        except Exception:
            continue
    return font_manager.FontProperties()


def set_cjk_tick_fonts(ax, font_properties: font_manager.FontProperties) -> None:
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_properties)


def has_chrome_or_chromium() -> bool:
    if any(shutil.which(command) for command in CHROME_COMMANDS):
        return True

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("PROGRAMFILES", "")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")
    chrome_paths = [
        Path(local_app_data) / "Google/Chrome/Application/chrome.exe",
        Path(program_files) / "Google/Chrome/Application/chrome.exe",
        Path(program_files_x86) / "Google/Chrome/Application/chrome.exe",
        Path(program_files) / "Chromium/Application/chrome.exe",
        Path(program_files_x86) / "Chromium/Application/chrome.exe",
    ]
    return any(path.exists() for path in chrome_paths)


def export_plotly_figure(fig: go.Figure, fmt: str = "png") -> bytes:
    fmt = fmt.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}")

    if importlib.util.find_spec("kaleido") is None:
        raise RuntimeError("Static export requires kaleido. Please install kaleido.")

    if not has_chrome_or_chromium():
        raise RuntimeError(
            "Static export requires kaleido and Chrome/Chromium. Please install "
            "Chrome or Chromium, then try again."
        )

    script = """
import sys
from io import BytesIO

import plotly.io as pio

fmt = sys.argv[1]
fig = pio.from_json(sys.stdin.buffer.read().decode("utf-8"))
buffer = BytesIO()
fig.write_image(buffer, format=fmt)
sys.stdout.buffer.write(buffer.getvalue())
"""
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            [sys.executable, "-c", script, fmt],
            input=fig.to_json().encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=EXPORT_TIMEOUT_SECONDS,
            creationflags=creationflags,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Static export timed out. Please check kaleido and Chrome/Chromium, "
            "then try again."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Static export failed. Please install kaleido and make sure "
            "Chrome/Chromium is available for Plotly image export."
        ) from exc

    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="ignore").strip()
        detail = f" Details: {error}" if error else ""
        raise RuntimeError(
            "Static export failed. Please install kaleido and make sure "
            f"Chrome/Chromium is available for Plotly image export.{detail}"
        )

    if not result.stdout:
        raise RuntimeError("Static export failed: empty image output.")

    return result.stdout


def export_tasks_static_image(
    df: pd.DataFrame,
    project_name: str,
    fmt: str = "png",
    show_progress: bool = True,
    show_today: bool = True,
) -> bytes:
    fmt = fmt.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}")

    plot_df = df.copy().reset_index(drop=True)
    plot_df["plot_end"] = plot_df["end"] + pd.Timedelta(days=1)
    plot_df["status"] = plot_df["status"].astype(str)
    plot_df["is_milestone"] = plot_df["status"].str.lower() == "milestone"
    label_position = get_task_label_position(plot_df)

    groups = plot_df["group"].astype(str).unique().tolist()
    palette = plt.get_cmap("tab10")
    color_map = {group: palette(i % 10) for i, group in enumerate(groups)}
    font_properties = get_cjk_font_properties()
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42

    fig_height = max(4.8, 0.5 * len(plot_df) + 1.8)
    fig_width = 12
    figure, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)

    y_positions = list(range(len(plot_df)))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(plot_df["name"].astype(str), fontproperties=font_properties)
    ax.invert_yaxis()

    for y, row in zip(y_positions, plot_df.to_dict("records")):
        start = pd.Timestamp(row["start"])
        plot_end = pd.Timestamp(row["plot_end"])
        group = str(row.get("group", "General"))
        color = color_map.get(group, "tab:blue")
        progress = int(row.get("progress", 0))
        task_label = str(row.get("name", ""))

        if row["is_milestone"]:
            ax.scatter(
                start,
                y,
                marker="D",
                s=90,
                color=color,
                edgecolor="#222222",
                linewidth=0.8,
                zorder=4,
            )
            ax.text(
                start,
                y - 0.25,
                task_label,
                fontsize=8,
                ha="left",
                va="bottom",
                color="#333333",
                fontproperties=font_properties,
                clip_on=False,
                bbox=dict(
                    facecolor="white",
                    alpha=0.88,
                    edgecolor="none",
                    boxstyle="round,pad=0.22",
                ),
            )
            continue

        total_days = (plot_end - start).total_seconds() / 86400
        start_num = mdates.date2num(start)
        ax.barh(
            y,
            total_days,
            left=start_num,
            height=0.5,
            color=color,
            alpha=0.28,
            edgecolor="none",
        )

        if show_progress and progress > 0:
            progress_days = total_days * progress / 100
            ax.barh(
                y,
                progress_days,
                left=start_num,
                height=0.5,
                color=color,
                alpha=0.95,
                edgecolor="none",
            )

        label_inside = label_position == LABEL_INSIDE
        ax.text(
            start_num + total_days / 2 if label_inside else start_num,
            y if label_inside else y - 0.33,
            task_label,
            ha="center" if label_inside else "left",
            va="center" if label_inside else "bottom",
            fontsize=8,
            color="#111827",
            fontproperties=font_properties,
            clip_on=False,
            bbox=dict(
                facecolor="white",
                alpha=0.74 if label_inside else 0.88,
                edgecolor="none",
                boxstyle="round,pad=0.22",
            ),
        )

    today = pd.Timestamp.today().normalize()
    x_min = plot_df["start"].min() - pd.Timedelta(days=2)
    x_max = plot_df["plot_end"].max() + pd.Timedelta(days=2)
    if show_today and x_min <= today <= x_max:
        ax.axvline(today, color="#d62728", linestyle="--", linewidth=1.4)
        ax.text(
            today,
            -0.75,
            f"Today {today.strftime('%Y-%m-%d')}",
            color="#d62728",
            fontsize=9,
            ha="left",
            va="bottom",
            fontproperties=font_properties,
        )

    ax.set_xlim(x_min, x_max)
    ax.set_title(project_name, fontsize=15, pad=14, fontproperties=font_properties)
    ax.set_xlabel("Date", fontproperties=font_properties)
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    figure.autofmt_xdate(rotation=35, ha="right")
    set_cjk_tick_fonts(ax, font_properties)

    legend_handles = [
        plt.Line2D([0], [0], color=color_map[group], lw=6, label=group)
        for group in groups
    ]
    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="upper right",
            frameon=False,
            prop=font_properties,
        )

    buffer = BytesIO()
    save_kwargs = {"format": fmt, "bbox_inches": "tight"}
    if fmt == "png":
        save_kwargs["dpi"] = 180
    figure.savefig(buffer, **save_kwargs)
    plt.close(figure)
    return buffer.getvalue()
