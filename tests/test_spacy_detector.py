from src.detector.spacy_detector import SpacyDetector


def test_detects_person():
    detector = SpacyDetector()

    results = detector.detect(
        "Barack Obama visited the office.",
        block_index=0,
    )

    assert any(
        entity.entity_type == "PERSON"
        and "Obama" in entity.original_text
        for entity in results
    )
   


def test_detects_organization():
    detector = SpacyDetector()

    results = detector.detect(
        "KSH International Limited is our Company.",
        block_index=0,
    )

    assert any(
        entity.entity_type == "ORGANIZATION"
        and "KSH International" in entity.original_text
        for entity in results
    )


def test_ignores_unmapped_entity_types():
    detector = SpacyDetector()

    results = detector.detect(
        "The company was incorporated in Pune.",
        block_index=0,
    )

    assert all(
        entity.entity_type
        in {
            "PERSON",
            "ORGANIZATION",
            "LOCATION",
        }
        for entity in results
    )