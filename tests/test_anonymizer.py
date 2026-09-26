from src.anonymizer.anonymizer import Anonymizer
from src.models import PIIEntity


def make_entity(
    entity_type,
    value,
    start=0,
    end=None,
    block_index=1,
):
    if end is None:
        end = start + len(value)

    return PIIEntity(
        entity_type=entity_type,
        original_text=value,
        start=start,
        end=end,
        confidence=1.0,
        source="test",
        block_index=block_index,
    )


def test_same_person_gets_same_fake_name():
    anonymizer = Anonymizer(seed=123)

    first = make_entity(
        "PERSON",
        "Rajesh Kushal Hegde",
    )

    second = make_entity(
        "PERSON",
        "Rajesh Kushal Hegde",
        start=50,
        end=69,
        block_index=2,
    )

    first_replacement = (
        anonymizer.anonymize_entity(first)
    )

    second_replacement = (
        anonymizer.anonymize_entity(second)
    )

    assert first_replacement == second_replacement
    assert first_replacement != "Rajesh Kushal Hegde"


def test_different_people_get_different_fake_names():
    anonymizer = Anonymizer(seed=123)

    first = make_entity(
        "PERSON",
        "Rajesh Kushal Hegde",
    )

    second = make_entity(
        "PERSON",
        "Rohit Kushal Hegde",
    )

    first_replacement = (
        anonymizer.anonymize_entity(first)
    )

    second_replacement = (
        anonymizer.anonymize_entity(second)
    )

    assert first_replacement != second_replacement


def test_email_uses_reserved_domain():
    anonymizer = Anonymizer(seed=123)

    entity = make_entity(
        "EMAIL_ADDRESS",
        "ksh.ipo@nuvama.com",
    )

    replacement = (
        anonymizer.anonymize_entity(entity)
    )

    assert "@example.com" in replacement
    assert replacement != "ksh.ipo@nuvama.com"


def test_phone_is_replaced():
    anonymizer = Anonymizer(seed=123)

    entity = make_entity(
        "PHONE_NUMBER",
        "+91 81081 14949",
    )

    replacement = (
        anonymizer.anonymize_entity(entity)
    )

    assert replacement != "+91 81081 14949"
    assert replacement.startswith("+91 ")


def test_company_is_replaced():
    anonymizer = Anonymizer(seed=123)

    entity = make_entity(
        "ORGANIZATION",
        "KSH INTERNATIONAL LIMITED",
    )

    replacement = (
        anonymizer.anonymize_entity(entity)
    )

    assert replacement != (
        "KSH INTERNATIONAL LIMITED"
    )

    assert any(
        suffix in replacement
        for suffix in [
            "Limited",
            "Private Limited",
            "LLP",
        ]
    )


def test_whitespace_and_case_are_normalized():
    anonymizer = Anonymizer(seed=123)

    first = make_entity(
        "PERSON",
        "Rajesh Kushal Hegde",
    )

    second = make_entity(
        "PERSON",
        "  RAJESH   KUSHAL HEGDE  ",
        start=50,
        end=78,
        block_index=2,
    )

    first_replacement = (
        anonymizer.anonymize_entity(first)
    )

    second_replacement = (
        anonymizer.anonymize_entity(second)
    )

    assert first_replacement == second_replacement


def test_anonymize_entities_returns_position_mapping():
    anonymizer = Anonymizer(seed=123)

    entity = make_entity(
        "EMAIL_ADDRESS",
        "test@example.com",
        start=10,
        end=26,
        block_index=5,
    )

    replacements = (
        anonymizer.anonymize_entities(
            [entity]
        )
    )

    replacement = replacements[
        (5, 10, 26)
    ]

    assert replacement != "test@example.com"


def test_mapping_can_be_retrieved():
    anonymizer = Anonymizer(seed=123)

    entity = make_entity(
        "PERSON",
        "Sarthak Malvadkar",
    )

    replacement = (
        anonymizer.anonymize_entity(entity)
    )

    mapping = anonymizer.get_mapping()

    assert (
        mapping["PERSON"]["sarthak malvadkar"]
        == replacement
    )