import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))
for k in d:
    if k.endswith('.InventoryItemModel') or 'IInventoryItemModel' in k or k.endswith('.VehicleTypeDescription') or k.endswith('.PlayerRoleDescription'):
        print('===', k)
        for fn, fv in d[k]['fields'].items():
            print('  0x%-5X %-34s %s' % (fv['offset'], fn, fv['decl'][:70]))
