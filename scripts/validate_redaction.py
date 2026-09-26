import sys
from collections import Counter
from pathlib import Path
import re

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader


INPUT_PATH = Path("input/RHP.docx")
OUTPUT_PATH = Path("output/Red_Herring_Prospectus_REDACTED.docx")


def normalize(text: str) -> str:
    """Normalize text for robust comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_phone(text: str) -> str:
    """Normalize phone numbers to digits only."""
    return re.sub(r"\D", "", text)


def is_phone(entity_type: str) -> bool:
    return entity_type == "PHONE_NUMBER"


def entity_still_exists(entity, redacted_text: str) -> bool:
    """Check whether an original entity value survived redaction."""

    original = entity.original_text

    if is_phone(entity.entity_type):
        original_normalized = normalize_phone(original)

        if len(original_normalized) < 10:
            return False

        redacted_digits = normalize_phone(redacted_text)
        return original_normalized in redacted_digits

    return normalize(original) in normalize(redacted_text)


def main():
    print("=" * 65)
    print("PII REDACTION VALIDATION")
    print("=" * 65)

    # ---------------------------------------------------------
    # 1. Verify output exists
    # ---------------------------------------------------------
    print("\n[1/5] Checking output file...")

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Redacted document not found: {OUTPUT_PATH}"
        )

    print(f"      Found: {OUTPUT_PATH}")

    # ---------------------------------------------------------
    # 2. Read original document
    # ---------------------------------------------------------
    print("\n[2/5] Reading original document...")

    original_reader = DocxReader(INPUT_PATH)
    original_blocks = original_reader.extract_blocks()

    print(f"      Original blocks: {len(original_blocks)}")

    # ---------------------------------------------------------
    # 3. Detect original PII
    # ---------------------------------------------------------
    print("\n[3/5] Detecting original PII...")

    pipeline = PIIDetectionPipeline()
    original_entities = pipeline.detect(original_blocks)

    print(f"      Original PII occurrences: {len(original_entities)}")

    # ---------------------------------------------------------
    # 4. Read redacted document
    # ---------------------------------------------------------
    print("\n[4/5] Reading redacted document...")

    redacted_reader = DocxReader(OUTPUT_PATH)
    redacted_blocks = redacted_reader.extract_blocks()

    print(f"      Redacted blocks: {len(redacted_blocks)}")

    original_text = "\n".join(
        block.text for block in original_blocks
    )

    redacted_text = "\n".join(
        block.text for block in redacted_blocks
    )

    # ---------------------------------------------------------
    # 5. Check PII leakage
    # ---------------------------------------------------------
    print("\n[5/5] Checking for original PII leakage...")

    leaks = []

    for entity in original_entities:
        if entity_still_exists(entity, redacted_text):
            leaks.append(entity)

    leak_counts = Counter(
        entity.entity_type
        for entity in leaks
    )

    print("\n" + "-" * 65)
    print("VALIDATION RESULT")
    print("-" * 65)

    print(f"Original PII occurrences : {len(original_entities)}")
    print(f"PII values still present : {len(leaks)}")

    if leaks:
        print("\n❌ PII LEAKAGE DETECTED")

        print("\nLeaks by category:")
        for entity_type, count in sorted(leak_counts.items()):
            print(f"  {entity_type:<20} {count}")

        print("\nFirst 20 leaked values:")

        for entity in leaks[:20]:
            print(
                f"  [{entity.entity_type}] "
                f"{entity.original_text!r}"
            )

        raise SystemExit(1)

    print("\n✅ NO ORIGINAL PII LEAKAGE DETECTED")

    # ---------------------------------------------------------
    # Structural validation
    # ---------------------------------------------------------
    print("\nStructural validation:")

    original_document = original_reader.load()
    redacted_document = redacted_reader.load()

    original_tables = len(original_document.tables)
    redacted_tables = len(redacted_document.tables)

    original_paragraphs = len(original_document.paragraphs)
    redacted_paragraphs = len(redacted_document.paragraphs)

    print(
        f"  Body paragraphs : "
        f"{original_paragraphs} → {redacted_paragraphs}"
    )

    print(
        f"  Tables          : "
        f"{original_tables} → {redacted_tables}"
    )

    if original_tables != redacted_tables:
        raise SystemExit(
            "\n❌ Table count changed during anonymization."
        )

    if original_paragraphs != redacted_paragraphs:
        raise SystemExit(
            "\n❌ Body paragraph count changed during anonymization."
        )

    print("\n✅ Document structure preserved.")

    print("\n" + "=" * 65)
    print("VALIDATION PASSED")
    print("=" * 65)


if __name__ == "__main__":
    main()