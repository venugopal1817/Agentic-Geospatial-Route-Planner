# Intent Processing

The intent parser converts natural-language user requests into a validated schema.

## Example

Input:

> I need to start from Hyderabad and visit Balapur, Mallapur and Chintapalli.

Structured output:

```json
{
  "origin": "Hyderabad",
  "destinations": ["Balapur", "Mallapur", "Chintapalli"],
  "travel_intent": "visit_locations",
  "optimization_goal": "minimum_distance"
}
```

## Rules

- Raw LLM output is never trusted directly.
- Output must validate against a typed schema.
- Intent parsing is only the interpretation layer.
- Actual village matching still happens in the deterministic service layer.
