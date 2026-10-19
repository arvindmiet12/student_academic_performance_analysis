from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

MODEL_NUMERIC_FEATURES = [
    "grade",
    "study_hours",
    "attendance_rate",
    "assignment_completion",
    "previous_score",
    "enrollment_year",
]
MODEL_CATEGORICAL_FEATURES = [
    "school",
    "gender",
    "parent_education",
    "internet_access",
]
SEGMENT_FEATURES = ["attendance_rate", "assignment_completion", "study_hours", "previous_score"]


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, MODEL_NUMERIC_FEATURES),
            ("categorical", categorical, MODEL_CATEGORICAL_FEATURES),
        ]
    )


def train_risk_models(data: pd.DataFrame) -> dict | None:
    """Train two baseline classifiers and return holdout metrics and importances."""
    features = data[MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES]
    target = data["at_risk"].astype(int)
    if target.nunique() < 2 or target.value_counts().min() < 2:
        return None
    try:
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.25,
            random_state=42,
            stratify=target,
        )
    except ValueError:
        return None

    estimators = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
        ),
    }
    metrics: dict[str, dict[str, float]] = {}
    fitted: dict[str, Pipeline] = {}
    for name, estimator in estimators.items():
        model = Pipeline([("preprocessor", _preprocessor()), ("classifier", estimator)])
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        metrics[name] = {
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
        }
        fitted[name] = model

    best_model = max(metrics, key=lambda name: metrics[name]["f1"])
    forest = fitted["Random Forest"]
    transformed_names = forest.named_steps["preprocessor"].get_feature_names_out()
    importance = pd.DataFrame(
        {
            "feature": [name.split("__", 1)[-1].replace("_", " ").title() for name in transformed_names],
            "importance": forest.named_steps["classifier"].feature_importances_,
        }
    ).groupby("feature", as_index=False)["importance"].sum().sort_values("importance", ascending=False)
    return {
        "metrics": metrics,
        "best_model": best_model,
        "feature_importance": importance,
        "test_size": len(y_test),
    }


def cluster_students(data: pd.DataFrame, n_clusters: int = 4) -> tuple[pd.DataFrame, float | None]:
    """Add reproducible K-means engagement segments to a copy of the data."""
    result = data.copy()
    cluster_count = min(n_clusters, max(2, len(result) // 2))
    features = result[SEGMENT_FEATURES]
    scaled = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=cluster_count, n_init=10, random_state=42).fit_predict(scaled)
    result["segment"] = pd.Series(labels, index=result.index).map(
        lambda value: f"Segment {value + 1}"
    )
    score = silhouette_score(scaled, labels) if len(set(labels)) > 1 and len(result) > cluster_count else None
    return result, score
