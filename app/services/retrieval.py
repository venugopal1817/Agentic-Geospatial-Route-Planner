from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_FILE = Path(__file__).resolve().parents[1] / ".." / "telangana_villages.csv"


def normalize_name(value: str) -> str:
    """Normalize a village name for retrieval and comparison."""
    if value is None:
        return ""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute straight-line distance between two coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def load_village_dataset(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load all village records from the trusted CSV file."""
    target_path = path or DATA_FILE
    with target_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VillageRetrievalService:
    """Retrieval layer over the village dataset with exact, normalized, and fuzzy matching."""

    def __init__(self, dataset: Optional[List[Dict[str, Any]]] = None):
        self.dataset = dataset or load_village_dataset()

    def exact_match(self, name: str) -> List[Dict[str, Any]]:
        normalized = normalize_name(name)
        return [
            row for row in self.dataset
            if normalize_name(row.get("village", "")) == normalized
        ]

    def normalized_match(self, name: str) -> List[Dict[str, Any]]:
        normalized = normalize_name(name)
        results: List[Dict[str, Any]] = []
        for row in self.dataset:
            village_name = row.get("village", "")
            candidate = normalize_name(village_name)
            if candidate == normalized:
                results.append(row)
            elif candidate.startswith(normalized) and len(candidate) - len(normalized) <= 3:
                results.append(row)
        return results

    def fuzzy_match(self, name: str, threshold: float = 0.5, limit: int = 5) -> List[Dict[str, Any]]:
        normalized_query = normalize_name(name)
        if not normalized_query:
            return []

        scored: List[tuple[float, Dict[str, Any]]] = []
        for row in self.dataset:
            village_name = row.get("village", "")
            candidate = normalize_name(village_name)
            if not candidate:
                continue
            max_len = max(len(normalized_query), len(candidate))
            if max_len == 0:
                score = 1.0
            else:
                distance = self._levenshtein(normalized_query, candidate)
                score = 1 - (distance / max_len)
            if score >= threshold:
                scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:limit]]

    def retrieve_candidates(self, name: str, threshold: float = 0.5, limit: int = 5) -> List[Dict[str, Any]]:
        """Return ranked candidate records for a village query."""
        exact = self.exact_match(name)
        normalized = self.normalized_match(name)
        fuzzy = self.fuzzy_match(name, threshold=threshold, limit=limit)

        merged: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in exact + normalized + fuzzy:
            key = item.get("village", "") + "|" + item.get("district", "") + "|" + item.get("subdistric", "")
            if key not in seen:
                seen.add(key)
                merged.append(item)

        if merged:
            return merged[:limit]
        return []

    @staticmethod
    def _levenshtein(first: str, second: str) -> int:
        if first == second:
            return 0
        if not first:
            return len(second)
        if not second:
            return len(first)

        previous = list(range(len(second) + 1))
        for i, first_char in enumerate(first, start=1):
            current = [i]
            for j, second_char in enumerate(second, start=1):
                insertion = current[j - 1] + 1
                deletion = previous[j] + 1
                substitution = previous[j - 1] + (0 if first_char == second_char else 1)
                current.append(min(insertion, deletion, substitution))
            previous = current
        return previous[-1]

    @staticmethod
    def build_candidate_summary(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return minimal metadata needed for selection and UI display."""
        results: List[Dict[str, Any]] = []
        for row in candidates:
            results.append({
                "id": row.get("village", ""),
                "name": row.get("village", ""),
                "district": row.get("district", ""),
                "subdistric": row.get("subdistric", ""),
                "state": row.get("state", "Telangana"),
                "latitude": float(row.get("latitude", 0.0)),
                "longitude": float(row.get("longitude", 0.0)),
            })
        return results
