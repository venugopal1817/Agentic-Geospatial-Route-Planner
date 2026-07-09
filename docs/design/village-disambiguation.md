# Feature: Fuzzy Matching & Proximity-Based Village Disambiguation

## Overview

This feature resolves ambiguous village names and misspellings to produce reliable, actionable location matches for downstream route planning.

## Background

Field inputs are noisy: duplicate village names across districts, spelling mistakes, and variant suffixes (OG, MD) are common. Without robust resolution, route optimization and any decisions based on location are unreliable.

## Requirements

### Functional
- Accept a list of village names and a source location.
- Resolve each input to either: `matched` (unambiguous), `matched_duplicate` (ambiguous but selected via proximity), `suggested` (fuzzy candidate with score), or `unresolved`.
- For multi-village queries, choose combinations of duplicates that minimize total geographic distance.
- Return coordinates (latitude, longitude), district, subdistrict, and status for each result.

### Non-Functional
- Deterministic results given identical input and dataset
- Fast enough for interactive use on modest hardware (single-node CPU)
- Configurable similarity threshold for fuzzy matches
- Clear, machine-readable response format (JSON)

## Architecture

The feature is implemented inside `app/services/planner.py` and exposed via `POST /plan` in `app/main.py`.
Key functions:
- `_normalize_name(name)` — canonicalizes input strings
- `_edit_distance(s1, s2)` + similarity conversion — fuzzy scoring
- `get_all_villages_by_normalized_name()` — returns exact + variant matches
- `_distance(coord1, coord2)` — Euclidean approximation for close-proximity selection
- `_choose_best_records(exact_groups)` — combinatorial selection minimizing total distance
- `build_plan(source, villages)` — orchestrates the above into final response

## Design Decisions

### Why Levenshtein + Threshold (0.5)
Levenshtein is simple, well-understood, and deterministic. A similarity threshold of 0.5 provides recall for realistic user typos (drastic misspellings ~0.6–0.7 still surface candidates) while keeping precision acceptable.

### Why Euclidean distance for proximity
The dataset spans relatively small geographic areas (state/regional scale). For disambiguation a planar Euclidean distance serves as an inexpensive proxy to great-circle distance. For production and large geographic spans this should be replaced with haversine/orthodromic distance.

### Why combinatorial minimization via itertools.product
The number of duplicate groups in multi-village queries is usually small (2–4). Exhaustive combination evaluation is simple and guarantees global minimal total-distance selection given small groups. For larger group sizes, heuristics or ILP formulations (OR-Tools) are planned.

## Alternatives Considered
- Soundex/Metaphone for phonetic matching — rejected because local spelling variations are better captured by edit distance for this dataset.
- Off-the-shelf fuzzy libraries (`fuzzywuzzy`, `rapidfuzz`) — considered but rejected to keep the prototype dependency-light and deterministic.
- Haversine vs Euclidean — Euclidean chosen for speed in Phase 1; plan to switch to haversine in Phase 2 if necessary.

## Implementation Details

### Modules and Key Functions
- `Planner` (module-level functions inside `app/services/planner.py`)
  - `load_villages()` — Loads CSV into memory; precomputes normalized names.
  - `_normalize_name()` — Lowercases, trims, removes punctuation and common suffixes.
  - `_edit_distance()` and similarity scoring — Returns float in [0,1].
  - `get_all_villages_by_normalized_name()` — Returns candidate records including suffix variants (±3 chars).
  - `_choose_best_records()` — Uses `itertools.product` to evaluate combinations and select the minimal total-distance result.
  - `build_plan()` — Top-level orchestration: exact match → dedupe & proximity selection → fuzzy suggestions.

### Engineering Reasoning
- Keep dataset in-memory for fast lookups during interactive prototyping. This simplifies the dependency graph and reduces infra overhead.
- Determinism prioritized for reproducible debugging and for generating unit tests with stable expectations.
- Explicit status tags in response (`matched`, `matched_duplicate`, `suggested`, `unresolved`) support downstream UI decisions and user-facing explanations.

## Edge Cases
- Multiple duplicates in >4 groups can lead to combinatorial explosion; current algorithm may be slow.
- Very large spelling errors (random characters) may return irrelevant suggestions; threshold tuning mitigates this.
- Missing or malformed coordinates in CSV -> record skipped but logged.
- Identical coordinates across different administrative areas (rare) -> distance-based tie-breaking is ambiguous.

## Performance Considerations
- Complexity: For N input villages and G duplicate groups with sizes s1..sG, combination evaluation is O(product(si)) — tractable for small G but exponential in worst-case.
- Memory: Entire CSV loaded to memory — OK for 3k records; consider DB or vector index for larger datasets.
- Optimization: Replace exhaustive search with OR-Tools/ILP for larger combination spaces; use haversine for accuracy in wide-area queries.

## Future Improvements
- Replace Euclidean with haversine for accurate distances.
- Add `rapidfuzz` for faster fuzzy comparisons with C-accelerated performance.
- Move village records into a vector DB (FAISS/Pinecone) for semantic retrieval and scalable RAG.
- Integrate LangGraph to orchestrate multi-agent flows and make disambiguation interactive (clarification questions to user).
- Add configurable rules for administrative precedence (e.g., prefer same district as `source`).

## Lessons Learned
- Normalization dramatically increases match rates — small preprocessing yields outsized benefits.
- Geographic proximity is a reliable signal for multi-village disambiguation.
- Thresholds require iteration against real user data.
- Prototyping with minimal external dependencies speeds feedback loops and reduces friction.

## Files & Links
- `app/services/planner.py`
- `app/main.py` (API)
- `tests/test_planner.py`


