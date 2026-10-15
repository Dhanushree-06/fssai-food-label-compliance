"""
Unit Tests for Machine Learning Model and Dataset
"""

import os
import csv
from app.services.ml_classifier import ComplianceClassifier


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)


def test_dataset_exact_150_rows():
    """Verify that dataset.csv contains exactly 150 rows."""
    dataset_csv = os.path.join(DATA_DIR, "dataset.csv")
    assert os.path.exists(dataset_csv), f"dataset.csv not found at {dataset_csv}"

    rows = []
    with open(dataset_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 150, f"Expected exactly 150 rows, got {len(rows)}"

    # Check class distribution: 50 each
    classes = [r["compliance_status"] for r in rows]
    assert classes.count("COMPLIANT") == 50
    assert classes.count("PARTIALLY_COMPLIANT") == 50
    assert classes.count("NON_COMPLIANT") == 50


def test_model_artifacts_exist():
    """Verify that model and vectorizer joblib files exist."""
    model_path = os.path.join(DATA_DIR, "fssai_lr_model.joblib")
    vec_path = os.path.join(DATA_DIR, "tfidf_vectorizer.joblib")
    metrics_path = os.path.join(DATA_DIR, "ml_metrics.json")

    assert os.path.exists(model_path)
    assert os.path.exists(vec_path)
    assert os.path.exists(metrics_path)


def test_model_metrics_integrity():
    """Verify that reported test metrics are mathematically valid."""
    metrics = ComplianceClassifier.get_metrics()
    assert "test_accuracy" in metrics
    assert "test_precision" in metrics
    assert "test_recall" in metrics
    assert "test_f1" in metrics
    assert "confusion_matrix" in metrics

    assert 0.0 <= metrics["test_accuracy"] <= 1.0
    assert 0.0 <= metrics["test_precision"] <= 1.0
    assert 0.0 <= metrics["test_recall"] <= 1.0
    assert 0.0 <= metrics["test_f1"] <= 1.0
    assert len(metrics["confusion_matrix"]) == 3


def test_model_prediction_inference():
    """Verify model prediction on compliant and defective texts."""
    compliant_text = (
        "Ingredients: Whole Wheat Flour, Water, Yeast, Salt. "
        "Nutrition: Energy 245 kcal, Protein 8.5g, Fat 2.1g. "
        "Green vegetarian logo. Net Wt: 400g. MRP: Rs 50 incl of taxes. "
        "FSSAI Lic. No. 10019064001234. Batch: WBD402. Best Before 5 days."
    )
    pred_res = ComplianceClassifier.predict(compliant_text)
    assert "prediction" in pred_res
    assert "confidence" in pred_res
    assert pred_res["prediction"] in ["COMPLIANT", "PARTIALLY_COMPLIANT", "NON_COMPLIANT"]
    assert 0.0 <= pred_res["confidence"] <= 1.0

    # Defective label
    defective_text = "Flour, butter, sugar. Price 20. FSSAI: None. Batch: None. Expiry: Missing."
    def_res = ComplianceClassifier.predict(defective_text)
    assert def_res["prediction"] in ["NON_COMPLIANT", "PARTIALLY_COMPLIANT"]
