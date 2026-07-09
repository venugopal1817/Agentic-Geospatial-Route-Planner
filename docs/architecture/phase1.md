# Phase 1 Architecture — Foundation

## Overview

This document describes the Phase 1 architecture for the Agentic Geospatial Route Planner: the thin, robust foundation that proves the core village-matching and disambiguation logic.

## Goals

- Validate core matching logic against real-world data (telangana_villages.csv)
- Provide a reproducible REST API surface for integration and testing
- Keep architecture minimal to reduce surface area for bugs

## Components

- FastAPI service (`app/main.py`) — HTTP API accepting plan requests
- Planner service (`app/services/planner.py`) — core matching and disambiguation logic
- CSV data source (`telangana_villages.csv`) — canonical village records with lat/lon
- Tests (`tests/test_planner.py`) — regression coverage for key scenarios

## Data Flow

1. Client posts `POST /plan` with `source` and list of `villages`.
2. FastAPI validates request and forwards to `Planner.build_plan()`.
3. Planner loads villages dataset (CSV), normalizes inputs, and attempts exact match.
4. If duplicates are found across multiple requested villages, Planner computes pairwise distances and chooses the minimal-total-distance combination.
5. If exact match fails, Planner runs fuzzy matching using Levenshtein edit distance and returns suggested matches with scores.
6. Response JSON contains `matched`, `suggested`, and `unresolved` lists with coordinates and metadata.

## Non-Goals (Phase 1)

- No agents orchestration (LangGraph) — deferred to Phase 2
- No vector DB / RAG system — deferred to Phase 2/3
- No interactive map rendering — deferred to Phase 2

## Deployment

Phase 1 is validated locally via Uvicorn (`uvicorn app.main:app --host 127.0.0.1 --port 8000`). Containerization and cloud deployment are scheduled in Phase 3.

## Observability

Local logs + pytest test reports are used for validation. Full observability (Langfuse/OpenTelemetry) is scheduled for Phase 4.

## Diagrams
- Component and sequence diagrams live in `docs/architecture/component-diagram.md` and `docs/architecture/sequence-diagram.md` (textual placeholders in this repo).