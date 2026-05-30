import pandas as pd
import yaml
from typing import Optional


def split_pipe_row(line: str) -> list[str]:
    parts = [p.strip() for p in line.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def parse_table_text(text: str) -> pd.DataFrame:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    if not lines:
        raise ValueError("Please input task data.")

    if "|" not in lines[0]:
        raise ValueError("Invalid table format. Use pipe (|) separated values.")

    header_parts = split_pipe_row(lines[0])

    expected_headers = ["任务名", "开始", "结束", "分组", "状态", "进度", "依赖"]
    if not all(h in header_parts for h in expected_headers[:3]):
        raise ValueError("Missing required columns: 任务名, 开始, 结束")

    tasks = []
    for line in lines[1:]:
        parts = split_pipe_row(line)

        if len(parts) < 3:
            continue

        parts = (parts + [""] * 7)[:7]

        task = {
            "name": parts[0] if len(parts) > 0 else "",
            "start": parts[1] if len(parts) > 1 else "",
            "end": parts[2] if len(parts) > 2 else "",
            "group": parts[3] or "General",
            "status": parts[4] or "pending",
            "progress": parts[5] or "0",
            "depends_on": parts[6] or "",
        }
        tasks.append(task)

    if not tasks:
        raise ValueError("No valid tasks found in input.")

    df = pd.DataFrame(tasks)
    return normalize_tasks(df)


def parse_yaml_text(text: str) -> pd.DataFrame:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {str(e)}")

    if not data or "tasks" not in data:
        raise ValueError("YAML must contain 'tasks' field.")

    tasks = data["tasks"]
    if not tasks:
        raise ValueError("No tasks found in YAML.")

    df = pd.DataFrame(tasks)

    column_mapping = {
        "name": "name",
        "start": "start",
        "end": "end",
        "group": "group",
        "status": "status",
        "progress": "progress",
        "depends_on": "depends_on",
    }

    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    for col in ["group", "status", "progress", "depends_on"]:
        if col not in df.columns:
            if col == "group":
                df[col] = "General"
            elif col == "status":
                df[col] = "pending"
            elif col == "progress":
                df[col] = 0
            elif col == "depends_on":
                df[col] = ""

    return normalize_tasks(df)


def normalize_tasks(df: pd.DataFrame) -> pd.DataFrame:
    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["end"] = pd.to_datetime(df["end"], errors="coerce")

    mask_invalid_start = df["start"].isna()
    mask_invalid_end = df["end"].isna()

    if mask_invalid_start.any() or mask_invalid_end.any():
        invalid_tasks = df[mask_invalid_start | mask_invalid_end]["name"].tolist()
        raise ValueError(
            f"Invalid date format for tasks: {', '.join(invalid_tasks)}. Please use YYYY-MM-DD."
        )

    df["progress"] = (
        pd.to_numeric(df["progress"], errors="coerce").fillna(0).astype(int)
    )
    df["progress"] = df["progress"].clip(0, 100)

    valid_statuses = ["done", "active", "pending", "critical", "milestone"]
    df["status"] = df["status"].apply(lambda x: x if x in valid_statuses else "pending")

    df["group"] = df["group"].fillna("General").astype(str)
    df["depends_on"] = df["depends_on"].fillna("").astype(str)

    df["duration_days"] = (df["end"] - df["start"]).dt.days + 1

    return df
