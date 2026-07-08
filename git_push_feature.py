#!/usr/bin/env python
import subprocess
import os
import sys

os.chdir(r'c:\Venu_projects\venu_portfolio\Agentic-Geospatial-Route-Planner')

commands = [
    ['git', 'checkout', '-b', 'feature/village-disambiguation'],
    ['git', 'add', '.'],
    ['git', 'commit', '-m', '''feat: implement proximity-based village disambiguation and fuzzy matching

- Add geographic proximity scoring for duplicate villages
- Implement multi-village disambiguation using coordinate distance
- Add fuzzy matching with edit distance for misspelled village names
- Support top 3 suggestions for close matches
- Return coordinates (lat/lon) and district info for all matches
- Handle village variants (e.g., 'Balapur' and 'Balapur OG')
- Add regression tests for disambiguation logic'''],
    ['git', 'branch', '-v']
]

for cmd in commands:
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

print("\n" + "="*60)
print("SUCCESS: Feature branch created with all changes committed!")
print("="*60)
print("\nNext step: Run 'git push origin feature/village-disambiguation'")
