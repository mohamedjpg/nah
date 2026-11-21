import json, sys

p = r'D:\tools2\dumpss\robrun\newasmbly\script.json'
d = json.load(open(p, encoding='utf-8'))
sm = d['ScriptMethod']

want = [
    'Models.Models.Roulette.RouletteModel$$AddBet',
    'Models.Models.Roulette.RouletteModel$$get_WinningNumber',
    'Models.Models.Roulette.RouletteModel$$get_Phase',
    'Models.Models.Roulette.RouletteModel$$get_PhaseEndTs',
    'Models.Models.WorldEntities.WorldEntitiesModel$$get_RouletteModels',
]
for w in want:
    hit = None
    for m in sm:
        if m['Name'] == w:
            hit = m
            break
    if hit:
        print(f"{w}\n    addr=0x{hit['Address']:X}  dec={hit['Address']}")
    else:
        print(f"{w}\n    NOT FOUND")

# Also list any method whose name contains RouletteBetDescriptions / Chip
print('\n--- description statics ---')
for m in sm:
    n = m['Name']
    if 'RouletteBetDescriptions' in n or 'RouletteChipDescriptions' in n:
        print(f"{n}  0x{m['Address']:X}")
