from collections import defaultdict
import re

from src.anonymizer.generators import SyntheticDataGenerator
from src.models import PIIEntity


class Anonymizer:
    """
    Replace detected PII with deterministic synthetic values.

    The same original value receives the same replacement
    throughout the document.
    """

    def __init__(self, seed: int = 20260926):
        self.generator = SyntheticDataGenerator(
            seed=seed
        )

        self._replacement_maps = defaultdict(dict)
        self._raw_text_map: dict[str, str] = {}

    def anonymize_entity(
        self,
        entity: PIIEntity,
    ) -> str:
        """
        Return a stable synthetic replacement.
        """

        entity_type = entity.entity_type

        normalized_value = self._normalize(
            entity.original_text
        )

        replacement_map = self._replacement_maps[
            entity_type
        ]

        # Existing mapping → reuse it.
        if normalized_value in replacement_map:
            replacement = replacement_map[
                normalized_value
            ]
        else:
            # Generate a new synthetic value.
            replacement = self.generator.generate(
                entity_type=entity_type,
                original_value=entity.original_text,
            )

            replacement_map[
                normalized_value
            ] = replacement

        self._raw_text_map[entity.original_text] = replacement
        self._raw_text_map[entity.original_text.strip()] = replacement
        return replacement

    def anonymize_entities(
        self,
        entities: list[PIIEntity],
    ) -> dict[tuple[int, int, int], str]:
        """
        Generate replacements for all detected entities.

        Returns:
            Mapping of:
            (block_index, start, end)
            →
            replacement
        """

        replacements = {}

        for entity in entities:
            key = (
                entity.block_index,
                entity.start,
                entity.end,
            )

            replacements[key] = (
                self.anonymize_entity(entity)
            )

        return replacements

    def get_mapping(self) -> dict[str, dict[str, str]]:
        """
        Return the complete anonymization mapping.
        """

        return {
            entity_type: dict(mapping)
            for entity_type, mapping
            in self._replacement_maps.items()
        }

    def get_raw_mapping(self) -> dict[str, str]:
        """
        Return raw text to replacement mapping.
        """
        return dict(self._raw_text_map)

    def reset(self) -> None:
        """Reset mappings and generated values."""

        self._replacement_maps.clear()
        self._raw_text_map.clear()
        self.generator.reset()

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )