# Clarification Flow

When multiple candidate villages match the same user query, the system must stop and ask the user.

## Flow

1. Parse natural-language request.
2. Use retrieval against the dataset.
3. Gather all candidates for each destination.
4. If any destination has more than one candidate, raise a clarification state.
5. Return structured clarification payload to the client.
6. User selects the correct option.
7. Resume the flow with the confirmed destination.

## Response example

```json
{
  "status": "clarification_required",
  "question": "We found multiple locations matching 'Balapur'. Which one do you mean?",
  "options": [
    {"id": "loc_001", "name": "Balapur", "district": "Ranga Reddy"},
    {"id": "loc_002", "name": "Balapur", "district": "Another District"}
  ]
}
```
