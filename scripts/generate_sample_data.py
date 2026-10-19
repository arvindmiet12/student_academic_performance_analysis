from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "student_performance.csv"


def generate_data(rows: int = 480, seed: int = 42) -> pd.DataFrame:
    if rows < 40:
        raise ValueError("Generate at least 40 rows for meaningful model evaluation.")
    rng = np.random.default_rng(seed)
    grades = rng.choice([9, 10, 11, 12], size=rows)
    schools = rng.choice(
        ["Northview High", "Riverside Academy", "Westfield School", "Central High"],
        size=rows,
        p=[.29, .25, .24, .22],
    )
    gender = rng.choice(["Female", "Male"], size=rows)
    parent_education = rng.choice(
        ["High school", "Some college", "Bachelor's", "Graduate"],
        size=rows,
        p=[.24, .28, .34, .14],
    )
    internet = rng.choice(["Yes", "No"], size=rows, p=[.87, .13])
    attendance = np.clip(rng.normal(88, 9, rows), 48, 100)
    assignments = np.clip(rng.normal(82, 13, rows), 30, 100)
    study_hours = np.clip(rng.normal(8.2, 3.2, rows), 1, 20)
    previous_score = np.clip(rng.normal(70, 14, rows), 25, 99)
    parent_effect = pd.Series(parent_education).map(
        {"High school": -2.5, "Some college": 0, "Bachelor's": 2.0, "Graduate": 3.5}
    ).to_numpy()
    school_effect = pd.Series(schools).map(
        {"Northview High": 2.0, "Riverside Academy": 0.5, "Westfield School": -1.5, "Central High": 0}
    ).to_numpy()
    internet_effect = np.where(internet == "Yes", 1.5, -2.5)
    noise = rng.normal(0, 8.5, rows)
    final_score = np.clip(
        0.34 * previous_score
        + 0.20 * attendance
        + 0.15 * assignments
        + 1.15 * study_hours
        + parent_effect
        + school_effect
        + internet_effect
        + 10
        + noise,
        25,
        100,
    )
    months = rng.integers(0, 12, size=rows)
    assessment_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(months * 30, unit="D")
    enrollment_year = rng.choice([2020, 2021, 2022, 2023, 2024], size=rows, p=[.12, .16, .19, .23, .30])

    return pd.DataFrame(
        {
            "student_id": [f"STU-{i + 1:04d}" for i in range(rows)],
            "school": schools,
            "grade": grades,
            "gender": gender,
            "study_hours": np.round(study_hours, 1),
            "attendance_rate": np.round(attendance, 1),
            "assignment_completion": np.round(assignments, 1),
            "parent_education": parent_education,
            "internet_access": internet,
            "previous_score": np.round(previous_score, 1),
            "final_score": np.round(final_score, 1),
            "assessment_date": assessment_dates.strftime("%Y-%m-%d"),
            "enrollment_year": enrollment_year,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic student performance dataset.")
    parser.add_argument("--rows", type=int, default=480, help="Number of synthetic student records.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path.")
    args = parser.parse_args()
    data = generate_data(rows=args.rows, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    print(f"Wrote {len(data):,} synthetic student records to {args.output}")


if __name__ == "__main__":
    main()
