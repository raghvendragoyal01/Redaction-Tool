from presidio_analyzer import AnalyzerEngine

from src.models import PIIEntity


class PresidioDetector:
    """
    Detect PII using Microsoft Presidio.
    """

    def __init__(self):
        self.analyzer = AnalyzerEngine()

    def detect(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:
        """
        Detect PII entities in a single text block.
        """

        results = self.analyzer.analyze(
            text=text,
            language="en",
        )

        entities = []

        for result in results:
            entities.append(
                PIIEntity(
                    entity_type=result.entity_type,
                    original_text=text[
                        result.start:result.end
                    ],
                    start=result.start,
                    end=result.end,
                    confidence=result.score,
                    source="presidio",
                    block_index=block_index,
                )
            )

        return entities