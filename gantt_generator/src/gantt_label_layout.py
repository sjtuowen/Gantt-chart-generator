import pandas as pd


LABEL_INSIDE = "inside"
LABEL_ABOVE = "above"


def task_label_fits_bar(label: str, duration_days: float) -> bool:
    estimated_days_needed = max(1.6, min(8.0, len(label) * 0.24))
    return duration_days >= estimated_days_needed


def get_task_label_position(df: pd.DataFrame) -> str:
    if "plot_end" not in df.columns:
        plot_end = df["end"] + pd.Timedelta(days=1)
    else:
        plot_end = df["plot_end"]

    is_milestone = df["status"].astype(str).str.lower() == "milestone"
    normal_df = df[~is_milestone].copy()
    if normal_df.empty:
        return LABEL_ABOVE

    normal_plot_end = plot_end.loc[normal_df.index]
    durations = (normal_plot_end - normal_df["start"]).dt.total_seconds() / 86400

    all_fit = all(
        task_label_fits_bar(str(label), duration_days)
        for label, duration_days in zip(normal_df["name"], durations)
    )
    return LABEL_INSIDE if all_fit else LABEL_ABOVE
