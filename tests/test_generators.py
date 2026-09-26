from src.anonymizer.generators import (
    SyntheticDataGenerator,
)


def test_person_generation():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "PERSON",
        "Rajesh Kushal Hegde",
    )

    assert value
    assert value != "Rajesh Kushal Hegde"


def test_email_generation():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "EMAIL_ADDRESS",
        "test@realcompany.com",
    )

    assert value.endswith("@example.com")


def test_phone_generation():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "PHONE_NUMBER",
        "+91 81081 14949",
    )

    assert value.startswith("+91 ")
    assert len(value.replace(" ", "")) == 13


def test_organization_generation():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "ORGANIZATION",
        "KSH INTERNATIONAL LIMITED",
    )

    assert value != "KSH INTERNATIONAL LIMITED"


def test_address_generation():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "ADDRESS",
        "11/3, Village Birdewadi, Pune - 410501",
    )

    assert value
    assert value != (
        "11/3, Village Birdewadi, Pune - 410501"
    )


def test_deterministic_generation():
    first = SyntheticDataGenerator(seed=123)
    second = SyntheticDataGenerator(seed=123)

    value1 = first.generate(
        "PERSON",
        "Person One",
    )

    value2 = second.generate(
        "PERSON",
        "Person One",
    )

    assert value1 == value2


def test_same_generator_does_not_repeat_values():
    generator = SyntheticDataGenerator(
        seed=123
    )

    first = generator.generate(
        "PERSON",
        "Person One",
    )

    second = generator.generate(
        "PERSON",
        "Person Two",
    )

    assert first != second


def test_documentation_ip_is_used():
    generator = SyntheticDataGenerator(
        seed=123
    )

    value = generator.generate(
        "IP_ADDRESS",
        "192.168.1.100",
    )

    assert value.startswith("192.0.2.")


def test_reset_clears_used_values():
    generator = SyntheticDataGenerator(
        seed=123
    )

    generator.generate(
        "PERSON",
        "Person One",
    )

    generator.reset()

    assert generator._used_values == set()