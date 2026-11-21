import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-40s %s' % (fv['offset'], fn, fv['decl'][:68]))
    ms = list(c['methods'].items())
    for mn, mv in ms[:25]:
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mn))

for k in ['ClientCore.Models.CheatModel.CheatModel',
          'ClientCore.Models.CheatModel.ICheatModel',
          'Models.Models.Roulette.RouletteCheatModel']:
    show(k)

print()
print('=== anything gating cheats: permission / isCheat / dev ===')
for k, c in d.items():
    for fn, fv in c['fields'].items():
        low = fn.lower()
        if ('cheat' in low or 'permission' in low) and 'decl' in fv:
            print('  %-64s 0x%-5X %s' % (k, fv['offset'], fv['decl'][:50]))
