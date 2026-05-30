import pandas as pd
from io import BytesIO


def export_tasks_to_csv(df: pd.DataFrame) -> bytes:
    column_mapping = {
        "name": "Task",
        "start": "Start",
        "end": "End",
        "group": "Group",
        "status": "Status",
        "progress": "Progress",
        "depends_on": "Depends On",
        "duration_days": "Duration Days",
    }

    export_df = df[list(column_mapping.keys())].rename(columns=column_mapping)

    csv_buffer = BytesIO()
    csv_buffer.write(b"\xef\xbb\xbf")
    csv_buffer.write(export_df.to_csv(index=False).encode("utf-8"))

    return csv_buffer.getvalue()


def export_tasks_to_excel(df: pd.DataFrame) -> bytes:
    column_mapping = {
        "name": "Task",
        "start": "Start",
        "end": "End",
        "group": "Group",
        "status": "Status",
        "progress": "Progress",
        "depends_on": "Depends On",
        "duration_days": "Duration Days",
    }

    export_df = df[list(column_mapping.keys())].rename(columns=column_mapping)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Tasks", index=False)

    return output.getvalue()
