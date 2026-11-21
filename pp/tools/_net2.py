import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k)
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-40s %s' % (fv['offset'], fn, fv['decl'][:68]))
    for mn, mv in c['methods'].items():
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mv['decl'][:92]))

for k in ['ClientCore.BattleIncomingPackets.BattleDataPacket',
          'ClientCore.BattleIncomingPackets.InitBattleIncomingPacket',
          'Models.Replication.EntityStreamReader.RouletteEntityStreamReader',
          'Models.Replication.EntityDataBuilder.RouletteEntityDataBuilder']:
    show(k)

print()
print('=== classes with "Encrypt"/"Protect"/"Obfusc" in the name ===')
for k in sorted(d):
    if any(s in k for s in ('Encrypt', 'Protect', 'Obfusc')):
        print('  ', k)
