import re

from src.models import PIIEntity


class PIIValidator:
    """
    Validate and filter detections produced by Presidio, regex,
    spaCy, and context rules.

    The goal is to reduce false positives before anonymization.
    """

    GENERIC_ORG_TERMS = {
        "red herring",
        "anchor investors",
        "book running lead managers",
        "book running lead manager",
        "registrar of companies",
        "the registrar of companies",
        "working capital",
        "senior management",
        "operations",
        "maximum",
        "offer",
        "qib",
        "upi",
        "challan",
        "specialized",
        "state insurance",
        "provident fund",
        "goods and services tax",
        "llp",
        "chartered accountants",
        "5th floor",
    }

    PERSON_BLACKLIST = {
        "scrr",
        "challan",
        "unpai",
        "senior management",
        "working capital",
        "operations",
        "maximum",
        "offer",
    }

    PHONE_MIN_DIGITS = 10

    COMPANY_SUFFIX_PATTERN = re.compile(
        r"\b(?:"
        r"limited|private limited|pvt\.?\s*ltd\.?|"
        r"ltd\.?|llp|inc\.?|corporation|corp\.?|"
        r"industries|enterprises|technologies|"
        r"solutions|services|holdings"
        r")\b",
        re.IGNORECASE,
    )

    DOB_LABEL_PATTERN = re.compile(
        r"\b(?:date\s+of\s+birth|dob|birth\s+date)\b"
        r"\s*(?:[:\-–]\s*|\bis\s+)?",
        re.IGNORECASE,
    )

    DOB_DATE_PATTERN = re.compile(
        r"(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+\d{4}"
        r"|"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}"
        r")",
        re.IGNORECASE,
    )

    def validate(self, entities: list[PIIEntity]) -> list[PIIEntity]:
        """
        Validate all entities and remove obvious false positives.
        """

        validated = []

        for entity in entities:
            if not self._is_valid(entity):
                continue

            validated.append(entity)

        return validated

    def _is_valid(self, entity: PIIEntity) -> bool:
        entity_type = entity.entity_type
        value = entity.original_text.strip()

        if not value:
            return False

        if entity_type == "PERSON":
            return self._valid_person(entity)

        if entity_type == "ORGANIZATION":
            return self._valid_organization(entity)

        if entity_type == "PHONE_NUMBER":
            return self._valid_phone(entity)

        if entity_type == "DATE_OF_BIRTH":
            return self._valid_dob(entity)

        return True

    def _valid_person(self, entity: PIIEntity) -> bool:
        value = entity.original_text.strip()
        normalized = value.lower()

        if normalized in self.PERSON_BLACKLIST:
            return False

        if not re.search(r"[A-Za-z]", value):
            return False

        # The assignment requires full names.
        # Context-based detections can be trusted when a document
        # role explicitly identifies the person.
        if entity.source != "context":
            name_parts = [
                part for part in value.split()
                if re.search(r"[A-Za-z]", part)
            ]

            if len(name_parts) < 2:
                return False

        # Reject short all-uppercase labels such as SCRR.
        if len(value) <= 6 and value.replace(" ", "").isupper():
            return False

        return True

    def _valid_organization(self, entity: PIIEntity) -> bool:
        value = entity.original_text.strip()
        normalized = value.lower().strip(" .,;:")

        if normalized in self.GENERIC_ORG_TERMS:
            return False

        words = re.findall(r"[A-Za-z0-9]+", value)
        if len(words) < 2:
            return False

        # Reject if the entire entity consists solely of legal suffix / article words
        suffix_words = {
            "private", "limited", "pvt", "ltd", "llp",
            "inc", "corp", "corporation", "co", "the", "and",
        }
        if all(w.lower() in suffix_words for w in words):
            return False

        # Reject very short abbreviations such as UPI, QIB, SCRR, etc.
        compact = value.replace(" ", "").replace(".", "")
        if len(compact) <= 8 and compact.isupper():
            return False

        # spaCy ORG entities need stronger evidence.
        if entity.source == "spacy":
            if not self.COMPANY_SUFFIX_PATTERN.search(value):
                return False

        return True

    def _valid_phone(self, entity: PIIEntity) -> bool:
        digits = re.sub(r"\D", "", entity.original_text)

        # Indian numbers may contain the country code 91.
        if digits.startswith("91") and len(digits) == 12:
            local_number = digits[2:]
        else:
            local_number = digits

        if len(local_number) < self.PHONE_MIN_DIGITS:
            return False

        # If Presidio returns a weak short match, reject it.
        if entity.source == "presidio" and entity.confidence < 0.60:
            return False

        return True

    def _valid_dob(self, entity: PIIEntity) -> bool:
        """
        DATE_OF_BIRTH entities must contain a valid date.

        Context association is handled separately in the
        DOB detector, so this method only validates the
        resulting entity itself.
        """

        return bool(
            self.DOB_DATE_PATTERN.fullmatch(
                entity.original_text.strip()
            )
        )