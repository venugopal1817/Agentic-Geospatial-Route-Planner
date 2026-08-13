from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field, field_validator


class ParsedIntent(BaseModel):
    origin: str | None = Field(default=None, description="Starting location")
    destinations: List[str] = Field(default_factory=list, description="Destination villages")
    travel_intent: str = Field(default="visit_locations", description="User intent category")
    optimization_goal: str = Field(default="minimum_distance", description="Optimization aim")

    @field_validator("destinations")
    @classmethod
    def validate_destinations(cls, value: List[str]) -> List[str]:
        cleaned = []
        for item in value:
            cleaned_item = item.strip()
            if cleaned_item:
                cleaned.append(cleaned_item)
        return cleaned


class IntentParser:
    """Simple structured intent parser that validates output against the typed schema."""

    @staticmethod
    def parse(text: str) -> ParsedIntent:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("Request text is required")

        origin = None
        match = re.search(r"from\s+([A-Za-z][A-Za-z0-9\s-]*?)(?=\s+(?:and|to|visit|travel|give|start|starting)|,|\.|$)", cleaned, flags=re.IGNORECASE)
        if match:
            origin = match.group(1).strip()

        destination_parts = re.split(r"[,;]|\s+and\s+|\bto\b|\bvisit\b|\btravel\b", cleaned, flags=re.IGNORECASE)
        destinations: List[str] = []
        for part in destination_parts:
            candidate = part.strip()
            candidate = re.sub(r"^(i need to|i want to|starting from|from)\s+", "", candidate, flags=re.IGNORECASE)
            candidate = re.sub(r"^hyderabad\s+", "", candidate, flags=re.IGNORECASE)
            candidate = candidate.rstrip(".")
            if not candidate:
                continue
            if origin and candidate.lower() == origin.lower():
                continue
            if candidate.lower() in {"i", "need", "start", "starting", "visit", "travel", "go", "to", "from", "give", "me", "most", "efficient", "route", "hyderabad"}:
                continue
            destinations.append(candidate)

        if not origin:
            origin = "Unknown"

        result = ParsedIntent(
            origin=origin,
            destinations=list(dict.fromkeys(destinations)),
            travel_intent="visit_locations",
            optimization_goal="minimum_distance",
        )
        return result
