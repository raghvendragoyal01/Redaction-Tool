import re

from src.models import PIIEntity


class ContextRuleDetector:
    """
    Detect PII using document context and deterministic rules.

    This layer complements Presidio, regex, and spaCy.
    It is intentionally conservative to reduce false positives.
    """

    PERSON_CONTEXTS = (
        "contact person",
        "company secretary",
        "compliance officer",
        "managing director",
        "whole time director",
        "whole-time director",
        "executive director",
        "independent director",
        "non executive director",
        "non-executive director",
        "director",
        "promoter",
        "chief financial officer",
        "chief executive officer",
        "chief operating officer",
        "authorized signatory",
        "authorised signatory",
        "designated person",
    )

    DOB_CONTEXTS = (
        "date of birth",
        "dob",
        "birth date",
        "born",
    )

    ADDRESS_CONTEXTS = (
        "registered office",
        "corporate office",
        "correspondence address",
        "registered address",
        "corporate address",
        "address",
        "residing at",
        "office address",
    )

    COMPANY_SUFFIXES = (
        "limited",
        "private limited",
        "pvt ltd",
        "pvt. ltd.",
        "ltd",
        "ltd.",
        "llp",
        "inc",
        "inc.",
        "corporation",
        "corp",
        "corp.",
        "industries",
        "enterprises",
        "technologies",
        "solutions",
        "services",
        "holdings",
    )

    # Organizations/institutions that are not company PII for this task.
    ORGANIZATION_WHITELIST = {
        "sebi",
        "bse",
        "nse",
        "rbi",
        "roc",
        "irdai",
        "gst",
        "gstn",
        "nsdl",
        "cdsl",
        "nclt",
        "nclat",
        "ministry of corporate affairs",
        "government of india",
        "companies act",
    }

    ADDRESS_MARKERS = (
        "road",
        "lane",
        "street",
        "society",
        "apartment",
        "flat",
        "floor",
        "building",
        "village",
        "taluka",
        "plot",
        "nagar",
        "colony",
        "marg",
        "house",
        "sector",
        "phase",
        "industrial estate",
    )

    PIN_PATTERN = re.compile(r"\b\d{3}\s?\d{3}\b")

    DOB_PATTERN = re.compile(
        r"\b(?:"
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
        r")\b",
        re.IGNORECASE,
    )

    def detect_person_from_context(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:
        """
        Detect a person's name when the surrounding text clearly
        indicates a person-related field.
        """

        lowered = text.lower()

        if not any(context in lowered for context in self.PERSON_CONTEXTS):
            return []

        # Look for a name after a colon.
        match = re.search(
            r":\s*([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,4})",
            text,
        )

        if not match:
            return []

        name = match.group(1).strip()

        return [
            PIIEntity(
                entity_type="PERSON",
                original_text=name,
                start=match.start(1),
                end=match.end(1),
                confidence=0.95,
                source="context",
                block_index=block_index,
            )
        ]

    def detect_company(self, text: str, block_index: int) -> list[PIIEntity]:
        """
        Detect company/legal entity names using corporate suffixes.

        The detector requires a meaningful company name before the
        legal suffix and avoids matching generic standalone phrases.
        """

        company_pattern = re.compile(
            r"""
            (?<![A-Za-z])
            (
                (?:
                    [A-Z][A-Za-z0-9&.,'()/-]*
                    (?:\s+|$)
                ){1,10}
                (?:
                    Limited
                    |Private\s+Limited
                    |Pvt\.?\s+Ltd\.?
                    |Ltd\.?
                    |LLP
                    |Inc\.?
                    |Corporation
                    |Corp\.?
                    |Industries
                    |Enterprises
                    |Technologies
                    |Solutions
                    |Services
                    |Holdings
                )
            )
            \b
            """,
            re.VERBOSE,
        )

        entities = []

        for match in company_pattern.finditer(text):
            company = match.group(1).strip()

            # Reject incomplete legal suffix fragments.
            normalized = company.lower().strip(" .,;:")

            if normalized in {
                "private limited",
                "private\nlimited",
                "co llp",
                "co. llp",
                "india limited",
                "india) limited",
                "pandit llp",
                "pandit, llp",
                "advisory private limited",
            }:
                continue

            # Remove accidental trailing punctuation.
            company = company.rstrip(".,;:")

            # Require at least two meaningful words.
            words = re.findall(r"[A-Za-z][A-Za-z0-9&'-]*", company)

            if len(words) < 2:
                continue

            # Avoid obviously generic phrases.
            normalized = company.lower()

            if normalized in {
                "working capital",
                "senior management",
                "book running lead managers",
                "anchor investors",
                "registrar of companies",
            }:
                continue

            entities.append(
                PIIEntity(
                    entity_type="ORGANIZATION",
                    original_text=company,
                    start=match.start(1),
                    end=match.start(1) + len(company),
                    confidence=0.97,
                    source="context",
                    block_index=block_index,
                )
            )

        return entities

    def detect_dob(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:
        """
        Detect a date only when it is directly associated with
        a DOB label.

        Examples accepted:
            DOB: 12/03/1985
            Date of Birth: 12 March 1985
            Birth Date - January 12, 1985

        Normal dates elsewhere in the paragraph are ignored.
        """

        pattern = re.compile(
            r"\b(?:"
            r"date\s+of\s+birth"
            r"|dob"
            r"|birth\s+date"
            r")\b"
            r"\s*(?:[:\-–]\s*|\bis\s+)?"
            r"("
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

        entities = []

        for match in pattern.finditer(text):
            date_value = match.group(1)

            start = match.start(1)
            end = match.end(1)

            entities.append(
                PIIEntity(
                    entity_type="DATE_OF_BIRTH",
                    original_text=date_value,
                    start=start,
                    end=end,
                    confidence=0.99,
                    source="context",
                    block_index=block_index,
                )
            )

        return entities

    def detect_address(self, text: str, block_index: int) -> list[PIIEntity]:
        """
        Detect physical/mailing addresses using strong address anchors.

        The detector primarily uses PIN codes as the end anchor and
        captures the nearest address-related phrase before the PIN.
        This avoids classifying general location sentences as addresses.
        """

        entities = []

        # Strong explicit address labels.
        explicit_pattern = re.compile(
            r"""
            (?:
                Registered\s+Office
                |Corporate\s+Office
                |Correspondence\s+Address
                |Registered\s+Address
                |Corporate\s+Address
                |Office\s+Address
                |Address
            )
            \s*(?:at|is|:|-|–)?\s*
            (
                [^.;\n]{5,300}?
                \b\d{3}\s?\d{3}\b
                (?:[^.;\n]{0,80})?
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        for match in explicit_pattern.finditer(text):
            address = match.group(1).strip()

            address = re.sub(
                r"^(?:Office|Address)\s*:\s*",
                "",
                address,
                flags=re.IGNORECASE,
            )

            if self._looks_like_address(address):
                entities.append(
                    PIIEntity(
                        entity_type="ADDRESS",
                        original_text=address,
                        start=match.start(1),
                        end=match.start(1) + len(address),
                        confidence=0.99,
                        source="context",
                        block_index=block_index,
                    )
                )

        # PIN-anchored addresses for cases without explicit labels.
        pin_pattern = re.compile(r"\b\d{3}\s?\d{3}\b")

        address_start_pattern = re.compile(
            r"""
            (?:
                Plot(?:\s+No\.?)?
                |Flat(?:\s+No\.?)?
                |House
                |Office
                |Shop
                |Building
                |Floor
                |Survey(?:\s+No\.?)?
                |S\.?\s*No\.?
                |Village
                |Road
                |Lane
                |Society
                |Apartment
                |Taluka
                |Nagar
                |Colony
                |Marg
                |Sector
                |Phase
                |Industrial\s+Park
                |Industrial\s+Estate
                |Tower
                |Centre
                |Center
                |Complex
                |Plaza
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        for pin_match in pin_pattern.finditer(text):
            pin_end = pin_match.end()

            # Do not create a duplicate if explicit detection already covers it.
            if any(
                entity.start <= pin_match.start() < entity.end
                for entity in entities
            ):
                continue

            window_start = max(0, pin_match.start() - 250)
            window = text[window_start:pin_match.start()]

            starts = list(address_start_pattern.finditer(window))

            if not starts:
                continue

            start_match = starts[-1]

            # Check if there are leading premise / survey numbers before the start marker
            prefix_window = window[:start_match.start()]
            premise_match = re.search(
                r"(\b\d+[/A-Za-z0-9,\-–\s]*(?:and\s+\d+[/A-Za-z0-9,\-–\s]*)?)\s*$",
                prefix_window,
            )
            if premise_match:
                prefix_before = prefix_window[:premise_match.start(1)].strip()
                if not prefix_before or prefix_before.endswith((".", ";", ":", "–", "-", "\n")):
                    absolute_start = window_start + premise_match.start(1)
                else:
                    absolute_start = window_start + start_match.start()
            else:
                absolute_start = window_start + start_match.start()

            # Check trailing state / country after PIN
            after_pin = text[pin_end:]
            state_country_match = re.match(
                r"^((?:[\s,–-]*(?:Maharashtra|Rajasthan|Karnataka|Delhi|Gujarat|Tamil\s+Nadu|Telangana|Uttar\s+Pradesh|West\s+Bengal|Madhya\s+Pradesh|India))+)",
                after_pin,
                re.IGNORECASE,
            )
            if state_country_match:
                actual_end = pin_end + len(state_country_match.group(1).rstrip(" .,;:\n"))
            else:
                actual_end = pin_end

            candidate = text[absolute_start:actual_end].strip()

            # Stop obvious sentence/legal prose.
            candidate = re.sub(
                r"^(?:Office|Address)\s*:\s*",
                "",
                candidate,
                flags=re.IGNORECASE,
            )

            if not self._looks_like_address(candidate):
                continue

            entities.append(
                PIIEntity(
                    entity_type="ADDRESS",
                    original_text=candidate,
                    start=absolute_start,
                    end=actual_end,
                    confidence=0.97,
                    source="context",
                    block_index=block_index,
                )
            )

        return self._remove_overlapping_addresses(entities)

    def _looks_like_address(self, value: str) -> bool:
        """Return True when a candidate contains enough address evidence."""

        normalized = value.lower()

        has_pin = bool(re.search(r"\b\d{3}\s?\d{3}\b", value))

        address_markers = [
            "road",
            "lane",
            "street",
            "society",
            "apartment",
            "flat",
            "floor",
            "building",
            "village",
            "taluka",
            "plot",
            "nagar",
            "colony",
            "marg",
            "sector",
            "phase",
            "industrial park",
            "industrial estate",
            "district",
            "tower",
            "centre",
            "center",
            "complex",
            "plaza",
            "farms",
            "heights",
            "bhavan",
            "enclave",
            "avenue",
            "drive",
            "house",
            "survey",
            "office",
            "pune",
            "mumbai",
            "delhi",
            "bangalore",
            "bengaluru",
            "chennai",
            "hyderabad",
            "ahmedabad",
            "kolkata",
        ]

        marker_count = sum(
            marker in normalized
            for marker in address_markers
        )

        return has_pin and marker_count >= 1

    def _remove_overlapping_addresses(
        self,
        entities: list[PIIEntity],
    ) -> list[PIIEntity]:
        """Keep the most complete address when candidates overlap."""

        if not entities:
            return []

        entities = sorted(
            entities,
            key=lambda entity: (
                entity.start,
                -(entity.end - entity.start),
            ),
        )

        resolved = []

        for entity in entities:
            if not resolved:
                resolved.append(entity)
                continue

            previous = resolved[-1]

            if entity.start < previous.end:
                previous_length = previous.end - previous.start
                current_length = entity.end - entity.start

                if current_length > previous_length:
                    resolved[-1] = entity
            else:
                resolved.append(entity)

        return resolved

    def detect(
        self,
        text: str,
        block_index: int,
    ) -> list[PIIEntity]:

        entities = []

        entities.extend(
            self.detect_person_from_context(
                text,
                block_index,
            )
        )

        entities.extend(
            self.detect_company(
                text,
                block_index,
            )
        )

        entities.extend(
            self.detect_address(
                text,
                block_index,
            )
        )

        entities.extend(
            self.detect_dob(
                text,
                block_index,
            )
        )

        return entities