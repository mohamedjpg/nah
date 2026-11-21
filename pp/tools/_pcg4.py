import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

def show(k):
    c = d.get(k)
    if not c:
        print('MISSING', k); return
    print('===', k, 'kind=', c.get('kind'), 'size=', c.get('size'))
    for fn, fv in c['fields'].items():
        print('   F 0x%-5X %-44s %s' % (fv['offset'], fn, fv['decl'][:72]))
    for mn, mv in c['methods'].items():
        print('   M %-9s %s' % (hex(mv['rva']) if mv['rva'] else 'extern', mv['decl'][:95]))

for k in ['Models.Models.Random.RandomModel', 'Models.MathUtils.RandomUtils']:
    show(k)

print()
print('=== who owns RandomModel? (fields typed RandomModel) ===')
for k, c in d.items():
    for fn, fv in c['fields'].items():
        if 'RandomModel' in fv['decl'] and 'IPrimitive' not in fv['decl']:
            print('%-64s 0x%-5X %-34s %s' % (k, fv['offset'], fn, fv['decl'][:50]))
