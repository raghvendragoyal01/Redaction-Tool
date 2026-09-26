from dataclasses import dataclass
from typing import Sequence


@dataclass
class MetricScore:
    """Precision, Recall, and F1 score representation."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        total_predicted = self.true_positives + self.false_positives
        if total_predicted == 0:
            return 1.0 if self.false_negatives == 0 else 0.0
        return self.true_positives / total_predicted

    @property
    def recall(self) -> float:
        total_actual = self.true_positives + self.false_negatives
        if total_actual == 0:
            return 1.0 if self.false_positives == 0 else 0.0
        return self.true_positives / total_actual

    @property
    def f1_score(self) -> float:
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return (2 * p * r) / (p + r)

    def to_dict(self) -> dict:
        return {
            "tp": self.true_positives,
            "fp": self.false_positives,
            "fn": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
        }


def calculate_category_metrics(
    predictions: Sequence[str],
    ground_truth: Sequence[str],
    normalize_fn=None,
) -> MetricScore:
    """
    Calculate precision, recall, and F1 given prediction strings and ground truth strings.
    """
    if normalize_fn is None:
        normalize_fn = lambda s: s.strip().lower()

    pred_set = {normalize_fn(p) for p in predictions if p}
    gt_set = {normalize_fn(g) for g in ground_truth if g}

    tp = len(pred_set & gt_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)

    return MetricScore(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )
