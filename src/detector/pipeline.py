from src.detector.context_detector import ContextRuleDetector
from src.detector.entity_resolver import EntityResolver
from src.detector.pii_validator import PIIValidator
from src.detector.presidio_detector import PresidioDetector
from src.detector.regex_detector import RegexDetector
from src.detector.spacy_detector import SpacyDetector


SUPPORTED_ENTITY_TYPES = {
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "ORGANIZATION",
    "ADDRESS",
    "SSN",
    "CREDIT_CARD",
    "DATE_OF_BIRTH",
    "IP_ADDRESS",
}


class PIIDetectionPipeline:
    """Run all PII detectors and return only supported assignment categories."""

    def __init__(self):
        self.presidio = PresidioDetector()
        self.regex = RegexDetector()
        self.spacy = SpacyDetector()
        self.context = ContextRuleDetector()
        self.resolver = EntityResolver()
        self.validator = PIIValidator()

    def detect_block(self, block):
        entities = []

        entities.extend(
            self.presidio.detect(
                text=block.text,
                block_index=block.index,
            )
        )

        entities.extend(
            self.regex.detect(
                text=block.text,
                block_index=block.index,
            )
        )

        entities.extend(
            self.spacy.detect(
                text=block.text,
                block_index=block.index,
            )
        )

        entities.extend(
            self.context.detect(
                text=block.text,
                block_index=block.index,
            )
        )

        resolved_entities = self.resolver.resolve(entities)

        validated_entities = self.validator.validate(
            resolved_entities
        )

        return [
            entity
            for entity in validated_entities
            if entity.entity_type in SUPPORTED_ENTITY_TYPES
        ]

    def detect(self, blocks):
        all_entities = []

        for block in blocks:
            all_entities.extend(
                self.detect_block(block)
            )

        return all_entities