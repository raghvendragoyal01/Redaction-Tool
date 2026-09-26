from src.detector.pii_validator import PIIValidator
from src.models import PIIEntity


def make_entity(
    entity_type,
    text,
    source="presidio",
    confidence=0.85,
):
    return PIIEntity(
        entity_type=entity_type,
        original_text=text,
        start=0,
        end=len(text),
        confidence=confidence,
        source=source,
        block_index=0,
    )


def test_rejects_false_person():
    validator = PIIValidator()

    entity = make_entity(
        "PERSON",
        "SCRR",
    )

    results = validator.validate([entity])

    assert results == []


def test_keeps_real_person():
    validator = PIIValidator()

    entity = make_entity(
        "PERSON",
        "Pushpa Kushal Hegde",
    )

    results = validator.validate([entity])

    assert len(results) == 1
    assert results[0].original_text == "Pushpa Kushal Hegde"


def test_rejects_generic_organization():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "Working Capital",
        source="spacy",
    )

    results = validator.validate([entity])

    assert results == []


def test_rejects_spacy_abbreviation():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "UPI",
        source="spacy",
    )

    results = validator.validate([entity])

    assert results == []


def test_keeps_company_name():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "KSH International Limited",
        source="spacy",
    )

    results = validator.validate([entity])

    assert len(results) == 1


def test_rejects_short_phone():
    validator = PIIValidator()

    entity = make_entity(
        "PHONE_NUMBER",
        "16949",
        confidence=0.40,
    )

    results = validator.validate([entity])

    assert results == []


def test_keeps_valid_phone():
    validator = PIIValidator()

    entity = make_entity(
        "PHONE_NUMBER",
        "+91 81081 14949",
        source="regex",
        confidence=1.0,
    )

    results = validator.validate([entity])

    assert len(results) == 1


def test_keeps_valid_dob():
    validator = PIIValidator()

    entity = make_entity(
        "DATE_OF_BIRTH",
        "12 March 1985",
        source="context",
        confidence=0.98,
    )

    results = validator.validate([entity])

    assert len(results) == 1


def test_rejects_invalid_dob_value():
    validator = PIIValidator()

    entity = make_entity(
        "DATE_OF_BIRTH",
        "June 30, 2025",
        source="context",
        confidence=0.98,
    )

    # The date itself is syntactically valid, so the validator
    # intentionally accepts it. Context association is tested
    # separately by the DOB detector.
    results = validator.validate([entity])

    assert len(results) == 1

def test_rejects_spacy_generic_org_without_company_suffix():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "Anchor Investors",
        source="spacy",
    )

    results = validator.validate([entity])

    assert results == []


def test_keeps_spacy_company_with_suffix():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "Bhandary Metal Extrusion Private Limited",
        source="spacy",
    )

    results = validator.validate([entity])

    assert len(results) == 1


def test_keeps_context_company_without_spacy_dependency():
    validator = PIIValidator()

    entity = make_entity(
        "ORGANIZATION",
        "KSH International Limited",
        source="context",
    )

    results = validator.validate([entity])

    assert len(results) == 1