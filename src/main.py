import argparse
from collections import Counter
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.anonymizer.anonymizer import Anonymizer
from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader
from src.document.writer import DocxWriter


DEFAULT_INPUT = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)
DEFAULT_OUTPUT = Path("output/Red_Herring_Prospectus_REDACTED.docx")


def redact_document(
    input_path: str | Path,
    output_path: str | Path,
    seed: int = 20260926,
) -> dict:
    input_path = Path(input_path)
    output_path = Path(output_path)

    print("=" * 60)
    print("PII REDACTION & ANONYMIZATION PIPELINE")
    print("=" * 60)

    # 1. Read document
    print(f"\n[1/4] Reading document: {input_path}...")
    reader = DocxReader(input_path)
    blocks = reader.extract_blocks()
    print(f"      Extracted {len(blocks)} text blocks.")

    # 2. Detect PII
    print("\n[2/4] Detecting PII entities...")
    pipeline = PIIDetectionPipeline()
    entities = pipeline.detect(blocks)
    print(f"      Total PII detected: {len(entities)}")

    counts = Counter(entity.entity_type for entity in entities)
    for entity_type, count in sorted(counts.items()):
        print(f"      - {entity_type:<18}: {count}")

    # 3. Generate synthetic replacements
    print("\n[3/4] Generating consistent synthetic replacements...")
    anonymizer = Anonymizer(seed=seed)
    replacements = anonymizer.anonymize_entities(entities)
    raw_mapping = anonymizer.get_raw_mapping()
    print(f"      Generated {len(replacements)} unique replacements.")

    # 4. Write redacted document
    print(f"\n[4/4] Writing redacted DOCX to: {output_path}...")
    writer = DocxWriter(input_path)
    writer.save(
        output_path=output_path,
        entities=entities,
        replacements=replacements,
        mapping=raw_mapping,
    )
    print(f"      Successfully saved redacted document: {output_path}")

    print("\n" + "=" * 60)
    print("REDACTION COMPLETE - ALL PII ANONYMIZED")
    print("=" * 60)

    return {
        "blocks": len(blocks),
        "entities": len(entities),
        "counts": dict(counts),
        "output": str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Redact and anonymize PII in financial DOCX documents."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to input DOCX file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to save redacted DOCX file",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=20260926,
        help="Random seed for reproducible synthetic data generation",
    )

    args = parser.parse_args()
    redact_document(
        input_path=args.input,
        output_path=args.output,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
