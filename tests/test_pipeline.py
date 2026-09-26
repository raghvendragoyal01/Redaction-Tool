from src.detector.pipeline import PIIDetectionPipeline
from src.models import TextBlock


def test_pipeline_detects_email():
    pipeline = PIIDetectionPipeline()

    block = TextBlock(
        text="Contact us at test@example.com",
        block_type="paragraph",
        location="body",
        index=0,
    )

    results = pipeline.detect_block(block)

    assert any(
        entity.entity_type == "EMAIL_ADDRESS"
        for entity in results
    )


def test_pipeline_detects_phone():
    pipeline = PIIDetectionPipeline()

    block = TextBlock(
        text="Call us at +91 81081 14949",
        block_type="paragraph",
        location="body",
        index=0,
    )

    results = pipeline.detect_block(block)

    assert any(
        entity.entity_type == "PHONE_NUMBER"
        for entity in results
    )


def test_pipeline_detects_person():
    pipeline = PIIDetectionPipeline()

    block = TextBlock(
        text="Contact Person: Sarthak Malvadkar",
        block_type="paragraph",
        location="body",
        index=0,
    )

    results = pipeline.detect_block(block)

    assert any(
        entity.entity_type == "PERSON"
        and "Sarthak Malvadkar" in entity.original_text
        for entity in results
    )


def test_pipeline_detects_address():
    pipeline = PIIDetectionPipeline()

    block = TextBlock(
        text=(
            "11/3, 11/4 and 11/5 Village Birdewadi, "
            "Chakan Taluka - Khed, Pune – 410 501, "
            "Maharashtra, India"
        ),
        block_type="paragraph",
        location="body",
        index=0,
    )

    results = pipeline.detect_block(block)

    assert any(
        entity.entity_type == "ADDRESS"
        for entity in results
    )