import pandas as pd
from typing import List


def validate_tasks(df: pd.DataFrame) -> List[str]:
    errors = []
    warnings = []

    if df.empty:
        errors.append("No tasks to validate.")
        return errors

    for idx, row in df.iterrows():
        task_name = row.get("name", f"Task {idx}")

        if pd.isna(row["name"]) or str(row["name"]).strip() == "":
            errors.append(f"Row {idx + 1}: Task name is empty.")

        if pd.isna(row["start"]):
            errors.append(f"Task '{task_name}': Start date is empty.")

        if pd.isna(row["end"]):
            errors.append(f"Task '{task_name}': End date is empty.")

        if not pd.isna(row["start"]) and not pd.isna(row["end"]):
            if row["end"] < row["start"]:
                errors.append(
                    f"Task '{task_name}': End date cannot be earlier than start date."
                )

        if not pd.isna(row.get("progress")):
            progress = row["progress"]
            if progress < 0 or progress > 100:
                errors.append(
                    f"Task '{task_name}': Progress must be between 0 and 100."
                )

        if row.get("status") not in [
            "done",
            "active",
            "pending",
            "critical",
            "milestone",
        ]:
            errors.append(f"Task '{task_name}': Invalid status '{row['status']}'.")

    task_names = set(df["name"].dropna().tolist())
    duplicate_names = df[df.duplicated(subset=["name"], keep=False)]["name"].unique()
    if len(duplicate_names) > 0:
        errors.append(f"Duplicate task names found: {', '.join(duplicate_names)}")

    for idx, row in df.iterrows():
        depends_on = row.get("depends_on", "")
        if depends_on and str(depends_on).strip() != "":
            if depends_on not in task_names:
                warnings.append(f"Warning: dependency task not found: {depends_on}")

    return errors + warnings
