import json, re
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

print('=== every field whose name mentions seed ===')
n = 0
for k, c in d.items():
    for fn, fv in c['fields'].items():
        if 'seed' in fn.lower():
            print('%-70s 0x%-5X %s' % (k, fv['offset'], fv['decl'][:60]))
            n += 1
print('total', n)

print()
print('=== methods whose name mentions Seed / Random / Winning ===')
for k, c in d.items():
    for mn, mv in c['methods'].items():
        low = mn.lower()
        if any(s in low for s in ('seed', 'random', 'winningnumber', 'getnext')):
            print('%-72s %-9s %s' % (k, hex(mv['rva']) if mv['rva'] else 'extern', mn))
