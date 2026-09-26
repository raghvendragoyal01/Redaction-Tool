import spacy

from src.models import PIIEntity


class SpacyDetector:
    """
    Detect named entities using spaCy NER.
    """

    ENTITY_MAPPING = {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
    }

    def __init__(
        self,
        model_name: str = "en_core_web_lg",
    ):
        self.nlp = spacy.load(model_name)

    def detect(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:
        """
        Detect relevant named entities in a text block.
        """

        document = self.nlp(text)

        entities: list[PIIEntity] = []

        for entity in document.ents:

            mapped_type = self.ENTITY_MAPPING.get(
                entity.label_
            )

            if mapped_type is None:
                continue

            entities.append(
                PIIEntity(
                    entity_type=mapped_type,
                    original_text=entity.text,
                    start=entity.start_char,
                    end=entity.end_char,
                    confidence=0.85,
                    source="spacy",
                    block_index=block_index,
                )
            )

        return entities