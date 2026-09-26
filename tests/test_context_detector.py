from src.detector.context_detector import ContextRuleDetector


def test_detects_person_from_contact_context():
    detector = ContextRuleDetector()

    text = "Contact Person: Sarthak Malvadkar"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert any(
        entity.entity_type == "PERSON"
        and entity.original_text == "Sarthak Malvadkar"
        for entity in results
    )


def test_detects_company_name():
    detector = ContextRuleDetector()

    text = "KSH International Limited"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert any(
        entity.entity_type == "ORGANIZATION"
        and "KSH International Limited" in entity.original_text
        for entity in results
    )


def test_detects_address():
    detector = ContextRuleDetector()

    text = (
        "11/3, 11/4 and 11/5 Village Birdewadi, "
        "Chakan Taluka - Khed, Pune – 410 501, "
        "Maharashtra, India"
    )

    results = detector.detect(
        text=text,
        block_index=0,
    )

    addresses = [
        entity
        for entity in results
        if entity.entity_type == "ADDRESS"
    ]

    assert len(addresses) == 1
    assert addresses[0].original_text == text


def test_does_not_detect_currency_as_person():
    detector = ContextRuleDetector()

    text = "₹ 100 million"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert not any(
        entity.entity_type == "PERSON"
        for entity in results
    )


def test_does_not_detect_na_as_company():
    detector = ContextRuleDetector()

    text = "N.A."

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert not any(
        entity.entity_type == "ORGANIZATION"
        for entity in results
    )

def test_detects_dob_with_date_of_birth_context():
    detector = ContextRuleDetector()

    text = "Date of Birth: 12 March 1985"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    dobs = [
        entity
        for entity in results
        if entity.entity_type == "DATE_OF_BIRTH"
    ]

    assert len(dobs) == 1
    assert dobs[0].original_text == "12 March 1985"


def test_detects_dob_with_numeric_date():
    detector = ContextRuleDetector()

    text = "DOB: 12/03/1985"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert any(
        entity.entity_type == "DATE_OF_BIRTH"
        and entity.original_text == "12/03/1985"
        for entity in results
    )


def test_does_not_treat_normal_date_as_dob():
    detector = ContextRuleDetector()

    text = "Date of Incorporation: 12 March 1985"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert not any(
        entity.entity_type == "DATE_OF_BIRTH"
        for entity in results
    )


def test_does_not_detect_date_without_dob_context():
    detector = ContextRuleDetector()

    text = "12 March 1985"

    results = detector.detect(
        text=text,
        block_index=0,
    )

    assert not any(
        entity.entity_type == "DATE_OF_BIRTH"
        for entity in results
    )

def test_does_not_capture_entire_business_paragraph_as_address():
    detector = ContextRuleDetector()

    text = (
        "The Company is expanding by setting up a plant at "
        "Plot No. F-223, Supa Parner Industrial Park, "
        "Mauje Palve Khurd, Taluka Parner, Dist – Ahmednagar, "
        "Maharashtra – 414 301. The proposed plant will be "
        "developed in phases."
    )

    results = detector.detect(
        text=text,
        block_index=0,
    )

    addresses = [
        entity
        for entity in results
        if entity.entity_type == "ADDRESS"
    ]

    assert addresses
    assert len(addresses[0].original_text) < len(text)
    assert "The proposed plant will be developed" not in addresses[0].original_text

def test_detects_full_company_name():
    detector = ContextRuleDetector()

    text = "KSH International Limited is the company."
    entities = detector.detect(text, 1)

    organizations = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ORGANIZATION"
    ]

    assert "KSH International Limited" in organizations


def test_detects_private_limited_company():
    detector = ContextRuleDetector()

    text = "Bhandary Metal Extrusion Private Limited"
    entities = detector.detect(text, 1)

    organizations = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ORGANIZATION"
    ]

    assert "Bhandary Metal Extrusion Private Limited" in organizations


def test_does_not_detect_generic_business_phrase():
    detector = ContextRuleDetector()

    text = "The company requires additional working capital."
    entities = detector.detect(text, 1)

    organizations = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ORGANIZATION"
    ]

    assert "working capital" not in [
        value.lower() for value in organizations
    ]

def test_rejects_location_sentence_as_address():
    detector = ContextRuleDetector()

    text = (
        "phase II of which is under construction, as on the date "
        "of this Red Herring Prospectus is located at Supa Ahilyanagar "
        "(formerly Ahmednagar), also in Maharashtra"
    )

    entities = detector.detect(text, 1)

    addresses = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ADDRESS"
    ]

    assert addresses == []


def test_detects_registered_office_address():
    detector = ContextRuleDetector()

    text = (
        "Registered Office at 11/3, 11/4 and 11/5, Village Birdewadi, "
        "Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India"
    )

    entities = detector.detect(text, 1)

    addresses = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ADDRESS"
    ]

    assert any("410 501" in address for address in addresses)


def test_detects_corporate_office_address():
    detector = ContextRuleDetector()

    text = (
        "Corporate Office at 201, Tower 2, Montreal Business Centre, "
        "Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India"
    )

    entities = detector.detect(text, 1)

    addresses = [
        entity.original_text
        for entity in entities
        if entity.entity_type == "ADDRESS"
    ]

    assert any("411 045" in address for address in addresses)