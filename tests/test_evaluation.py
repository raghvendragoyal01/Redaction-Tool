import pytest
from src.evaluation.metrics import MetricScore, calculate_category_metrics
from src.evaluation.evaluator import PIIEvaluator
from src.models import PIIEntity


def test_metric_score_calculations():
    # Perfect score
    score = MetricScore(true_positives=10, false_positives=0, false_negatives=0)
    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1_score == 1.0

    # Half precision
    score_half_prec = MetricScore(true_positives=5, false_positives=5, false_negatives=0)
    assert score_half_prec.precision == 0.5
    assert score_half_prec.recall == 1.0
    assert round(score_half_prec.f1_score, 4) == 0.6667

    # Half recall
    score_half_rec = MetricScore(true_positives=5, false_positives=0, false_negatives=5)
    assert score_half_rec.precision == 1.0
    assert score_half_rec.recall == 0.5
    assert round(score_half_rec.f1_score, 4) == 0.6667

    # Zero all
    score_zero = MetricScore(true_positives=0, false_positives=0, false_negatives=0)
    assert score_zero.precision == 1.0
    assert score_zero.recall == 1.0
    assert score_zero.f1_score == 0.0


def test_calculate_category_metrics():
    preds = ["Rajesh Hegde", "Sarthak Malvadkar", "Unknown Person"]
    ground_truth = ["Rajesh Hegde", "Sarthak Malvadkar", "Pushpa Hegde"]

    score = calculate_category_metrics(preds, ground_truth)
    assert score.true_positives == 2
    assert score.false_positives == 1
    assert score.false_negatives == 1
    assert round(score.precision, 4) == 0.6667
    assert round(score.recall, 4) == 0.6667
    assert round(score.f1_score, 4) == 0.6667


def test_pii_evaluator_report_generation():
    evaluator = PIIEvaluator()
    dummy_entities = [
        PIIEntity(
            entity_type="PERSON",
            original_text="Pushpa Kushal Hegde",
            start=0,
            end=19,
            confidence=1.0,
            source="test",
            block_index=0,
        ),
        PIIEntity(
            entity_type="EMAIL_ADDRESS",
            original_text="cs.connect@kshinternational.com",
            start=0,
            end=31,
            confidence=1.0,
            source="test",
            block_index=0,
        ),
    ]

    results = evaluator.evaluate(dummy_entities)
    assert "PERSON" in results
    assert "EMAIL_ADDRESS" in results
    assert results["PERSON"].true_positives >= 1
    assert results["EMAIL_ADDRESS"].true_positives >= 1

    report_md = evaluator.generate_report_markdown(
        results=results,
        total_detections=len(dummy_entities),
        total_blocks=10,
    )
    assert "# 📊 PII Redaction Evaluation Report" in report_md
    assert "Category-wise Performance Metrics" in report_md
