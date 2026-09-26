import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.document.reader import DocxReader
from src.detector.spacy_detector import SpacyDetector


INPUT_FILE = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)


reader = DocxReader(INPUT_FILE)
blocks = reader.extract_blocks()

detector = SpacyDetector()

print("\n" + "=" * 90)
print("SPACY PROSPECTUS INSPECTION")
print("=" * 90)

total_entities = 0

for block in blocks:

    entities = detector.detect(
        text=block.text,
        block_index=block.index,
    )

    if not entities:
        continue

    total_entities += len(entities)

    print(
        f"\nBLOCK {block.index} | "
        f"{block.block_type} | "
        f"{block.location}"
    )

    print(f"TEXT: {block.text[:250]}")

    for entity in entities:
        print(
            f"  → {entity.entity_type:<15} "
            f"{entity.original_text!r}"
        )

print("\n" + "=" * 90)
print(f"TOTAL SPACY ENTITIES: {total_entities}")
print("=" * 90)