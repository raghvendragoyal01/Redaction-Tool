import sys
from collections import Counter
from pathlib import Path
import re

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader


INPUT_PATH = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)
OUTPUT_PATH = Path("output/Red_Herring_Prospectus_REDACTED.docx")


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_phone(text):
    return re.sub(r"\D", "", text)


def still_present(entity, redacted_text):
    if entity.entity_type == "PHONE_NUMBER":
        original = normalize_phone(entity.original_text)
        return original in normalize_phone(redacted_text)

    return normalize(entity.original_text) in normalize(redacted_text)


def main():
    pipeline = PIIDetectionPipeline()

    original_reader = DocxReader(INPUT_PATH)
    original_blocks = original_reader.extract_blocks()

    redacted_reader = DocxReader(OUTPUT_PATH)
    redacted_blocks = redacted_reader.extract_blocks()

    redacted_text = "\n".join(
        block.text for block in redacted_blocks
    )

    entities = pipeline.detect(original_blocks)

    leaks = [
        entity
        for entity in entities
        if still_present(entity, redacted_text)
    ]

    print("=" * 70)
    print("LEAKAGE LOCATION ANALYSIS")
    print("=" * 70)

    print(f"\nTotal original entities : {len(entities)}")
    print(f"Leaked entities         : {len(leaks)}")

    print("\nBy entity type:")

    type_counts = Counter(entity.entity_type for entity in leaks)

    for entity_type, count in sorted(type_counts.items()):
        print(f"  {entity_type:<20} {count}")

    print("\nBy block type:")

    block_lookup = {
        block.index: block
        for block in original_blocks
    }

    location_counts = Counter(
        block_lookup[entity.block_index].block_type
        for entity in leaks
    )

    for block_type, count in sorted(location_counts.items()):
        print(f"  {block_type:<20} {count}")

    print("\nFirst 30 leaked entities:")

    for entity in leaks[:30]:
        block = block_lookup[entity.block_index]

        print(
            f"\n[{entity.entity_type}] "
            f"{entity.original_text!r}"
        )
        print(f"  block index : {entity.block_index}")
        print(f"  block type  : {block.block_type}")
        print(f"  location    : {block.location}")
        print(f"  start/end   : {entity.start}/{entity.end}")
        print(f"  block text  : {block.text[:200]!r}")


if __name__ == "__main__":
    main()