from __future__ import annotations

import unittest

import pandas as pd

from scripts.generate_sample_data import generate_data
from student_analytics.analysis import cluster_students, train_risk_models
from student_analytics.data import validate_and_prepare


class StudentAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = validate_and_prepare(generate_data(rows=240, seed=17))

    def test_sample_data_is_reproducible(self) -> None:
        first = generate_data(rows=50, seed=5)
        second = generate_data(rows=50, seed=5)
        pd.testing.assert_frame_equal(first, second)

    def test_validation_derives_outcomes(self) -> None:
        self.assertEqual(set(self.data["pass_status"]), {"Pass", "Needs Support"})
        self.assertTrue(self.data["at_risk"].isin([True, False]).all())

    def test_validation_rejects_out_of_range_score(self) -> None:
        invalid = generate_data(rows=50)
        invalid.loc[0, "final_score"] = 120
        with self.assertRaisesRegex(ValueError, "final_score"):
            validate_and_prepare(invalid)

    def test_risk_models_return_holdout_metrics(self) -> None:
        results = train_risk_models(self.data)
        self.assertIsNotNone(results)
        assert results is not None
        self.assertIn(results["best_model"], {"Logistic Regression", "Random Forest"})
        self.assertEqual(set(results["metrics"]), {"Logistic Regression", "Random Forest"})
        for model_metrics in results["metrics"].values():
            self.assertTrue(all(0 <= value <= 1 for value in model_metrics.values()))
        self.assertFalse(results["feature_importance"].empty)

    def test_clustering_adds_segments_and_score(self) -> None:
        segmented, silhouette = cluster_students(self.data)
        self.assertIn("segment", segmented)
        self.assertGreaterEqual(segmented["segment"].nunique(), 2)
        self.assertIsNotNone(silhouette)
        assert silhouette is not None
        self.assertGreaterEqual(silhouette, -1)
        self.assertLessEqual(silhouette, 1)


if __name__ == "__main__":
    unittest.main()
