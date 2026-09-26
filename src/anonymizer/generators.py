from __future__ import annotations

import random
import re
from datetime import date, timedelta
from typing import Callable

from faker import Faker


class SyntheticDataGenerator:
    """
    Generate deterministic synthetic replacements for PII.

    Generated values are kept consistent for the lifetime of the
    generator instance. A collision check prevents generated values
    from matching known original PII values.
    """

    RESERVED_EMAIL_DOMAINS = {
        "example.com",
        "example.org",
        "example.net",
    }

    COMPANY_ADJECTIVES = [
        "Meridian",
        "Northstar",
        "Silverline",
        "Bluecrest",
        "Apex",
        "Pioneer",
        "Vertex",
        "Evergreen",
        "Summit",
        "Crestview",
    ]

    COMPANY_INDUSTRIES = [
        "Industrial",
        "Engineering",
        "Precision",
        "Advanced",
        "Integrated",
        "Global",
        "Technical",
        "Manufacturing",
    ]

    COMPANY_NOUNS = [
        "Technologies",
        "Industries",
        "Components",
        "Solutions",
        "Systems",
        "Enterprises",
        "Engineering",
        "Manufacturing",
    ]

    COMPANY_SUFFIXES = [
        "Limited",
        "Private Limited",
        "LLP",
    ]

    def __init__(self, seed: int = 20260926):
        """
        Initialize deterministic generators.

        A fixed seed makes test runs reproducible.
        """

        self.faker = Faker("en_IN")
        self.faker.seed_instance(seed)

        self.random = random.Random(seed)

        self._used_values: set[str] = set()

        self._generators: dict[str, Callable[[], str]] = {
            "PERSON": self.generate_person,
            "EMAIL_ADDRESS": self.generate_email,
            "PHONE_NUMBER": self.generate_phone,
            "ORGANIZATION": self.generate_organization,
            "ADDRESS": self.generate_address,
            "DATE_OF_BIRTH": self.generate_date_of_birth,
            "SSN": self.generate_ssn,
            "CREDIT_CARD": self.generate_credit_card,
            "IP_ADDRESS": self.generate_ip_address,
        }

    def generate(
        self,
        entity_type: str,
        original_value: str | None = None,
    ) -> str:
        """
        Generate a synthetic replacement for an entity type.

        The generated value is checked against known original values
        when original_value is supplied.
        """

        generator = self._generators.get(entity_type)

        if generator is None:
            raise ValueError(
                f"Unsupported entity type: {entity_type}"
            )

        original_normalized = self._normalize(original_value)

        for _ in range(100):
            candidate = generator()
            candidate_normalized = self._normalize(candidate)

            if candidate_normalized == original_normalized:
                continue

            if candidate_normalized in self._used_values:
                continue

            self._used_values.add(candidate_normalized)

            return candidate

        raise RuntimeError(
            f"Unable to generate a unique replacement for "
            f"{entity_type}"
        )

    def generate_person(self) -> str:
        """Generate a synthetic Indian-style full name."""

        return self.faker.name()

    def generate_email(self) -> str:
        """
        Generate an email using a reserved example domain.

        Example:
            arjun.mehta@example.com
        """

        first_name = self.faker.first_name().lower()
        last_name = self.faker.last_name().lower()

        first_name = re.sub(r"[^a-z]", "", first_name)
        last_name = re.sub(r"[^a-z]", "", last_name)

        return f"{first_name}.{last_name}@example.com"

    def generate_phone(self) -> str:
        """
        Generate a synthetic Indian mobile number.

        Uses a 10-digit mobile format beginning with 6-9.
        """

        first_digit = self.random.choice("6789")
        remaining = "".join(
            self.random.choice("0123456789")
            for _ in range(9)
        )

        return f"+91 {first_digit}{remaining}"

    def generate_organization(self) -> str:
        """Generate a synthetic company/legal entity name."""

        adjective = self.random.choice(
            self.COMPANY_ADJECTIVES
        )

        industry = self.random.choice(
            self.COMPANY_INDUSTRIES
        )

        noun = self.random.choice(
            self.COMPANY_NOUNS
        )

        suffix = self.random.choice(
            self.COMPANY_SUFFIXES
        )

        return (
            f"{adjective} {industry} "
            f"{noun} {suffix}"
        )

    def generate_address(self) -> str:
        """
        Generate a synthetic Indian-style address.
        """

        house_number = self.random.randint(10, 999)

        street = self.faker.street_name()

        city = self.faker.city()

        state = self.random.choice(
            [
                "Maharashtra",
                "Rajasthan",
                "Karnataka",
                "Gujarat",
                "Delhi",
                "Telangana",
                "Tamil Nadu",
            ]
        )

        pincode = self.random.randint(
            100000,
            999999,
        )

        return (
            f"{house_number}, {street}, "
            f"{city}, {state} – {pincode}, India"
        )

    def generate_date_of_birth(self) -> str:
        """Generate a synthetic date of birth."""

        start_date = date(
            1950,
            1,
            1,
        )

        end_date = date(
            2005,
            12,
            31,
        )

        days = (
            end_date - start_date
        ).days

        generated = (
            start_date
            + timedelta(
                days=self.random.randint(
                    0,
                    days,
                )
            )
        )

        return generated.strftime(
            "%d %B %Y"
        )

    def generate_ssn(self) -> str:
        """
        Generate a synthetic SSN-like value.

        This is intended only as a replacement string,
        not as a real government identifier.
        """

        first = self.random.randint(
            100,
            899,
        )

        middle = self.random.randint(
            10,
            99,
        )

        last = self.random.randint(
            1000,
            9999,
        )

        return f"{first:03d}-{middle:02d}-{last:04d}"

    def generate_credit_card(self) -> str:
        """
        Generate a synthetic payment-card replacement.

        Uses a reserved Visa test number so that the anonymized
        document does not contain a real person's card.
        """

        return "4111 1111 1111 1111"

    def generate_ip_address(self) -> str:
        """
        Generate a documentation/test IPv4 address.
        """

        return (
            f"192.0.2."
            f"{self.random.randint(1, 254)}"
        )

    @staticmethod
    def _normalize(value: str | None) -> str:
        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    def reset(self) -> None:
        """Reset generated-value tracking."""

        self._used_values.clear()