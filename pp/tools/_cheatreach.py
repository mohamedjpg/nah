import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-44s %s' % (fv['offset'], fn, fv['decl'][:66]))
    for mn, mv in list(c['methods'].items())[:14]:
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mn))

show('Game.Battle.BattleModel')
print()
show('ClientCore.ApplyDataUpdater.ApplyDataUpdater')
print()
print('=== any field whose decl mentions "Cheat" and is a model ===')
for k, c in d.items():
    for fn, fv in c['fields'].items():
        dec = fv['decl']
        if 'Cheat' in dec and ('Model' in dec):
            print('  %-62s 0x%-5X %-30s %s' % (k, fv['offset'], fn, dec[:46]))
