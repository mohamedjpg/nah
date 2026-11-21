import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))
for k in ['Models.Data.RouletteData', 'Game.Battle.EntityModel.Roulette.RouletteDialog.RouletteDialogModel',
          'Models.Models.Roulette.RouletteCheatModel', 'Models.References.Roulette.RouletteChipDescription',
          'Models.References.Roulette.RouletteBetDescription', 'Models.Models.Roulette.CharacterRouletteRewardModel']:
    print('===', k, k in d)
    if k in d:
        for fn, fv in d[k]['fields'].items():
            print('  0x%-5X %-42s %s' % (fv['offset'], fn, fv['decl'][:78]))
