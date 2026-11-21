import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k, 'size=', c.get('size'))
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-40s %s' % (fv['offset'], fn, fv['decl'][:70]))
    for mn, mv in c['methods'].items():
        r = mv['rva']
        print('   M %-9s %s' % (hex(r) if r else 'extern', mv['decl'][:95]))

for k in ['Models.Models.Roulette.RouletteModel',
          'Models.Utils.Extensions.Roulette.RouletteRules',
          'Models.Utils.Extensions.Roulette.RouletteExtensions']:
    show(k)

print()
print('=== classes mentioning Random/Seed/Rng in the name ===')
for k in sorted(d):
    low = k.lower()
    if ('roulette' in low and any(s in low for s in ('random','seed','rng','roll','spin','wheel'))):
        print(' ', k)
