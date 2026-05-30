import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc


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

    groups = df["group"].unique()
    color_palette = pc.qualitative.Plotly
    group_color_map = {}
    for i, g in enumerate(groups):
        group_color_map[g] = color_palette[i % len(color_palette)]

    if show_progress:
        df["progress_end"] = df.apply(
            lambda row: row["start"] + (row["end"] - row["start"]) * row["progress"] / 100
            if row["progress"] > 0
            else row["start"],
            axis=1,
        )

        fig = go.Figure()

        legend_shown = set()

        for _, row in df.iterrows():
            task_name = str(row["name"])
            group = str(row["group"])
            color = group_color_map.get(group, "gray")
            start_ts = pd.Timestamp(row["start"])
            end_ts = pd.Timestamp(row["end"])
            progress_ts = pd.Timestamp(row["progress_end"])
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

            if progress_val < 100:
                remain_start = progress_ts if progress_val > 0 else start_ts
                remain_duration_ms = (end_ts - remain_start).total_seconds() * 1000

                fig.add_trace(go.Bar(
                    base=remain_start,
                    x=[remain_duration_ms],
                    y=[task_name],
                    orientation="h",
                    marker=dict(color=color, line=dict(width=0)),
                    opacity=0.3,
                    hovertemplate=hovertemplate,
                    legendgroup=group,
                    showlegend=False,
                    width=0.6,
                ))

            if progress_val > 0:
                completed_duration_ms = (progress_ts - start_ts).total_seconds() * 1000

                show_legend = group not in legend_shown
                if show_legend:
                    legend_shown.add(group)

                fig.add_trace(go.Bar(
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
                ))

        fig.update_layout(
            title=dict(text=project_name, font=dict(size=18)),
            barmode="overlay",
        )
    else:
        fig = px.timeline(
            df,
            x_start="start",
            x_end="end",
            y="name",
            color="group",
            hover_data={
                "start": True,
                "end": True,
                "status": True,
                "progress": True,
                "depends_on": True,
                "name": False,
                "group": False,
            },
            title=dict(text=project_name, font=dict(size=18)),
            color_discrete_map=group_color_map,
        )

    fig.update_yaxes(autorange="reversed", type="category", title=None, tickfont=dict(size=14))

    today = pd.Timestamp.now().normalize()
    x_min = df["start"].min() - pd.Timedelta(days=2)
    x_max = df["end"].max() + pd.Timedelta(days=2)

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
            y=1.02,
            xref="x",
            yref="paper",
            text=today_label,
            showarrow=False,
            font=dict(size=12, color="#d62728"),
            xanchor="left",
        )

    height = max(520, 70 * len(df) + 180)
    fig.update_layout(
        height=height,
        bargap=0.4,
        margin=dict(l=140, r=40, t=80, b=80),
        font=dict(size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="right",
            x=1,
            font=dict(size=12),
        ),
    )

    return fig
