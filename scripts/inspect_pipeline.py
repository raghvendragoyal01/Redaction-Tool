import sys
from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
import re

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader


INPUT_FILE = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)
EVALUATION_DIR = Path("evaluation")

CATEGORIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "ORGANIZATION",
    "ADDRESS",
    "SSN",
    "CREDIT_CARD",
    "DATE_OF_BIRTH",
    "IP_ADDRESS",
]


def normalize_value(value: str) -> str:
    """Normalize text for unique-value counting."""
    return re.sub(r"\s+", " ", value.strip().lower())


def write_detection_audit(entities):
    """Write every detection to a CSV audit file."""

    output_file = EVALUATION_DIR / "detection_audit.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "entity_type",
            "original_text",
            "block_index",
            "start",
            "end",
            "confidence",
            "source",
        ])

        for entity in entities:
            writer.writerow([
                entity.entity_type,
                entity.original_text,
                entity.block_index,
                entity.start,
                entity.end,
                f"{entity.confidence:.4f}",
                entity.source,
            ])

    return output_file


def write_unique_entities(entities):
    """Write unique detected values and occurrence counts."""

    output_file = EVALUATION_DIR / "unique_entities.csv"

    grouped = defaultdict(Counter)

    for entity in entities:
        normalized = normalize_value(entity.original_text)
        grouped[entity.entity_type][normalized] += 1

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "entity_type",
            "normalized_value",
            "occurrences",
        ])

        for entity_type in CATEGORIES:
            for value, count in sorted(
                grouped[entity_type].items(),
                key=lambda item: (-item[1], item[0]),
            ):
                writer.writerow([
                    entity_type,
                    value,
                    count,
                ])

    return output_file


def is_suspicious(entity):
    """
    Flag detections that deserve manual review.

    This does NOT mean the detection is wrong.
    It simply identifies candidates for inspection.
    """

    value = entity.original_text.strip()
    normalized = value.lower()

    if entity.entity_type == "ORGANIZATION":

        suspicious_terms = {
            "advisory private limited",
            "pandit llp",
            "working capital",
            "anchor investors",
            "book running lead managers",
            "registrar of companies",
            "upi",
        }

        if normalized in suspicious_terms:
            return True

        if len(value.split()) <= 2:
            return True

    if entity.entity_type == "ADDRESS":

        suspicious_phrases = [
            "corporate office at",
            "registered office at",
            "phase ii",
            "located at",
        ]

        if any(
            phrase in normalized
            for phrase in suspicious_phrases
        ):
            return True

        if len(value.split()) < 6:
            return True

    if entity.entity_type == "PERSON":

        if len(value.split()) == 1:
            return True

    return False


def write_suspicious_detections(entities):
    """Write potentially questionable detections for manual review."""

    output_file = EVALUATION_DIR / "suspicious_detections.csv"

    suspicious = [
        entity
        for entity in entities
        if is_suspicious(entity)
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "entity_type",
            "original_text",
            "block_index",
            "start",
            "end",
            "confidence",
            "source",
        ])

        for entity in suspicious:
            writer.writerow([
                entity.entity_type,
                entity.original_text,
                entity.block_index,
                entity.start,
                entity.end,
                f"{entity.confidence:.4f}",
                entity.source,
            ])

    return output_file, len(suspicious)


def create_summary(entities, blocks):
    """Create machine-readable detection summary."""

    summary = {
        "input_file": str(INPUT_FILE),
        "text_blocks": len(blocks),
        "total_detections": len(entities),
        "categories": {},
    }

    for category in CATEGORIES:

        category_entities = [
            entity
            for entity in entities
            if entity.entity_type == category
        ]

        unique_values = {
            normalize_value(entity.original_text)
            for entity in category_entities
        }

        summary["categories"][category] = {
            "occurrences": len(category_entities),
            "unique_values": len(unique_values),
        }

    output_file = EVALUATION_DIR / "detection_summary.json"

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    return output_file, summary


def main():

    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("PII DETECTION SUMMARY")
    print("=" * 70)

    print(f"\nInput: {INPUT_FILE}")

    reader = DocxReader(INPUT_FILE)
    blocks = reader.extract_blocks()

    print(f"Text blocks: {len(blocks)}")

    print("\nRunning detection...")

    pipeline = PIIDetectionPipeline()
    entities = pipeline.detect(blocks)

    audit_file = write_detection_audit(entities)
    unique_file = write_unique_entities(entities)
    suspicious_file, suspicious_count = (
        write_suspicious_detections(entities)
    )
    summary_file, summary = create_summary(
        entities,
        blocks,
    )

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"\n{'CATEGORY':<20}"
        f"{'OCCURRENCES':>15}"
        f"{'UNIQUE':>12}"
    )

    print("-" * 70)

    for category in CATEGORIES:

        data = summary["categories"][category]

        print(
            f"{category:<20}"
            f"{data['occurrences']:>15}"
            f"{data['unique_values']:>12}"
        )

    print("-" * 70)

    print(
        f"{'TOTAL':<20}"
        f"{len(entities):>15}"
    )

    print("\n" + "=" * 70)
    print("AUDIT FILES")
    print("=" * 70)

    print(f"\nFull detection audit:")
    print(f"  {audit_file}")

    print(f"\nUnique entities:")
    print(f"  {unique_file}")

    print(f"\nSuspicious detections:")
    print(f"  {suspicious_file}")
    print(f"  Candidates for review: {suspicious_count}")

    print(f"\nMachine-readable summary:")
    print(f"  {summary_file}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()