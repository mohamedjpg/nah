import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

# Any roulette class whose fields or methods mention random/seed
print('=== roulette classes touching RNG ===')
hits = 0
for k, c in d.items():
    if 'oulette' not in k:
        continue
    for fn, fv in c['fields'].items():
        if any(s in fn.lower() for s in ('random', 'seed', 'rng')):
            print('  FIELD %s.%s' % (k, fn)); hits += 1
    for mn in c['methods']:
        if any(s in mn.lower() for s in ('random', 'seed', 'rng', 'next')):
            print('  METH  %s.%s' % (k, mn)); hits += 1
print('hits:', hits)

print()
print('=== the client-side roulette entity chain ===')
for k in ['Game.Battle.EntityModel.Roulette.RouletteEntityModel',
          'Game.Battle.EntityModel.Roulette.RouletteClientModel',
          'Game.Battle.EntityModel.Roulette.RouletteModelUpdater',
          'Game.Battle.EntityModel.Roulette.RouletteWheelView']:
    c = d.get(k)
    if not c:
        print('MISSING', k); continue
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-42s %s' % (fv['offset'], fn, fv['decl'][:66]))
