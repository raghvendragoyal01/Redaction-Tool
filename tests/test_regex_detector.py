from src.detector.regex_detector import RegexDetector


def test_detects_email():
    detector = RegexDetector()

    results = detector.detect(
        "Contact test@example.com",
        block_index=0,
    )

    assert any(
        entity.entity_type == "EMAIL_ADDRESS"
        for entity in results
    )


def test_detects_indian_phone_number():
    detector = RegexDetector()

    results = detector.detect(
        "Call +91 81081 14949",
        block_index=0,
    )

    assert any(
        entity.entity_type == "PHONE_NUMBER"
        for entity in results
    )


def test_detects_valid_ip():
    detector = RegexDetector()

    results = detector.detect(
        "Server IP: 192.168.1.100",
        block_index=0,
    )

    assert any(
        entity.entity_type == "IP_ADDRESS"
        for entity in results
    )


def test_rejects_invalid_ip():
    detector = RegexDetector()

    results = detector.detect(
        "Invalid IP: 999.999.999.999",
        block_index=0,
    )

    assert not any(
        entity.entity_type == "IP_ADDRESS"
        for entity in results
    )


def test_detects_valid_credit_card():
    detector = RegexDetector()

    # Standard Luhn-valid test number.
    results = detector.detect(
        "Card: 4111 1111 1111 1111",
        block_index=0,
    )

    assert any(
        entity.entity_type == "CREDIT_CARD"
        for entity in results
    )


def test_rejects_invalid_credit_card():
    detector = RegexDetector()

    results = detector.detect(
        "Number: 4111 1111 1111 1112",
        block_index=0,
    )

    assert not any(
        entity.entity_type == "CREDIT_CARD"
        for entity in results
    )


def test_detects_ssn():
    detector = RegexDetector()

    results = detector.detect(
        "SSN: 123-45-6789",
        block_index=0,
    )

    assert any(
        entity.entity_type == "SSN"
        for entity in results
    )

def test_detects_indian_landline_with_country_code():
    detector = RegexDetector()

    entities = detector.detect(
        "+91 20 4505 3237",
        block_index=1,
    )

    phones = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "PHONE_NUMBER"
    ]

    assert "+91 20 4505 3237" in phones


def test_detects_indian_landline_without_country_code():
    detector = RegexDetector()

    entities = detector.detect(
        "022-68052182",
        block_index=1,
    )

    phones = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "PHONE_NUMBER"
    ]

    assert "022-68052182" in phones


def test_detects_indian_mobile():
    detector = RegexDetector()

    entities = detector.detect(
        "+91 81081 14949",
        block_index=1,
    )

    phones = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "PHONE_NUMBER"
    ]

    assert "+91 81081 14949" in phones


def test_rejects_short_numeric_value_as_phone():
    detector = RegexDetector()

    entities = detector.detect(
        "The reference number is 16949.",
        block_index=1,
    )

    phones = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "PHONE_NUMBER"
    ]

    assert "16949" not in phones