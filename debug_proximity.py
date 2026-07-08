import csv
import math
from pathlib import Path

path = Path('telangana_villages.csv')
rows = list(csv.DictReader(path.open('r', encoding='utf-8-sig')))

balapurs = [r for r in rows if r['village'].strip().lower().startswith('balapur')]
mallapurs = [r for r in rows if r['village'].strip().lower().startswith('mallapur')]

print('balapur count', len(balapurs))
for b in balapurs:
    print('BALAPUR', b['village'], b['district'], b['subdistric'], b['latitude'], b['longitude'])
print('mallapur count', len(mallapurs))


def dist(a, b):
    return math.hypot(float(a['latitude']) - float(b['latitude']), float(a['longitude']) - float(b['longitude']))

best = None
for b in balapurs:
    for m in mallapurs:
        d = dist(b, m)
        if best is None or d < best[0]:
            best = (d, b, m)

print('best dist', best[0])
print('balapur', best[1]['village'], best[1]['district'], best[1]['subdistric'], best[1]['latitude'], best[1]['longitude'])
print('mallapur', best[2]['village'], best[2]['district'], best[2]['subdistric'], best[2]['latitude'], best[2]['longitude'])

print('\nNearby mallapurs to each balapur:')
for b in balapurs:
    for m in mallapurs:
        d = dist(b, m)
        if d < 0.5:
            print('balapur', b['district'], b['subdistric'], 'mallapur', m['district'], m['subdistric'], 'd', d)
