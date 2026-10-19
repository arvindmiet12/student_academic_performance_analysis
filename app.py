from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from student_analytics.analysis import cluster_students, train_risk_models
from student_analytics.data import (
    REQUIRED_COLUMNS,
    load_sample_data,
    validate_and_prepare,
)

st.set_page_config(
    page_title="Education Analytics Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#102b4e"
BLUE = "#3b82d0"
GREEN = "#28a36a"
RED = "#d94f54"
TEAL = "#39a99b"
ORANGE = "#e99540"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f5f7fb; }
    section[data-testid="stSidebar"] { background: #102b4e; }
    section[data-testid="stSidebar"] * { color: #edf4ff; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 5px 0; }
    .dashboard-title { font-size: 2.05rem; font-weight: 800; color: #131b28; margin: 0 0 .15rem; }
    .dashboard-subtitle { color: #667085; margin: 0 0 1.2rem; }
    .metric-card { background: #fff; border: 1px solid #e7ebf1; border-radius: 15px;
      padding: 18px 20px; min-height: 124px; box-shadow: 0 6px 16px rgba(16, 43, 78, .07); }
    .metric-label { font-size: .93rem; font-weight: 600; color: #303846; }
    .metric-value { font-size: 2.25rem; line-height: 1.2; font-weight: 800; margin-top: 8px; }
    .metric-note { color: #687386; font-size: .82rem; margin-top: 3px; }
    .panel { background: #fff; border: 1px solid #e7ebf1; border-radius: 15px;
      padding: 16px 18px; box-shadow: 0 5px 14px rgba(16, 43, 78, .045); }
    .section-heading { color: #182230; font-size: 1.08rem; font-weight: 700; margin: 0 0 2px; }
    .section-caption { color: #768195; font-size: .84rem; margin: 0 0 10px; }
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def metric_card(label: str, value: str, color: str, note: str = "") -> None:
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        <div class="metric-note">{note}</div></div>""",
        unsafe_allow_html=True,
    )


def panel_heading(title: str, caption: str = "") -> None:
    st.markdown(
        f'<div class="section-heading">{title}</div>'
        f'<div class="section-caption">{caption}</div>',
        unsafe_allow_html=True,
    )


@st.cache_data
def get_sample_data() -> pd.DataFrame:
    return load_sample_data()


def style_chart(fig, height: int = 310):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#344054", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e4e7ec")
    fig.update_yaxes(gridcolor="#edf0f4", zeroline=False)
    return fig


def render_overview(data: pd.DataFrame) -> None:
    if data.empty:
        st.warning("No students match the current filters. Adjust the filters to continue.")
        return

    passed = data["pass_status"].eq("Pass").mean() * 100
    gpa = min(4.0, max(0.0, data["final_score"].mean() / 25))
    attendance = data["attendance_rate"].mean()
    at_risk = int(data["at_risk"].sum())

    cards = st.columns(4)
    with cards[0]:
        metric_card("Pass Rate", f"{passed:.0f}%", GREEN, "Students scoring 60 or above")
    with cards[1]:
        metric_card("Average GPA", f"{gpa:.2f}", BLUE, "Score mapped to a 4.0 scale")
    with cards[2]:
        metric_card("Attendance", f"{attendance:.0f}%", GREEN, "Average attendance rate")
    with cards[3]:
        metric_card("At-Risk Students", f"{at_risk:,}", RED, "Needs early academic support")

    st.write("")
    left, middle, right = st.columns([1.45, 1.08, 1.08])
    monthly = (
        data.assign(month=data["assessment_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["attendance_rate"]
        .mean()
        .sort_values("month")
    )
    with left:
        with st.container(border=True):
            panel_heading("Student Attendance Rate", "Monthly average · sample academic year")
            fig = px.line(
                monthly,
                x="month",
                y="attendance_rate",
                markers=True,
                color_discrete_sequence=[BLUE],
                labels={"month": "", "attendance_rate": "Attendance (%)"},
            )
            fig.update_traces(line_width=3, marker_size=7, fill="tozeroy", fillcolor="rgba(59,130,208,.10)")
            fig.update_yaxes(range=[60, 100], ticksuffix="%")
            st.plotly_chart(style_chart(fig, 300), use_container_width=True)
    with middle:
        with st.container(border=True):
            panel_heading("Average Test Scores by Grade", "Current filtered students")
            grade_scores = data.groupby("grade", as_index=False)["final_score"].mean()
            fig = px.bar(
                grade_scores,
                x="grade",
                y="final_score",
                color="grade",
                color_discrete_sequence=[BLUE, TEAL, GREEN, ORANGE],
                text=grade_scores["final_score"].round().astype(int),
                labels={"grade": "Grade", "final_score": "Score"},
            )
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_yaxes(range=[0, 110], title="")
            fig.update_layout(showlegend=False)
            st.plotly_chart(style_chart(fig, 300), use_container_width=True)
    with right:
        with st.container(border=True):
            panel_heading("Enrollment Trend", "Student records by enrollment year")
            enrollments = data.groupby("enrollment_year", as_index=False).size()
            fig = px.area(
                enrollments,
                x="enrollment_year",
                y="size",
                markers=True,
                color_discrete_sequence=[ORANGE],
                labels={"enrollment_year": "", "size": "Students"},
            )
            fig.update_traces(line_width=3, fillcolor="rgba(233,149,64,.16)")
            st.plotly_chart(style_chart(fig, 300), use_container_width=True)

    st.write("")
    col_a, col_b = st.columns([1.15, 1])
    with col_a:
        with st.container(border=True):
            panel_heading("Score Distribution", "Final assessment scores")
            fig = px.histogram(
                data,
                x="final_score",
                color="pass_status",
                nbins=20,
                barmode="overlay",
                opacity=.78,
                color_discrete_map={"Pass": GREEN, "Needs Support": RED},
                labels={"final_score": "Final score", "pass_status": "Outcome"},
            )
            st.plotly_chart(style_chart(fig, 270), use_container_width=True)
    with col_b:
        with st.container(border=True):
            panel_heading("School Performance", "Average final score by school")
            schools = data.groupby("school", as_index=False)["final_score"].mean().sort_values("final_score")
            fig = px.bar(
                schools,
                x="final_score",
                y="school",
                orientation="h",
                color="final_score",
                color_continuous_scale=["#ef9a9a", "#f6c85f", "#35a875"],
                labels={"final_score": "Average score", "school": ""},
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig, 270), use_container_width=True)


def render_students(data: pd.DataFrame) -> None:
    st.subheader("Student Explorer")
    st.caption("Search, sort, and export the students included by your current filters.")
    search = st.text_input("Search student ID or school", placeholder="e.g. STU-0001 or North")
    table = data.copy()
    if search.strip():
        matches = table["student_id"].astype(str).str.contains(search, case=False, na=False)
        matches |= table["school"].astype(str).str.contains(search, case=False, na=False)
        table = table[matches]

    display_columns = [
        "student_id", "school", "grade", "gender", "attendance_rate", "study_hours",
        "assignment_completion", "previous_score", "final_score", "pass_status", "at_risk",
    ]
    st.dataframe(
        table[display_columns].rename(
            columns={
                "student_id": "Student ID", "school": "School", "grade": "Grade",
                "gender": "Gender", "attendance_rate": "Attendance %",
                "study_hours": "Study hours / week", "assignment_completion": "Assignments %",
                "previous_score": "Previous score", "final_score": "Final score",
                "pass_status": "Outcome", "at_risk": "At risk",
            }
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Attendance %": st.column_config.ProgressColumn("Attendance %", min_value=0, max_value=100, format="%.0f%%"),
            "Assignments %": st.column_config.ProgressColumn("Assignments %", min_value=0, max_value=100, format="%.0f%%"),
            "At risk": st.column_config.CheckboxColumn("At risk"),
        },
    )
    st.download_button(
        "Download filtered students as CSV",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name="filtered_student_performance.csv",
        mime="text/csv",
    )


def render_risk_analysis(data: pd.DataFrame) -> None:
    st.subheader("Early-Warning Risk Analysis")
    st.caption(
        "A predictive classification model estimates the likelihood of a student needing support. "
        "Model inputs exclude final score and the derived risk label."
    )
    if len(data) < 30 or data["at_risk"].nunique() < 2 or data["at_risk"].value_counts().min() < 2:
        st.warning("At least 30 filtered students and both risk classes are needed to train and evaluate the model.")
        return

    with st.spinner("Training and evaluating baseline models…"):
        results = train_risk_models(data)
    if results is None:
        st.warning("The filtered data does not contain enough examples of each risk class for a reliable split.")
        return

    metrics = results["metrics"]
    best = results["best_model"]
    metric_columns = st.columns(4)
    with metric_columns[0]:
        metric_card("Best Model", best, BLUE, "Selected by test-set F1")
    with metric_columns[1]:
        metric_card("Accuracy", f"{metrics[best]['accuracy']:.1%}", GREEN, "Held-out test set")
    with metric_columns[2]:
        metric_card("Precision", f"{metrics[best]['precision']:.1%}", TEAL, "Predicted risks that are true")
    with metric_columns[3]:
        metric_card("Recall", f"{metrics[best]['recall']:.1%}", ORANGE, "At-risk students identified")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            panel_heading("Model Comparison", "Performance on the same stratified holdout")
            metric_frame = pd.DataFrame(metrics).T.reset_index(names="model")
            metric_long = metric_frame.melt(
                id_vars="model", value_vars=["accuracy", "precision", "recall", "f1"],
                var_name="metric", value_name="score",
            )
            fig = px.bar(
                metric_long,
                x="metric",
                y="score",
                color="model",
                barmode="group",
                range_y=[0, 1],
                color_discrete_sequence=[BLUE, GREEN],
                labels={"metric": "", "score": "Score", "model": "Model"},
            )
            st.plotly_chart(style_chart(fig, 330), use_container_width=True)
    with right:
        with st.container(border=True):
            panel_heading("Risk Drivers", "Random forest feature importance")
            importance = results["feature_importance"].head(10).sort_values("importance")
            fig = px.bar(
                importance,
                x="importance",
                y="feature",
                orientation="h",
                color_discrete_sequence=[TEAL],
                labels={"importance": "Relative importance", "feature": ""},
            )
            st.plotly_chart(style_chart(fig, 330), use_container_width=True)

    st.info(
        "Use these results as a decision-support signal, not as an automated judgment. "
        "The included dataset is synthetic; validate on representative, consented data before real-world use."
    )


def render_segments(data: pd.DataFrame) -> None:
    st.subheader("Student Segments")
    st.caption("Unsupervised K-means clustering groups students by learning and engagement patterns.")
    if len(data) < 8:
        st.warning("At least 8 students are required for segmentation.")
        return
    with st.spinner("Finding student engagement segments…"):
        segmented, silhouette = cluster_students(data)

    if silhouette is not None:
        st.metric("Silhouette score", f"{silhouette:.3f}", help="Higher values generally indicate more distinct clusters.")
    profile = segmented.groupby("segment", as_index=False).agg(
        students=("student_id", "count"),
        attendance=("attendance_rate", "mean"),
        assignments=("assignment_completion", "mean"),
        study_hours=("study_hours", "mean"),
        final_score=("final_score", "mean"),
        at_risk_rate=("at_risk", "mean"),
    )
    left, right = st.columns([1.25, 1])
    with left:
        with st.container(border=True):
            panel_heading("Engagement Map", "Attendance vs. assignment completion")
            fig = px.scatter(
                segmented,
                x="attendance_rate",
                y="assignment_completion",
                color="segment",
                size="study_hours",
                hover_data=["student_id", "grade", "final_score"],
                color_discrete_sequence=[BLUE, GREEN, ORANGE, RED, TEAL],
                labels={"attendance_rate": "Attendance (%)", "assignment_completion": "Assignments completed (%)"},
            )
            st.plotly_chart(style_chart(fig, 390), use_container_width=True)
    with right:
        with st.container(border=True):
            panel_heading("Segment Profiles", "Average engagement and outcomes")
            profile_view = profile.rename(
                columns={
                    "segment": "Segment", "students": "Students", "attendance": "Attendance %",
                    "assignments": "Assignments %", "study_hours": "Study hours",
                    "final_score": "Final score", "at_risk_rate": "At-risk %",
                }
            )
            profile_view["At-risk %"] *= 100
            st.dataframe(
                profile_view.style.format(
                    {"Attendance %": "{:.1f}", "Assignments %": "{:.1f}", "Study hours": "{:.1f}",
                     "Final score": "{:.1f}", "At-risk %": "{:.1f}%"}
                ),
                use_container_width=True,
                hide_index=True,
            )


def main() -> None:
    st.sidebar.markdown("## 🎓 Education\n### Analytics Dashboard")
    st.sidebar.caption("Student performance · Data mining")
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Students", "Risk Analysis", "Student Segments"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Data")
    uploaded = st.sidebar.file_uploader("Upload student CSV", type=["csv"])
    if uploaded is None:
        raw = get_sample_data()
        st.sidebar.caption(f"Using sample dataset · {len(raw):,} students")
    else:
        try:
            raw = pd.read_csv(uploaded)
            missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
            if missing:
                st.sidebar.error("Missing required columns: " + ", ".join(missing))
                st.stop()
            raw = validate_and_prepare(raw)
            st.sidebar.caption(f"Uploaded dataset · {len(raw):,} students")
        except (
            ValueError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
        ) as exc:
            st.sidebar.error(f"Could not read this dataset: {exc}")
            st.stop()

    st.sidebar.subheader("Filters")
    schools = sorted(raw["school"].dropna().astype(str).unique())
    grades = sorted(raw["grade"].dropna().unique())
    genders = sorted(raw["gender"].dropna().astype(str).unique())
    selected_schools = st.sidebar.multiselect("School", schools, default=schools)
    selected_grades = st.sidebar.multiselect("Grade", grades, default=grades)
    selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)
    filtered = raw[
        raw["school"].astype(str).isin(selected_schools)
        & raw["grade"].isin(selected_grades)
        & raw["gender"].astype(str).isin(selected_genders)
    ].copy()

    st.markdown('<div class="dashboard-title">Education Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-subtitle">Explore academic outcomes, identify early-warning signals, and understand student engagement.</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Showing {len(filtered):,} of {len(raw):,} students")

    if page == "Overview":
        render_overview(filtered)
    elif page == "Students":
        render_students(filtered)
    elif page == "Risk Analysis":
        render_risk_analysis(filtered)
    else:
        render_segments(filtered)

    st.sidebar.divider()
    st.sidebar.caption("For educational exploration only · Sample data is synthetic")


if __name__ == "__main__":
    main()
