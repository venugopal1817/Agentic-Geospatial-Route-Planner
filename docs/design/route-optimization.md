# Route Optimization

The final route engine is deterministic and works only on confirmed village records.

## Process

1. Confirm each destination is a trusted village record.
2. Validate coordinates.
3. Compute pairwise distances using the Haversine formula.
4. Build a distance matrix.
5. Select route order using nearest-neighbor optimization.
6. Return ordered stops plus total distance.

## Security rule

The LLM never decides the route or the distance. It only explains the final computed result.
