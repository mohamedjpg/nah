import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-44s %s' % (fv['offset'], fn, fv['decl'][:64]))
    for mn, mv in list(c['methods'].items())[:10]:
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mn))

for k in ['Game.Battle.CheatSpawnCarModel', 'Models.Models.CheatSpawnCar.CheatSpawnCarModel',
          'Game.Battle.CheatSpawnHelicopterModel', 'Game.Shared.NetworkStatusModel',
          'Game.Battle.Network.BattleIncomingPacketsUpdater']:
    show(k)

print()
print('=== search for CheatSpawnCarModel / NetworkStatusModel by suffix ===')
for k in sorted(d):
    if k.endswith('CheatSpawnCarModel') or k.endswith('CheatSpawnHelicopterModel') or k.endswith('NetworkStatusModel'):
        print('  ', k)
