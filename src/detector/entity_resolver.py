from src.models import PIIEntity


class EntityResolver:
    """
    Merge, deduplicate, and resolve overlapping PII detections.
    """

    SOURCE_PRIORITY = {
        "regex": 3,
        "presidio": 2,
        "spacy": 1,
    }

    def resolve(
        self,
        entities: list[PIIEntity],
    ) -> list[PIIEntity]:
        """
        Resolve duplicate and overlapping entities.

        Entities are resolved independently within each
        document block.
        """

        if not entities:
            return []

        # Sort by:
        # 1. block
        # 2. start position
        # 3. longer span first
        # 4. confidence
        # 5. detector priority
        sorted_entities = sorted(
            entities,
            key=lambda entity: (
                entity.block_index,
                entity.start,
                -(entity.end - entity.start),
                -entity.confidence,
                -self.SOURCE_PRIORITY.get(
                    entity.source,
                    0,
                ),
            ),
        )

        resolved: list[PIIEntity] = []

        for candidate in sorted_entities:

            # Check whether candidate overlaps an
            # already accepted entity.
            overlapping = [
                existing
                for existing in resolved
                if self._overlaps(
                    candidate,
                    existing,
                )
            ]

            if not overlapping:
                resolved.append(candidate)
                continue

            # Decide whether the candidate should
            # replace all overlapping detections.
            if all(
                self._is_better(candidate, existing)
                for existing in overlapping
            ):
                resolved = [
                    entity
                    for entity in resolved
                    if not self._overlaps(
                        candidate,
                        entity,
                    )
                ]

                resolved.append(candidate)

        return sorted(
            resolved,
            key=lambda entity: (
                entity.block_index,
                entity.start,
            ),
        )

    @staticmethod
    def _overlaps(
        first: PIIEntity,
        second: PIIEntity,
    ) -> bool:
        """Return True when two entities overlap."""

        if first.block_index != second.block_index:
            return False

        return (
            first.start < second.end
            and second.start < first.end
        )

    def _is_better(
        self,
        candidate: PIIEntity,
        existing: PIIEntity,
    ) -> bool:
        """
        Decide whether candidate is stronger than
        an existing overlapping detection.
        """

        candidate_priority = self.SOURCE_PRIORITY.get(
            candidate.source,
            0,
        )

        existing_priority = self.SOURCE_PRIORITY.get(
            existing.source,
            0,
        )

        # 1. Higher confidence wins
        if candidate.confidence > existing.confidence:
            return True

        if candidate.confidence < existing.confidence:
            return False

        # 2. If confidence is equal, prefer the longer detected span
        candidate_length = candidate.end - candidate.start
        existing_length = existing.end - existing.start

        if candidate_length > existing_length:
            return True

        if candidate_length < existing_length:
            return False

        # 3. If length is also equal, use detector priority
        return candidate_priority > existing_priority