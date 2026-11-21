import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-44s %s' % (fv['offset'], fn, fv['decl'][:64]))
    for mn, mv in list(c['methods'].items())[:12]:
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mn))

for k in ['Game.Battle.Cheats.CheatSpawnCarModel', 'Game.Battle.Cheats.CheatSpawnHelicopterModel']:
    show(k)

print()
print('=== who owns NetworkStatusModel? ===')
for k, c in d.items():
    for fn, fv in c['fields'].items():
        if 'NetworkStatusModel' in fv['decl']:
            print('  %-58s 0x%-5X %-32s %s' % (k, fv['offset'], fn, fv['decl'][:44]))

print()
print('=== EosAntiCheatModel ===')
show('Game.Global.EpicOnlineServices.EosAntiCheatModel')
