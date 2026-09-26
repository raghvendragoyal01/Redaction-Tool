import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader
from src.evaluation.evaluator import PIIEvaluator

INPUT_PATH = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)
REPORT_PATH = Path("evaluation/evaluation_report.md")


def main():
    print("=" * 65)
    print("PII EVALUATION & METRICS BENCHMARK")
    print("=" * 65)

    print(f"\n[1/4] Loading document: {INPUT_PATH}")
    reader = DocxReader(INPUT_PATH)
    blocks = reader.extract_blocks()
    print(f"      Total text blocks: {len(blocks)}")

    print("\n[2/4] Detecting PII entities...")
    pipeline = PIIDetectionPipeline()
    entities = pipeline.detect(blocks)
    print(f"      Total entities detected: {len(entities)}")

    print("\n[3/4] Evaluating against ground-truth benchmarks...")
    evaluator = PIIEvaluator()
    results = evaluator.evaluate(entities)

    print("\n" + "-" * 75)
    print(f"{'CATEGORY':<18} {'TP':>5} {'FP':>5} {'FN':>5} {'PRECISION':>12} {'RECALL':>10} {'F1 SCORE':>10}")
    print("-" * 75)

    for cat, score in sorted(results.items()):
        print(
            f"{cat:<18} {score.true_positives:>5} {score.false_positives:>5} {score.false_negatives:>5} "
            f"{score.precision:>11.2%} {score.recall:>9.2%} {score.f1_score:>9.2%}"
        )

    total_tp = sum(m.true_positives for m in results.values())
    total_fp = sum(m.false_positives for m in results.values())
    total_fn = sum(m.false_negatives for m in results.values())
    micro_prec = total_tp / max(1, (total_tp + total_fp))
    micro_rec = total_tp / max(1, (total_tp + total_fn))
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec) if (micro_prec + micro_rec) > 0 else 0.0

    print("-" * 75)
    print(
        f"{'OVERALL (MICRO)':<18} {total_tp:>5} {total_fp:>5} {total_fn:>5} "
        f"{micro_prec:>11.2%} {micro_rec:>9.2%} {micro_f1:>9.2%}"
    )
    print("-" * 75)

    print("\n[4/4] Generating evaluation report...")
    report_md = evaluator.generate_report_markdown(
        results=results,
        total_detections=len(entities),
        total_blocks=len(blocks),
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")
    print(f"      Saved report to: {REPORT_PATH}")

    print("\n" + "=" * 65)
    print("EVALUATION COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
