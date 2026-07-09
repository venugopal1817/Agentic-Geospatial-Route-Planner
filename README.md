# Building an Agentic Geospatial Route Planner: Phase 1 Foundation

**LinkedIn / Medium blog style technical README**

---

## The Problem That Started It All

Field teams often need to visit multiple villages or locations across regions. The reality:

- Route planning is **manual** and spreadsheet-driven
- Heavily dependent on **local knowledge**
- **Time consuming** and error-prone
- No intelligent validation or decision support

A common example for Telangana:

- There are **2 villages named "Balapur"** (Adilabad district & Ranga Reddy district)
- There are **20 villages named "Mallapur"** across different districts
- Which combination is the best choice for a visit plan?

**This prototype proves that agentic geospatial intelligence can resolve ambiguity, suggest corrections, and support route planning decisions.**

---

## Phase 1: What We Built

In Phase 1, we built the foundation of the Agentic Geospatial Route Planner:

1. **FastAPI REST Service** for accepting route planning requests
2. **Village Matching Engine** for resolving names, duplicates, and variants
3. **Fuzzy Matching Logic** for spelling errors and close matches
4. **Proximity-Based Disambiguation** for duplicate village selections
5. **Regression Tests** to validate core edge cases

**Key repository files:**
- `app/main.py`
- `app/services/planner.py`
- `tests/test_planner.py`
- `telangana_villages.csv`

---

## Why This Feature Was Required

Field location input is noisy. When users type village names, the system must handle:

- Duplicate names across districts
- Variant spellings and suffixes (`OG`, `MD`, `_`)
- Human typos and transcription errors
- Conflicting results for multi-village queries

Without robust matching, any route plan built on this data is unreliable.

---

## What We Implemented

### 1. String Normalization for Robust Matching

User text is not reliable. We normalize village names before comparing.

```python
return name.lower().strip().replace('_', ' ')
```

This prevents failures from capitalization, whitespace, and simple formatting differences.

---

### 2. Levenshtein Edit Distance for Fuzzy Matching

Users often misspell village names.
We compute edit distance and convert it into a similarity score.

```python
similarity = 1 - (distance / max_len)
```

A **0.5 threshold** was selected for this prototype to balance recall and precision.

---

### 3. Disambiguation for Duplicate Villages

When a name maps to multiple records, we keep all matches and use cross-query context to resolve ambiguity.

```python
if village_norm == norm_name:
    matches.append(village)
elif village_norm.startswith(norm_name) and len(village_norm) <= len(norm_name) + tolerance:
    matches.append(village)
```

This handles variants such as `Balapur` and `Balapur OG`.

---

### 4. Geographic Proximity-Based Selection

For queries like `['Balapur', 'Mallapur']`, the system evaluates candidate combinations and chooses the pair with the smallest total distance.

This is the key disambiguation signal for multi-village inputs.

---

### 5. Structured API Responses with Metadata

The response includes:
- `matched`
- `suggested`
- `unresolved`

Each item returns coordinates, district data, and status metadata so the caller can reason about results.

```json
{
  "name": "Gudur",
  "score": 0.85,
  "status": "suggested",
  "district": "Vikarabad"
}
```

---

## Technical Architecture

```
FastAPI Server (Port 8000)
    ↓
POST /plan → Planner Service
    ├── Load villages from CSV
    ├── Normalize input names
    ├── Try exact matching → normalized matching
    ├── If duplicates exist across requested villages → apply proximity selection
    ├── If no exact match → fuzzy matching with Levenshtein distance
    ├── Return ranked suggestions
    └── Return structured JSON response
```

**Stack:**
- FastAPI
- Pydantic
- Uvicorn
- Python 3.11
- pytest

---

## Testing: Proving It Works

### Test cases covered

1. **Exact match + unresolved fallback**
2. **Fuzzy suggestions for misspellings**
3. **Duplicate village disambiguation using geographic proximity**

These tests ensure the core matching logic is stable and ready for the next phase.

---

## Next Steps

This foundation is ready for Phase 2:

- Validate village data with a dedicated agent
- Add route optimization using OR-Tools
- Generate interactive maps with map APIs
- Introduce LangGraph for multi-agent orchestration

---

## Learnings

- Normalization is the first and most valuable step in text matching
- Geographic proximity is a powerful disambiguation signal
- Threshold tuning is essential for fuzzy search
- Structured metadata makes results actionable and debuggable

---

## How to Use

Run locally:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Send a POST request to `/plan` with a JSON body:

```json
{
  "source": "Hyderabad",
  "villages": ["Balapur", "Mallapur", "Nalgonda"]
}
```

---

## Publishing Notes

This README doubles as a Phase 1 technical blog post for Medium or LinkedIn because it includes:
- Problem definition
- implemented solution
- technical reasoning
- code snippets
- results and next steps

If you want, I can also create a separate `docs/feature-readme.md` that is exactly optimized for Medium formatting.
