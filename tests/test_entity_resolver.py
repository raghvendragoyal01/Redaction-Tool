from src.detector.entity_resolver import EntityResolver
from src.models import PIIEntity


def make_entity(
    entity_type: str,
    text: str,
    start: int,
    end: int,
    confidence: float,
    source: str,
    block_index: int = 0,
) -> PIIEntity:

    return PIIEntity(
        entity_type=entity_type,
        original_text=text,
        start=start,
        end=end,
        confidence=confidence,
        source=source,
        block_index=block_index,
    )


def test_empty_entities():
    resolver = EntityResolver()

    result = resolver.resolve([])

    assert result == []


def test_keeps_non_overlapping_entities():
    resolver = EntityResolver()

    entities = [
        make_entity(
            "EMAIL_ADDRESS",
            "test@example.com",
            0,
            16,
            0.98,
            "presidio",
        ),
        make_entity(
            "PHONE_NUMBER",
            "+91 81081 14949",
            30,
            46,
            0.95,
            "presidio",
        ),
    ]

    result = resolver.resolve(entities)

    assert len(result) == 2


def test_removes_duplicate_detection():
    resolver = EntityResolver()

    entities = [
        make_entity(
            "EMAIL_ADDRESS",
            "test@example.com",
            0,
            16,
            0.98,
            "presidio",
        ),
        make_entity(
            "EMAIL_ADDRESS",
            "test@example.com",
            0,
            16,
            1.00,
            "regex",
        ),
    ]

    result = resolver.resolve(entities)

    assert len(result) == 1
    assert result[0].source == "regex"


def test_higher_confidence_wins():
    resolver = EntityResolver()

    entities = [
        make_entity(
            "PERSON",
            "Sarthak Malvadkar",
            0,
            18,
            0.70,
            "presidio",
        ),
        make_entity(
            "PERSON",
            "Sarthak Malvadkar",
            0,
            18,
            0.95,
            "spacy",
        ),
    ]

    result = resolver.resolve(entities)

    assert len(result) == 1
    assert result[0].source == "spacy"


def test_longer_overlapping_entity_is_kept_when_confidence_matches():
    resolver = EntityResolver()

    entities = [
        make_entity(
            "PERSON",
            "Sarthak",
            0,
            7,
            0.90,
            "presidio",
        ),
        make_entity(
            "PERSON",
            "Sarthak Malvadkar",
            0,
            18,
            0.90,
            "regex",
        ),
    ]

    result = resolver.resolve(entities)

    assert len(result) == 1
    assert result[0].original_text == "Sarthak Malvadkar"


def test_entities_from_different_blocks_do_not_overlap():
    resolver = EntityResolver()

    entities = [
        make_entity(
            "PERSON",
            "Sarthak Malvadkar",
            0,
            18,
            0.90,
            "presidio",
            block_index=0,
        ),
        make_entity(
            "PERSON",
            "Sarthak Malvadkar",
            0,
            18,
            0.90,
            "presidio",
            block_index=1,
        ),
    ]

    result = resolver.resolve(entities)

    assert len(result) == 2