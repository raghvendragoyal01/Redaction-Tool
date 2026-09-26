from pathlib import Path

from src.detector.presidio_detector import PresidioDetector
from src.document.reader import DocxReader


INPUT_FILE = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)


def test_presidio_detects_email():
    detector = PresidioDetector()

    text = "Contact us at test@example.com"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    entities = {
        result.entity_type
        for result in results
    }

    assert "EMAIL_ADDRESS" in entities


def test_presidio_detects_real_prospectus_email():
    reader = DocxReader(INPUT_FILE)

    blocks = reader.extract_blocks()

    detector = PresidioDetector()

    all_entities = []

    for block in blocks:
        entities = detector.detect(
            text=block.text,
            block_index=block.index,
        )

        all_entities.extend(entities)

    emails = [
        entity
        for entity in all_entities
        if entity.entity_type == "EMAIL_ADDRESS"
    ]

    assert emails

    print("\nDetected emails:")

    for email in emails[:10]:
        print(
            f"  {email.original_text} "
            f"(confidence={email.confidence:.2f}, "
            f"block={email.block_index})"
        )