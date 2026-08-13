# Final Architecture

```mermaid
flowchart TD
    U[User natural-language request] --> API[Frontend / API Layer]
    API --> ORCH[Agent / Orchestrator]
    ORCH --> NLP[LLM Intent Parser]
    NLP --> SCHEMA[Typed Request Schema]
    SCHEMA --> RAG[RAG Retrieval Layer]
    RAG --> DATASET[Trusted Village Dataset]
    DATASET --> RESOLVE[Village Resolution Service]
    RESOLVE --> AMBIG{Ambiguous?}

    AMBIG -- Yes --> CLARIFY[Clarification API / User Selection]
    CLARIFY --> RESUME[Resume Planning Session]
    RESUME --> CONFIRM[Confirmed Locations]

    AMBIG -- No --> CONFIRM

    CONFIRM --> VALIDATE[Validation Service]
    VALIDATE --> DIST[Distance Matrix Service]
    DIST --> ROUTE[Deterministic Route Optimizer]
    ROUTE --> SUMMARY[Final Route + Explanation]

    SUMMARY --> LLM[LLM Response Summarizer]
    LLM --> USER[Final User Response]
```

## Principle

- LLM handles understanding and orchestration.
- RAG retrieves from the trusted village dataset.
- Deterministic services validate coordinates and compute routes.
- Ambiguity triggers user clarification before route optimization.
