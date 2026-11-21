import json, sys
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))
for k in d:
    if any(s in k for s in ('PrimitiveData`', 'ReferenceData`', 'BasePrimitiveData', 'PrimitiveModel`', 'IntData', 'ReferenceMapData`')):
        print('===', k)
        for fn, fv in d[k]['fields'].items():
            print('  0x%-5X %-32s %s' % (fv['offset'], fn, fv['decl'][:70]))
