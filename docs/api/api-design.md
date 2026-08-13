# API Design

## Request flow

### POST /plan-text

Request:

```json
{
  "request_text": "I need to visit Balapur, Mallapur and Chintapalli from Hyderabad"
}
```

Possible responses:

- `planning` when the system can continue without ambiguity
- `clarification_required` when multiple candidates match
- `error` when validation fails

### POST /clarification

Request:

```json
{
  "session_id": "session-123",
  "selected_option_id": "loc_001"
}
```

### GET /health

Returns: `{ "status": "ok" }`
