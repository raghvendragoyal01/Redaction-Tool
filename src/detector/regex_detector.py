import ipaddress
import re

from src.models import PIIEntity


class RegexDetector:
    """
    Detect deterministic PII patterns using regular expressions
    and validation rules.
    """

    PATTERNS = {
        "EMAIL_ADDRESS": re.compile(
            r"\b[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),

        "PHONE_NUMBER": re.compile(
            r"""
            (?<!\d)
            (?:
                # Indian mobile
                (?:\+?\s*91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}

                |

                # Indian landline with country code
                \+?\s*91[\s-]?
                \d{2,4}[\s-]?(?:\d{3,4}[\s-]?\d{3,4}|\d{6,8})

                |

                # Indian landline with leading 0
                0\d{2,4}[\s-]?(?:\d{3,4}[\s-]?\d{3,4}|\d{6,8})

                |

                # Common parenthesized format
                \(0\d{2,4}\)[\s-]?(?:\d{3,4}[\s-]?\d{3,4}|\d{6,8})
            )
            (?!\d)
            """,
            re.VERBOSE,
        ),

        "IP_ADDRESS": re.compile(
            r"(?<![\d.])"
            r"(?:\d{1,3}\.){3}\d{1,3}"
            r"(?![\d.])"
        ),

        "CREDIT_CARD": re.compile(
            r"(?<!\d)"
            r"(?:\d[ -]?){13,19}"
            r"(?!\d)"
        ),

        "SSN": re.compile(
            r"(?<!\d)"
            r"\d{3}-\d{2}-\d{4}"
            r"(?!\d)"
        ),
    }

    def detect(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:
        """
        Detect regex-based PII entities in a text block.
        """

        entities: list[PIIEntity] = []

        for entity_type, pattern in self.PATTERNS.items():

            for match in pattern.finditer(text):

                matched_text = match.group()

                if entity_type == "IP_ADDRESS":
                    if not self._is_valid_ip(matched_text):
                        continue

                if entity_type == "CREDIT_CARD":
                    digits = re.sub(
                        r"\D",
                        "",
                        matched_text,
                    )

                    if not self._passes_luhn(digits):
                        continue

                entities.append(
                    PIIEntity(
                        entity_type=entity_type,
                        original_text=matched_text,
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,
                        source="regex",
                        block_index=block_index,
                    )
                )

        return entities

    @staticmethod
    def _is_valid_ip(value: str) -> bool:
        """Validate an IPv4 or IPv6 address."""

        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _passes_luhn(number: str) -> bool:
        """
        Validate a number using the Luhn checksum algorithm.
        """

        if not number.isdigit():
            return False

        if not 13 <= len(number) <= 19:
            return False

        total = 0
        reverse_digits = number[::-1]

        for index, digit in enumerate(reverse_digits):
            value = int(digit)

            if index % 2 == 1:
                value *= 2

                if value > 9:
                    value -= 9

            total += value

        return total % 10 == 0