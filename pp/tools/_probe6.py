import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))
for k in d:
    if 'RoulettePhaseDescription' in k:
        print('===', k)
        for fn, fv in d[k]['fields'].items():
            print('  0x%-5X %-30s %s' % (fv['offset'], fn, fv['decl'][:70]))
