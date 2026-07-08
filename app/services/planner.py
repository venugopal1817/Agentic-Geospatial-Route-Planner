from __future__ import annotations

import csv
import itertools
import math
import re
from pathlib import Path
from typing import List, Dict, Optional


DATA_FILE = Path(__file__).resolve().parents[1] / ".." / "telangana_villages.csv"


def _normalize_name(value: str) -> str:
    """Normalize a village name for comparison."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def _edit_distance(first: str, second: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if first == second:
        return 0
    if not first:
        return len(second)
    if not second:
        return len(first)

    previous_row = list(range(len(second) + 1))
    for i, first_char in enumerate(first, start=1):
        current_row = [i]
        for j, second_char in enumerate(second, start=1):
            insertion = current_row[j - 1] + 1
            deletion = previous_row[j] + 1
            substitution = previous_row[j - 1] + (0 if first_char == second_char else 1)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row

    return previous_row[-1]


def _distance(a: Dict[str, str], b: Dict[str, str]) -> float:
    """Compute a simple planar distance between two coordinate pairs."""
    return math.hypot(float(a["latitude"]) - float(b["latitude"]), float(a["longitude"]) - float(b["longitude"]))


def _choose_best_records(candidate_groups: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """Select the best one record from each group using geographic proximity."""
    if not candidate_groups:
        return []
    total_combinations = 1
    for group in candidate_groups:
        total_combinations *= len(group)
    if total_combinations > 5000:
        # Too many combinations, fallback to first option for each group
        return [group[0] for group in candidate_groups]

    best_score = None
    best_choice: Optional[List[Dict[str, str]]] = None
    for choice in itertools.product(*candidate_groups):
        score = 0.0
        for i, record_a in enumerate(choice):
            for record_b in choice[i + 1 :]:
                score += _distance(record_a, record_b)
        if best_score is None or score < best_score:
            best_score = score
            best_choice = list(choice)
    return best_choice or []


def _find_best_matches(query: str, candidates: List[str], top_n: int = 3) -> Optional[List[Dict[str, object]]]:
    """Find the top N likely village matches using normalized exact match and fuzzy similarity."""
    normalized_query = _normalize_name(query)
    if not normalized_query:
        return None

    exact_matches = [candidate for candidate in candidates if _normalize_name(candidate) == normalized_query]
    if exact_matches:
        return [{"suggested_match": exact_matches[0], "status": "matched", "score": 1.0}]

    scored_matches: List[Dict[str, object]] = []
    for candidate in candidates:
        candidate_key = _normalize_name(candidate)
        if not candidate_key:
            continue
        distance = _edit_distance(normalized_query, candidate_key)
        max_len = max(len(normalized_query), len(candidate_key))
        score = round(1 - (distance / max_len), 2) if max_len else 1.0

        if score >= 0.5:
            scored_matches.append({"candidate": candidate, "score": score})

    if not scored_matches:
        return None

    scored_matches.sort(key=lambda item: item["score"], reverse=True)
    return [{"suggested_match": m["candidate"], "status": "suggested", "score": m["score"]} for m in scored_matches[:top_n]]


def load_villages(path: Optional[Path] = None) -> List[Dict[str, str]]:
    """Load village records from the CSV file."""
    target_path = path or DATA_FILE
    with target_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def get_village_by_name(name: str) -> Optional[Dict[str, str]]:
    """Get the first village record matching a name (normalized)."""
    dataset = load_villages()
    normalized_name = _normalize_name(name)
    for row in dataset:
        if _normalize_name(row["village"].strip()) == normalized_name:
            return row
    return None


def get_all_villages_by_name(name: str) -> List[Dict[str, str]]:
    """Get all village records matching a name (exact match on original name)."""
    dataset = load_villages()
    return [row for row in dataset if row["village"].strip() == name]


def get_all_villages_by_normalized_name(name: str) -> List[Dict[str, str]]:
    """Get all village records matching a name by normalized base name."""
    normalized_name = _normalize_name(name)
    dataset = load_villages()
    results: List[Dict[str, str]] = []
    for row in dataset:
        candidate = _normalize_name(row["village"].strip())
        if candidate == normalized_name:
            results.append(row)
        elif candidate.startswith(normalized_name) and len(candidate) - len(normalized_name) <= 3:
            results.append(row)
    return results


def resolve_nearby_variants(village_names: List[str]) -> List[Dict[str, str]]:
    """Resolve multiple village names by choosing nearby duplicate records."""
    if len(village_names) == 1:
        return []

    groups = [get_all_villages_by_normalized_name(name) for name in village_names]
    groups = [group for group in groups if group]
    return _choose_best_records(groups)


def build_plan(villages: List[str], source: str = "User") -> Dict[str, object]:
    """Create a simple structured route plan from a list of village names."""
    dataset = load_villages()
    available_names = [row["village"].strip() for row in dataset]
    available_name_keys = {_normalize_name(name): name for name in available_names}

    matched: List[Dict[str, object]] = []
    suggested: List[Dict[str, object]] = []
    unresolved: List[str] = []

    exact_groups: List[tuple[str, List[Dict[str, str]]]] = []
    pending_names: List[str] = []

    for village in villages:
        raw_name = village.strip()
        if not raw_name:
            unresolved.append(raw_name)
            continue

        exact_key = _normalize_name(raw_name)
        canonical_name = available_name_keys.get(exact_key)
        if canonical_name:
            duplicates = get_all_villages_by_normalized_name(raw_name)
            if duplicates:
                exact_groups.append((raw_name, duplicates))
                continue

        pending_names.append(raw_name)

    if len(exact_groups) > 1:
        groups = [group for _, group in exact_groups]
        chosen_records = _choose_best_records(groups)
        for (raw_name, _), record in zip(exact_groups, chosen_records):
            matched.append({
                "name": raw_name,
                "canonical_name": _normalize_name(raw_name).title(),
                "status": "matched_duplicate",
                "district": record["district"],
                "subdistric": record["subdistric"],
                "latitude": float(record["latitude"]),
                "longitude": float(record["longitude"]),
            })
    else:
        for raw_name, duplicates in exact_groups:
            if len(duplicates) > 1:
                for duplicate in duplicates:
                    matched.append({
                        "name": raw_name,
                        "canonical_name": _normalize_name(raw_name).title(),
                        "status": "matched_duplicate",
                        "district": duplicate["district"],
                        "subdistric": duplicate["subdistric"],
                        "latitude": float(duplicate["latitude"]),
                        "longitude": float(duplicate["longitude"]),
                    })
            else:
                village_record = duplicates[0]
                matched.append({
                    "name": raw_name,
                    "canonical_name": _normalize_name(raw_name).title(),
                    "status": "matched",
                    "district": village_record["district"],
                    "subdistric": village_record["subdistric"],
                    "latitude": float(village_record["latitude"]),
                    "longitude": float(village_record["longitude"]),
                })

    for raw_name in pending_names:
        match_results = _find_best_matches(raw_name, available_names, top_n=3)
        if match_results:
            if match_results[0]["status"] == "matched":
                village_record = get_village_by_name(match_results[0]["suggested_match"])
                if village_record:
                    matched.append({
                        "name": raw_name,
                        "canonical_name": match_results[0]["suggested_match"],
                        "status": "matched",
                        "district": village_record["district"],
                        "subdistric": village_record["subdistric"],
                        "latitude": float(village_record["latitude"]),
                        "longitude": float(village_record["longitude"]),
                    })
                else:
                    unmatched = raw_name
                    unresolved.append(unmatched)
            else:
                for result in match_results:
                    village_record = get_village_by_name(result["suggested_match"])
                    if village_record:
                        suggested.append({
                            "input": raw_name,
                            "suggested_match": result["suggested_match"],
                            "status": "suggested",
                            "score": result["score"],
                            "district": village_record["district"],
                            "subdistric": village_record["subdistric"],
                            "latitude": float(village_record["latitude"]),
                            "longitude": float(village_record["longitude"]),
                        })
                unresolved.append(raw_name)
        else:
            unresolved.append(raw_name)

    return {
        "source": source,
        "requested_villages": villages,
        "matched_villages": matched,
        "suggested_villages": suggested,
        "unresolved_villages": unresolved,
        "total_matched": len(matched),
        "total_suggested": len(suggested),
        "total_requested": len(villages),
    }
