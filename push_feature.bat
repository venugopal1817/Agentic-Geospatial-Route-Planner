@echo off
cd c:\Venu_projects\venu_portfolio\Agentic-Geospatial-Route-Planner

git checkout -b feature/village-disambiguation

git add app/services/planner.py app/main.py requirements.txt tests/test_planner.py

git commit -m "feat: implement proximity-based village disambiguation and fuzzy matching

- Add geographic proximity scoring for duplicate villages
- Implement multi-village disambiguation using coordinate distance
- Add fuzzy matching with edit distance for misspelled village names
- Support top 3 suggestions for close matches
- Return coordinates (lat/lon) and district info for all matches
- Handle village variants (e.g., 'Balapur' and 'Balapur OG')
- Add regression tests for disambiguation logic"

echo.
echo Feature branch created and changes committed.
echo.
git branch
