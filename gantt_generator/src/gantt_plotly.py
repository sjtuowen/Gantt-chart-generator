import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
from html import escape

try:
    from .gantt_label_layout import LABEL_INSIDE, get_task_label_position
except ImportError:
    from gantt_label_layout import LABEL_INSIDE, get_task_label_position


VIEW_MODE_CONFIGS = {
    "Day": {
        "tickformat": "%m-%d",
        "dtick": 86400000,
        "tickangle": -45,
    },
    "Week": {
        "tickformat": "%Y-%m-%d",
        "dtick": 604800000,
        "tickangle": 0,
    },
    "Month": {
        "tickformat": "%Y-%m",
        "dtick": "M1",
        "tickangle": 0,
    },
}


def auto_view_mode(df: pd.DataFrame) -> str:
    span = (df["end"].max() - df["start"].min()).days
    if span <= 31:
        return "Day"
    elif span <= 180:
        return "Week"
    return "Month"


def create_gantt_figure(
    df: pd.DataFrame,
    project_name: str,
    view_mode: str = "Day",
    show_progress: bool = True,
    show_today: bool = True,
) -> go.Figure:
    task_order = df["name"].tolist()
    df = df.copy()
    df["name"] = pd.Categorical(df["name"], categories=task_order, ordered=True)
    df["plot_end"] = df["end"] + pd.Timedelta(days=1)
    df["is_milestone"] = df["status"].astype(str).str.lower() == "milestone"
    label_position = get_task_label_position(df)

    groups = df["group"].unique()
    color_palette = pc.qualitative.Plotly
    group_color_map = {}
    for i, g in enumerate(groups):
        group_color_map[g] = color_palette[i % len(color_palette)]

    if show_progress:
        df["progress_end"] = df.apply(
            lambda row: (
                row["start"] + (row["plot_end"] - row["start"]) * row["progress"] / 100
                if row["progress"] > 0
                else row["start"]
            ),
            axis=1,
        )

    fig = go.Figure()

    legend_shown = set()
    annotations = []

    for _, row in df[~df["is_milestone"]].iterrows():
        task_name = str(row["name"])
        group = str(row["group"])
        color = group_color_map.get(group, "gray")
        start_ts = pd.Timestamp(row["start"])
        end_ts = pd.Timestamp(row["end"])
        plot_end_ts = pd.Timestamp(row["plot_end"])
        status = str(row.get("status", ""))
        progress_val = int(row.get("progress", 0))
        depends = str(row.get("depends_on", ""))

        hovertemplate = (
            f"<b>{task_name}</b><br>"
            f"start={start_ts.strftime('%Y-%m-%d')}<br>"
            f"end={end_ts.strftime('%Y-%m-%d')}<br>"
            f"status={status}<br>"
            f"progress={progress_val}%<br>"
            f"depends_on={depends}<extra></extra>"
        )
        label_inside = label_position == LABEL_INSIDE
        label_x = start_ts + (plot_end_ts - start_ts) / 2 if label_inside else start_ts
        annotations.append(
            dict(
                x=label_x,
                y=task_name,
                text=escape(task_name),
                showarrow=False,
                xanchor="center" if label_inside else "left",
                yanchor="middle" if label_inside else "bottom",
                yshift=0 if label_inside else 18,
                font=dict(size=12, color="#111827"),
                bgcolor=(
                    "rgba(255,255,255,0.74)"
                    if label_inside
                    else "rgba(255,255,255,0.88)"
                ),
                bordercolor="rgba(0,0,0,0)",
                borderpad=3,
            )
        )

        if show_progress:
            progress_ts = pd.Timestamp(row["progress_end"])
            show_legend = group not in legend_shown
            if show_legend:
                legend_shown.add(group)

            if progress_val < 100:
                remain_start = progress_ts if progress_val > 0 else start_ts
                remain_duration_ms = (plot_end_ts - remain_start).total_seconds() * 1000

                fig.add_trace(
                    go.Bar(
                        base=remain_start,
                        x=[remain_duration_ms],
                        y=[task_name],
                        orientation="h",
                        marker=dict(color=color, line=dict(width=0)),
                        opacity=0.3,
                        name=group,
                        hoverinfo="skip",
                        legendgroup=group,
                        showlegend=show_legend,
                        width=0.6,
                    )
                )
                show_legend = False

            if progress_val > 0:
                completed_duration_ms = (progress_ts - start_ts).total_seconds() * 1000

                fig.add_trace(
                    go.Bar(
                        base=start_ts,
                        x=[completed_duration_ms],
                        y=[task_name],
                        orientation="h",
                        marker=dict(color=color, line=dict(width=0)),
                        opacity=1.0,
                        name=group,
                        hovertemplate=hovertemplate,
                        legendgroup=group,
                        showlegend=show_legend,
                        width=0.6,
                    )
                )
        else:
            duration_ms = (plot_end_ts - start_ts).total_seconds() * 1000
            show_legend = group not in legend_shown
            if show_legend:
                legend_shown.add(group)

            fig.add_trace(
                go.Bar(
                    base=start_ts,
                    x=[duration_ms],
                    y=[task_name],
                    orientation="h",
                    marker=dict(color=color, line=dict(width=0)),
                    opacity=1.0,
                    name=group,
                    hovertemplate=hovertemplate,
                    legendgroup=group,
                    showlegend=show_legend,
                    width=0.6,
                )
            )

    milestone_df = df[df["is_milestone"]]
    if not milestone_df.empty:
        for _, row in milestone_df.iterrows():
            task_name = str(row["name"])
            annotations.append(
                dict(
                    x=pd.Timestamp(row["start"]),
                    y=task_name,
                    text=escape(task_name),
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    yshift=18,
                    font=dict(size=12, color="#333333"),
                    bgcolor="rgba(255,255,255,0.88)",
                    bordercolor="rgba(0,0,0,0)",
                    borderpad=3,
                )
            )
        fig.add_trace(
            go.Scatter(
                x=milestone_df["start"],
                y=milestone_df["name"].astype(str),
                mode="markers",
                name="milestone",
                marker=dict(
                    symbol="diamond",
                    size=14,
                    color=[
                        group_color_map.get(str(group), "gray")
                        for group in milestone_df["group"]
                    ],
                    line=dict(width=1, color="#222"),
                ),
                customdata=milestone_df[
                    ["name", "status", "progress", "depends_on"]
                ].astype(str),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "date=%{x|%Y-%m-%d}<br>"
                    "status=%{customdata[1]}<br>"
                    "progress=%{customdata[2]}%<br>"
                    "depends_on=%{customdata[3]}<extra></extra>"
                ),
                showlegend=True,
            )
        )

    fig.update_layout(
        title=dict(text=project_name, font=dict(size=18)),
        barmode="overlay",
        annotations=annotations,
    )

    fig.update_yaxes(
        autorange="reversed",
        type="category",
        title=None,
        tickfont=dict(size=14),
        categoryorder="array",
        categoryarray=task_order,
    )

    today = pd.Timestamp.now().normalize()
    x_min = df["start"].min() - pd.Timedelta(days=2)
    x_max = df["plot_end"].max() + pd.Timedelta(days=2)

    if show_today:
        if today < x_min:
            x_min = today - pd.Timedelta(days=2)
        if today > x_max:
            x_max = today + pd.Timedelta(days=2)

    view_config = VIEW_MODE_CONFIGS.get(view_mode, VIEW_MODE_CONFIGS["Day"])

    fig.update_xaxes(
        title=dict(text="Date", font=dict(size=13)),
        range=[x_min, x_max],
        tickformat=view_config["tickformat"],
        dtick=view_config["dtick"],
        tickangle=view_config["tickangle"],
        type="date",
        tickfont=dict(size=12),
    )

    if show_today:
        today_label = f"Today: {today.strftime('%Y-%m-%d')}"
        fig.add_shape(
            type="line",
            x0=today,
            x1=today,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(width=2, dash="dash", color="#d62728"),
        )
        fig.add_annotation(
            x=today,
            y=1.12,
            xref="x",
            yref="paper",
            text=today_label,
            showarrow=False,
            font=dict(size=12, color="#d62728"),
            xanchor="left",
            yanchor="bottom",
        )

    height = max(620, 82 * len(df) + 220)
    fig.update_layout(
        height=height,
        bargap=0.4,
        margin=dict(l=150, r=40, t=120, b=70),
        font=dict(size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="right",
            x=1,
            font=dict(size=12),
        ),
    )

    return fig
