from dataclasses import dataclass
from typing import Optional


@dataclass
class TextBlock:
    """
    Represents a piece of text extracted from a DOCX document.
    """

    text: str
    block_type: str
    location: str
    index: int
    style_name: Optional[str] = None

@dataclass
class PIIEntity:
    """
    Represents a detected PII entity.

    All detection engines are converted into this common format.
    """

    entity_type: str
    original_text: str
    start: int
    end: int
    confidence: float
    source: str
    block_index: int