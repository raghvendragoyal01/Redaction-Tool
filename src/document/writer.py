import re
from collections import defaultdict
from pathlib import Path

from docx import Document

from src.document.reader import DocxReader
from src.models import PIIEntity


class DocxWriter:
    """
    Apply anonymization replacements to a DOCX document.

    The writer preserves the existing document structure and replaces
    detected entities directly inside Word paragraphs/runs using the
    exact same traversal order as DocxReader.
    """

    def __init__(self, input_path: str | Path):
        self.input_path = Path(input_path)

        if not self.input_path.exists():
            raise FileNotFoundError(
                f"DOCX file not found: {self.input_path}"
            )

        if self.input_path.suffix.lower() != ".docx":
            raise ValueError(
                f"Expected a DOCX file, got: {self.input_path.suffix}"
            )

        self.document = Document(self.input_path)

    def save(
        self,
        output_path: str | Path,
        entities: list[PIIEntity],
        replacements: dict[tuple[int, int, int], str] | dict,
        mapping: dict[str, str] | None = None,
    ):
        """
        Apply replacements and save the resulting document.
        """

        entities_by_block = defaultdict(list)

        for entity in entities:
            key = (
                entity.block_index,
                entity.start,
                entity.end,
            )

            replacement = replacements.get(key)

            if replacement is None:
                continue

            entities_by_block[entity.block_index].append(
                (entity, replacement)
            )

        block_index = 0

        # Unified traversal matching DocxReader.iter_paragraphs exactly
        for location, block_type, paragraph in DocxReader.iter_paragraphs(self.document):

            if not paragraph.text.strip():
                continue

            block_entities = entities_by_block.get(block_index, [])
            self._process_paragraph(paragraph, block_entities)

            block_index += 1

        # Global safety pass: replace any remaining mapped PII strings
        if mapping:
            self._apply_global_mapping_pass(mapping)

        # ---------------------------------------------------------
        # Save
        # ---------------------------------------------------------

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.document.save(output_path)

    # =============================================================
    # BLOCK PROCESSING
    # =============================================================

    def _process_paragraph(self, paragraph, entities):
        if not entities:
            return

        located = []
        paragraph_text = paragraph.text

        for entity, replacement in entities:
            result = self._find_entity(
                paragraph_text,
                entity.original_text,
            )

            if result is None:
                continue

            start, end = result
            located.append((start, end, replacement))

        # Replace from right to left
        located.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        for start, end, replacement in located:
            self._replace_range(
                paragraph,
                start,
                end,
                replacement,
            )

    def _apply_global_mapping_pass(self, mapping: dict[str, str]):
        """
        Ensure any occurrences of known PII throughout the document
        are substituted with their mapped synthetic values.
        """
        sorted_pairs = sorted(
            mapping.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

        for _, _, paragraph in DocxReader.iter_paragraphs(self.document):
            if not paragraph.text.strip():
                continue

            for original, replacement in sorted_pairs:
                if len(original.strip()) < 3:
                    continue

                for _ in range(20):
                    result = self._find_entity(paragraph.text, original)
                    if result is None:
                        break
                    start, end = result
                    self._replace_range(paragraph, start, end, replacement)

    # =============================================================
    # ENTITY SEARCH
    # =============================================================

    @staticmethod
    def _find_entity(text: str, target: str):
        if not text or not target:
            return None

        # 1. Exact match
        position = text.find(target)
        if position != -1:
            return position, position + len(target)

        # 2. Case-insensitive exact match
        position = text.lower().find(target.lower())
        if position != -1:
            return position, position + len(target)

        # 3. Flexible whitespace & dash regex match
        words = re.split(r"[\s\xa0\-_–—/]+", target.strip())
        if words:
            escaped_words = [re.escape(w) for w in words if w]
            pattern_str = r"[\s\xa0\n\r\t\-–—/.,()]+".join(escaped_words)
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    return match.start(), match.end()
            except re.error:
                pass

        # 4. Phone number digit flexibility
        digits = re.sub(r"\D", "", target)
        if len(digits) >= 10:
            phone_pattern_str = r"[\s\xa0\(\)\-\+\.]*".join(list(digits))
            try:
                phone_pattern = re.compile(phone_pattern_str)
                match = phone_pattern.search(text)
                if match:
                    return match.start(), match.end()
            except re.error:
                pass

        return None

    # =============================================================
    # RUN-AWARE RANGE REPLACEMENT
    # =============================================================

    def _replace_range(
        self,
        paragraph,
        start: int,
        end: int,
        replacement: str,
    ):
        runs = paragraph.runs
        if not runs:
            return

        run_ranges = []
        position = 0

        for run in runs:
            text = run.text or ""
            run_start = position
            run_end = position + len(text)

            run_ranges.append(
                (
                    run,
                    run_start,
                    run_end,
                )
            )

            position = run_end

        affected = [
            item
            for item in run_ranges
            if item[1] < end and item[2] > start
        ]

        if not affected:
            return

        first_run, first_start, _ = affected[0]
        last_run, last_start, _ = affected[-1]

        # Same run
        if first_run is last_run:
            text = first_run.text or ""
            local_start = max(0, start - first_start)
            local_end = max(0, end - first_start)

            first_run.text = (
                text[:local_start]
                + replacement
                + text[local_end:]
            )
            return

        # Multiple runs
        first_text = first_run.text or ""
        local_start = max(0, start - first_start)
        first_run.text = first_text[:local_start] + replacement

        for run, _, _ in affected[1:-1]:
            run.text = ""

        last_text = last_run.text or ""
        local_end = max(0, end - last_start)
        last_run.text = last_text[local_end:]