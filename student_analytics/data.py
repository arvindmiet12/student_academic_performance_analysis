from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "student_performance.csv"

REQUIRED_COLUMNS = {
    "student_id",
    "school",
    "grade",
    "gender",
    "study_hours",
    "attendance_rate",
    "assignment_completion",
    "parent_education",
    "internet_access",
    "previous_score",
    "final_score",
    "assessment_date",
    "enrollment_year",
}

NUMERIC_COLUMNS = (
    "grade",
    "study_hours",
    "attendance_rate",
    "assignment_completion",
    "previous_score",
    "final_score",
    "enrollment_year",
)


def validate_and_prepare(data: pd.DataFrame) -> pd.DataFrame:
    """Validate the input schema and derive consistent outcome fields."""
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if data.empty:
        raise ValueError("The dataset contains no student records.")

    prepared = data.copy()
    for column in NUMERIC_COLUMNS:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise ValueError(f"Column '{column}' must contain numeric values without blanks.")

    for column in ("attendance_rate", "assignment_completion", "previous_score", "final_score"):
        if not prepared[column].between(0, 100).all():
            raise ValueError(f"Column '{column}' must contain values between 0 and 100.")
    if (prepared["study_hours"] < 0).any():
        raise ValueError("Column 'study_hours' cannot contain negative values.")
    if not prepared["grade"].between(1, 12).all():
        raise ValueError("Column 'grade' must contain values from 1 to 12.")

    prepared["assessment_date"] = pd.to_datetime(prepared["assessment_date"], errors="coerce")
    if prepared["assessment_date"].isna().any():
        raise ValueError("Column 'assessment_date' contains invalid dates.")
    for column in ("student_id", "school", "gender", "parent_education", "internet_access"):
        if prepared[column].isna().any() or prepared[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"Column '{column}' cannot contain blank values.")

    prepared["student_id"] = prepared["student_id"].astype(str)
    prepared["school"] = prepared["school"].astype(str)
    prepared["gender"] = prepared["gender"].astype(str)
    prepared["parent_education"] = prepared["parent_education"].astype(str)
    prepared["internet_access"] = prepared["internet_access"].astype(str)
    prepared["grade"] = prepared["grade"].astype(int)
    prepared["enrollment_year"] = prepared["enrollment_year"].astype(int)
    prepared["pass_status"] = prepared["final_score"].ge(60).map(
        {True: "Pass", False: "Needs Support"}
    )
    prepared["at_risk"] = prepared["final_score"].lt(60) | prepared["attendance_rate"].lt(70)
    return prepared.reset_index(drop=True)


def load_sample_data() -> pd.DataFrame:
    if not SAMPLE_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Sample data was not found at {SAMPLE_DATA_PATH}. "
            "Run `python scripts/generate_sample_data.py` to create it."
        )
    return validate_and_prepare(pd.read_csv(SAMPLE_DATA_PATH))
