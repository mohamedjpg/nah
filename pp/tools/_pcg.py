import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

print('=== PCG32 ===')
for k in d:
    if 'PCG' in k or 'Pcg' in k:
        c = d[k]
        print(k, 'kind=', c.get('kind'), 'size=', c.get('size'))
        for fn, fv in c['fields'].items():
            print('   F 0x%-5X %-30s %s' % (fv['offset'], fn, fv['decl'][:70]))
        for mn, mv in c['methods'].items():
            r = mv['rva']
            print('   M %-8s %s' % (hex(r) if r else 'extern', mv['decl'][:90]))
