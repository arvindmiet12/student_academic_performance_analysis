# Student Academic Performance Analysis Using Data Mining

An interactive Streamlit dashboard for exploring student outcomes, analyzing academic and engagement patterns, identifying student segments, and comparing early-warning risk models. The included sample dataset is synthetic and reproducible.

## Features

- **Descriptive analytics:** pass rate, average GPA estimate, attendance, score distributions, school and grade comparisons, enrollment trends, and student-level exploration.
- **Predictive analytics:** logistic regression and random forest classifiers evaluated on a stratified holdout set with accuracy, precision, recall, F1, and random-forest feature importance.
- **Unsupervised data mining:** K-means engagement segments with a silhouette score and segment profiles.
- **Interactive dashboard:** school, grade, and gender filters; CSV upload; searchable student table; filtered CSV export.
- **Responsible-use note:** sample records are synthetic; model predictions are decision-support signals, not automated decisions.

## Project structure

```text
student_analysis/
├── app.py
├── data/
│   └── student_performance.csv
├── scripts/
│   ├── generate_sample_data.py
│   └── create_project_presentation.py
├── assets/
│   └── dashboard_screenshot.png
├── student_analytics/
│   ├── __init__.py
│   ├── analysis.py
│   └── data.py
├── tests/
│   └── test_analysis.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Requirements

- Python 3.10 or newer
- pip

## Setup and run

Open a terminal in the project directory. On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard opens at the local URL printed by Streamlit (typically `http://localhost:8501`).

## Project presentation

The PowerPoint deck includes a screenshot of the Streamlit dashboard, the project workflow, model results, segment profiles, setup instructions, and responsible-use notes.

```powershell
python scripts/create_project_presentation.py
```

This creates `Student_Academic_Performance_Analysis.pptx` in the project root. The deck is also included in the project deliverables.

## Sample data

`data/student_performance.csv` contains 480 generated records. Recreate it with:

```powershell
python scripts/generate_sample_data.py
```

Optional generator arguments:

```powershell
python scripts/generate_sample_data.py --rows 800 --seed 7 --output data\student_performance.csv
```

Uploaded CSVs must include these columns:

| Column | Meaning |
| --- | --- |
| `student_id` | Unique student identifier |
| `school` | School name |
| `grade` | Grade level, 1–12 |
| `gender` | Student gender category |
| `study_hours` | Study hours per week |
| `attendance_rate` | Attendance percentage, 0–100 |
| `assignment_completion` | Completed assignments percentage, 0–100 |
| `parent_education` | Parent/guardian education category |
| `internet_access` | Internet access category |
| `previous_score` | Previous assessment score, 0–100 |
| `final_score` | Current final score, 0–100 |
| `assessment_date` | Assessment date in a parseable date format |
| `enrollment_year` | Enrollment year |

The app derives `pass_status` (score ≥ 60) and `at_risk` (score < 60 or attendance < 70) from the uploaded data.

## Analytical approach

1. **Data validation and preparation:** validates required columns, numeric ranges, and dates; derives outcome labels.
2. **Descriptive analysis:** aggregates outcomes by grade, school, month, and enrollment year.
3. **Risk classification:** predicts the derived at-risk label using study habits, attendance, prior score, school, and demographic/context categories. Final score and the derived target are excluded from model inputs. Metrics are calculated on a stratified test split.
4. **Clustering:** standardizes attendance, assignment completion, study hours, and prior score before fitting reproducible K-means segments.

These models are educational examples, not validated tools for consequential decisions. Do not upload identifiable or sensitive student information unless you have appropriate authorization, consent, and safeguards. Assess bias and validate performance on representative data before deployment.

## Tests

Run the project tests from the project root:

```powershell
python -m unittest discover -s tests -v
```
