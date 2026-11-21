import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

print('=== who references RouletteCheatModel ===')
for k, c in d.items():
    for fn, fv in c['fields'].items():
        if 'RouletteCheatModel' in fv['decl']:
            print('  FIELD %-58s 0x%-5X %-30s %s' % (k, fv['offset'], fn, fv['decl'][:50]))
    for mn, mv in c['methods'].items():
        if 'RouletteCheat' in mn:
            print('  METH  %-58s %s' % (k, mn))

print()
print('=== RouletteCheatModel full ===')
c = d['Models.Models.Roulette.RouletteCheatModel']
for fn, fv in c['fields'].items():
    print('   F 0x%-5X %-42s %s' % (fv['offset'], fn, fv['decl']))
print('   -- methods with real bodies (rva not in tiny-stub range):')
for mn, mv in c['methods'].items():
    print('   M 0x%-9X %s' % (mv['rva'] if mv['rva'] else 0, mn))
