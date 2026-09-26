import sys
from collections import Counter
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.anonymizer.anonymizer import Anonymizer
from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader
from src.document.writer import DocxWriter


INPUT_PATH = Path("input/RHP.docx")
OUTPUT_PATH = Path("output/Red_Herring_Prospectus_REDACTED.docx")


def main():
    print("=" * 60)
    print("PII ANONYMIZATION PIPELINE")
    print("=" * 60)

    # 1. Read document
    print("\n[1/5] Reading document...")
    reader = DocxReader(INPUT_PATH)
    blocks = reader.extract_blocks()

    print(f"      Text blocks: {len(blocks)}")

    # 2. Detect PII
    print("\n[2/5] Detecting PII...")
    pipeline = PIIDetectionPipeline()
    entities = pipeline.detect(blocks)

    print(f"      Total detections: {len(entities)}")

    counts = Counter(entity.entity_type for entity in entities)

    for entity_type, count in sorted(counts.items()):
        print(f"      {entity_type}: {count}")

    # 3. Generate synthetic replacements
    print("\n[3/5] Generating synthetic replacements...")
    anonymizer = Anonymizer()
    replacements = anonymizer.anonymize_entities(entities)

    print(f"      Replacements generated: {len(replacements)}")

    # 4. Write redacted document
    print("\n[4/5] Writing redacted document...")
    writer = DocxWriter(INPUT_PATH)
    writer.save(
        output_path=OUTPUT_PATH,
        entities=entities,
        replacements=replacements,
        mapping=anonymizer.get_raw_mapping(),
    )

    print(f"      Output: {OUTPUT_PATH}")

    # 5. Summary
    print("\n[5/5] Pipeline completed.")
    print("\nDetection summary:")

    for entity_type, count in sorted(counts.items()):
        print(f"  {entity_type:<20} {count}")

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()