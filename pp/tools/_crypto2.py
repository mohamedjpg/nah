import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k, 'kind=', c.get('kind'))
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-40s %s' % (fv['offset'], fn, fv['decl'][:70]))
    for mn, mv in c['methods'].items():
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mv['decl'][:95]))

show('BattleCryptoUpdater')
print()
print('=== Kefir framework classes (all) ===')
for k in sorted(d):
    if k.startswith('Kefir'):
        print('  ', k)
