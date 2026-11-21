#!/usr/bin/env python3
"""Re-sync the generated offset headers from an Il2CppDumper dump.cs.

Reads 2_src_port/robrun_offsets.h and 2_src_port/robrun_sdk_offsets.h, resolves
every RR_* macro against the dump, rewrites the values that moved and reports
macros the dump can no longer resolve (removed or renamed fields).

    python sync_offsets_from_dump.py                  # rewrite in place
    python sync_offsets_from_dump.py --check          # report only, exit 1 on drift
    python sync_offsets_from_dump.py --dump path\\dump.cs

The macro -> (class, field, namespace) table below is the contract: it mirrors
offsets/robrun_offsets.json and offsets/robrun_sdk_offsets.json. Add a row when
a new macro is introduced; the script only ever writes values, never names.
"""

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DUMP = ROOT.parent.parent / 'newasmbly' / 'dump.cs'
HEADER_DIR = ROOT / '2_src_port'
HEADERS = ('robrun_offsets.h', 'robrun_sdk_offsets.h')

# macro, class (simple name), field, namespace hint
SPECS = [
    ('RR_OFF_AIM_BATTLE', 'BattleAimTargetUpdater', '_battleEntitiesModel', 'Game.Battle.Entities.Player.Updaters'),
    ('RR_OFF_AIM_BRAIN', 'BattleAimTargetUpdater', '_cinemachineBrain', 'Game.Battle.Entities.Player.Updaters'),
    ('RR_OFF_BATTLE_AIM', 'BattleModel', '<AimTargetModel>k__BackingField', 'Game.Battle'),
    ('RR_OFF_BATTLE_CAMERA', 'BattleModel', '<BattleCameraModel>k__BackingField', 'Game.Battle'),
    ('RR_OFF_BATTLE_ENTITIES', 'BattleModel', '<BattleEntitiesModel>k__BackingField', 'Game.Battle'),
    ('RR_OFF_BATTLE_MODELS', 'BattleEntitiesModel', '_models', 'Game.Battle'),
    ('RR_OFF_BATTLE_PLAYER_SLOTS', 'BattleModel', '<BattleCharacterSlotsModel>k__BackingField', 'Game.Battle'),
    ('RR_OFF_BATTLE_SLOTS', 'BattleEntitiesModel', '_characterSlotModel', 'Game.Battle'),
    ('RR_OFF_BATTLE_VOICE_ROOM', 'BattleModel', '<VoiceChatBattleRoomModel>k__BackingField', 'Game.Battle'),
    ('RR_OFF_BATTLE_WORLD', 'BattleEntitiesModel', '_worldEntitiesModel', 'Game.Battle'),
    ('RR_OFF_CAR_DESC', 'CarModel', '<Description>k__BackingField', 'Models.Models.Car'),
    ('RR_OFF_CAR_ID', 'CarModel', '<Id>k__BackingField', 'Models.Models.Car'),
    ('RR_OFF_CAR_OWNER_ROLE', 'CarModel', '<OwnerRole>k__BackingField', 'Models.Models.Car'),
    ('RR_OFF_CAR_SEATS', 'CarModel', '<Seats>k__BackingField', 'Models.Models.Car'),
    ('RR_OFF_CAR_TRANSFORM', 'CarModel', '<Transform>k__BackingField', 'Models.Models.Car'),
    ('RR_OFF_CHAR_CONFIG', 'BattleCharacterModel', '<Config>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_CROUCH', 'BattleCharacterModel', '<CrouchModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_DATA', 'BattleCharacterModel', '<Data>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_ID', 'BattleCharacterModel', '<Id>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_INVEH', 'BattleCharacterModel', '<InVehicleModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_ISDEAD', 'BattleCharacterModel', '<IsDead>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_LOOK_DIR', 'BattleCharacterModel', '<LookDirection>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_PBM', 'BattleCharacterModel', '<PlayerBattleModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_PRIVATE', 'BattleCharacterModel', '<PrivateModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_REPL_TRANSFORM', 'BattleCharacterModel', '<ReplicatedTransform>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_SKELETON', 'BattleCharacterModel', '<SkeletonModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_STANCE', 'BattleCharacterModel', '<BattleStanceModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_STATE', 'BattleCharacterModel', '<StateModel>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_TRANSFORM', 'BattleCharacterModel', '<Transform>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_CHAR_WEAPON', 'BattleCharacterModel', '<Weapon>k__BackingField', 'Models.Models.BattleCharacter'),
    ('RR_OFF_COMMON_ITEM_IN_HANDS', 'BattleCharacterCommonData', '<ItemInHands>k__BackingField', 'Models.Data'),
    ('RR_OFF_CONTAINER_INV', 'ContainerModel', 'Inventory', 'Models.Models.Container'),
    ('RR_OFF_CONTAINER_POS', 'ContainerModel', '<PositionModel>k__BackingField', 'Models.Models.Container'),
    ('RR_OFF_DOOR_POS', 'DoorModel', '<Position>k__BackingField', 'Models.Models.Door'),
    ('RR_OFF_DOOR_STATE', 'DoorModel', '<State>k__BackingField', 'Models.Models.Door'),
    ('RR_OFF_DOOR_STATE_DATA', 'DoorStateModel', '_state', 'Models.Models.DoorState'),
    ('RR_OFF_DROPPED_LOOT_POS', 'LootModel', '<InteractPositionModel>k__BackingField', 'Models.Models.LootModel'),
    ('RR_OFF_ENTRY_GAME', 'UnityEntry', '_game', 'Start'),
    ('RR_OFF_GAME_BATTLE', 'GameModel', '_battleModel', 'Game'),
    ('RR_OFF_GAME_MODEL', 'Game', '<GameModel>k__BackingField', 'Game'),
    ('RR_OFF_HELI_DESC', 'HelicopterModel', '<Description>k__BackingField', 'Models.Models.Helicopter'),
    ('RR_OFF_HELI_ID', 'HelicopterModel', '<Id>k__BackingField', 'Models.Models.Helicopter'),
    ('RR_OFF_HELI_OWNER_ROLE', 'HelicopterModel', '<OwnerRole>k__BackingField', 'Models.Models.Helicopter'),
    ('RR_OFF_HELI_SEATS', 'HelicopterModel', '<Seats>k__BackingField', 'Models.Models.Helicopter'),
    ('RR_OFF_HELI_TRANSFORM', 'HelicopterModel', '<Transform>k__BackingField', 'Models.Models.Helicopter'),
    ('RR_OFF_HIDDEN_ID_DATA', 'CharacterHideObjectStateModel', '_hideObjectEntityIdData', 'Models.Models.CharacterHideObjectState'),
    ('RR_OFF_HIDE_DESC', 'HideObjectModel', '<Description>k__BackingField', 'Models.Models.HideObject'),
    ('RR_OFF_HIDE_DESC_ID', 'LocationHideObjectDescription', '<EntityId>k__BackingField', 'Models.References.HideObject'),
    ('RR_OFF_HIDE_DESC_INTERACT', 'LocationHideObjectDescription', '<InteractPoint>k__BackingField', 'Models.References.HideObject'),
    ('RR_OFF_HIDE_DESC_POS', 'LocationHideObjectDescription', '<Position>k__BackingField', 'Models.References.HideObject'),
    ('RR_OFF_HIDE_DESC_ROT', 'LocationHideObjectDescription', '<Orientation>k__BackingField', 'Models.References.HideObject'),
    ('RR_OFF_HIDE_DESC_TYPE', 'LocationHideObjectDescription', '<HideObjectDescriptionFunc>k__BackingField', 'Models.References.HideObject'),
    ('RR_OFF_HIDE_OCCUPANT', 'HideObjectModel', '_entityId', 'Models.Models.HideObject'),
    ('RR_OFF_INVEH_ID', 'InVehicleModel', '_entityId', 'Models.Models.InVehicle'),
    ('RR_OFF_INVEH_TYPE', 'InVehicleModel', '_vehicleType', 'Models.Models.InVehicle'),
    ('RR_OFF_INVEH_VEHICLE', 'InVehicleModel', 'Vehicle', 'Models.Models.InVehicle'),
    ('RR_OFF_POS_X', 'PositionModel', '<X>k__BackingField', 'Models.Models.PositionModel'),
    ('RR_OFF_POS_Y', 'PositionModel', '<Y>k__BackingField', 'Models.Models.PositionModel'),
    ('RR_OFF_POS_Z', 'PositionModel', '<Z>k__BackingField', 'Models.Models.PositionModel'),
    ('RR_OFF_RM_BETS_BY_CHAR', 'RouletteModel', '_betsByCharacter', 'Models.Models.Roulette'),
    ('RR_OFF_RM_PHASE', 'RouletteModel', '<Phase>k__BackingField', 'Models.Models.Roulette'),
    ('RR_OFF_RM_PHASE_END', 'RouletteModel', '<PhaseEndTs>k__BackingField', 'Models.Models.Roulette'),
    ('RR_OFF_RM_WIN_NUMBER', 'RouletteModel', '<WinningNumber>k__BackingField', 'Models.Models.Roulette'),
    ('RR_OFF_SEATS_DATA', 'VehicleSeatsModel', '_data', 'Models.Models.VehicleSeats'),
    ('RR_OFF_SEAT_ENTITY_ID', 'VehicleSeatData', '<EntityId>k__BackingField', 'Models.Data.Vehicle'),
    ('RR_OFF_SEAT_OCCUPIED', 'VehicleSeatData', '<Occupied>k__BackingField', 'Models.Data.Vehicle'),
    ('RR_OFF_SLOTS_DICTIONARY', 'BattleCharacterSlotsModel', '_slots', 'Models.Models.BattleCharacterSlots'),
    ('RR_OFF_SLOT_DATA', 'BattleCharacterSlotModel', '_data', 'Models.Models.BattleCharacterSlots'),
    ('RR_OFF_SLOT_DESC', 'BattleCharacterSlotModel', '<Description>k__BackingField', 'Models.Models.BattleCharacterSlots'),
    ('RR_OFF_SLOT_ENTITY_ID', 'BattleCharacterSlotData', '<EntityId>k__BackingField', 'Models.Data'),
    ('RR_OFF_SLOT_NICKNAME', 'BattleCharacterSlotData', '<Nickname>k__BackingField', 'Models.Data'),
    ('RR_OFF_SLOT_USER_ID', 'BattleCharacterSlotData', '<EOSProductUserId>k__BackingField', 'Models.Data'),
    ('RR_OFF_STATE_HIDDEN', 'BattleCharacterStateModel', '_characterHiddenStateModel', 'Models.Models.BattleCharacterStateModel'),
    ('RR_OFF_VEHICLE_LOOT_POS', 'VehicleLootModel', '<InteractPositionModel>k__BackingField', 'Models.Models.VehicleLootModel'),
    ('RR_OFF_VIEWS_BATTLE', 'BattleEntitiesUpdater', '_battleEntitiesModel', 'Game.Battle'),
    ('RR_OFF_VIEWS_CARS', 'BattleEntitiesUpdater', '_carEntityViews', 'Game.Battle'),
    ('RR_OFF_VIEWS_CHARACTERS', 'BattleEntitiesUpdater', '_characterEntityViews', 'Game.Battle'),
    ('RR_OFF_VIEWS_HELICOPTERS', 'BattleEntitiesUpdater', '_helicopterEntityViews', 'Game.Battle'),
    ('RR_OFF_VIEWS_MODEL', 'BattleEntitiesUpdater', '_battleModel', 'Game.Battle'),
    ('RR_OFF_VOICE_HIDE_ID', 'VoiceChatBattleParticipantModel', '<HideObjectEntityId>k__BackingField', 'Game.Battle.VoiceChat'),
    ('RR_OFF_VOICE_ROOM_PARTICIPANTS', 'VoiceChatRoomModel', 'ParticipantsModel', 'Game.Global.VoiceChat'),
    ('RR_OFF_VOICE_SLOT', 'VoiceChatBattleParticipantModel', '<SlotDescription>k__BackingField', 'Game.Battle.VoiceChat'),
    ('RR_OFF_VOICE_SPEAKING', 'VoiceChatRoomParticipantModel', '<IsSpeaking>k__BackingField', 'Game.Global.VoiceChat'),
    ('RR_OFF_VOICE_STRING_MAP', 'VoiceChatParticipantsModel', '_participantStringIdToModels', 'Game.Global.VoiceChat'),
    ('RR_OFF_VOICE_USER_ID', 'VoiceChatRoomParticipantModel', '<ProductUserIdString>k__BackingField', 'Game.Global.VoiceChat'),
    ('RR_OFF_WEM_BATTLE_CHARS', 'WorldEntitiesModel', '_battleCharacters', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_CARS', 'WorldEntitiesModel', '_cars', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_CONTAINERS', 'WorldEntitiesModel', '_containers', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_DOORS', 'WorldEntitiesModel', '_doors', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_DROPPED_LOOT', 'WorldEntitiesModel', '_loots', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_HELICOPTERS', 'WorldEntitiesModel', '_helicopters', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_HIDE_OBJECTS', 'WorldEntitiesModel', '_hideObjects', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_ROULETTES', 'WorldEntitiesModel', '_rouletteModels', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_VEHICLES', 'WorldEntitiesModel', '_vehicles', 'Models.Models.WorldEntities'),
    ('RR_OFF_WEM_VEHICLE_LOOT', 'WorldEntitiesModel', '_vehicleLoots', 'Models.Models.WorldEntities'),
    ('RR_OFF_WORLD_ENTITIES', 'WorldModel', '<WorldEntitiesModel>k__BackingField', 'Models.Models.WorldModel'),
    ('RR_RVA_ADDBET', 'RouletteModel', 'AddBet', 'Models.Models.Roulette'),
    ('RR_SF_BET_BLACK', 'RouletteBetDescriptions', 'Black', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_BET_DOZEN_13_24', 'RouletteBetDescriptions', 'Dozen_13_24', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_BET_DOZEN_1_12', 'RouletteBetDescriptions', 'Dozen_1_12', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_BET_DOZEN_25_36', 'RouletteBetDescriptions', 'Dozen_25_36', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_BET_RED', 'RouletteBetDescriptions', 'Red', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_BET_STRAIGHT0', 'RouletteBetDescriptions', 'Straight0', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_CHIP_100K', 'RouletteChipDescriptions', '<Chip100k>k__BackingField', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_CHIP_1K', 'RouletteChipDescriptions', '<Chip1k>k__BackingField', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_CHIP_25K', 'RouletteChipDescriptions', '<Chip25k>k__BackingField', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_CHIP_50K', 'RouletteChipDescriptions', '<Chip50k>k__BackingField', 'Models.ReferencesProject.Descriptions.Roulette'),
    ('RR_SF_CHIP_5K', 'RouletteChipDescriptions', '<Chip5k>k__BackingField', 'Models.ReferencesProject.Descriptions.Roulette'),
]

CLASS_RE = re.compile(r'^\s*(?:\[[^\]]*\]\s*)*(?:public|internal|private|protected)?\s*'
                      r'(?:sealed\s+|abstract\s+|static\s+|partial\s+|readonly\s+|unsafe\s+)*'
                      r'(class|struct|interface|enum)\s+([A-Za-z_][\w`]*)')
FIELD_RE = re.compile(r'^\s*(?:(?:public|private|protected|internal|static|readonly|volatile|const|new|'
                      r'override|virtual|unsafe|extern|fixed|event)\s+)*'
                      r'(?P<type>[^;=(){}]+?)\s+(?P<name>[A-Za-z_<][\w`<>\[\]]*)\s*;\s*'
                      r'//\s*0x(?P<off>[0-9A-Fa-f]+)\s*$')
RVA_RE = re.compile(r'^\s*//\s*RVA:\s*0x([0-9A-Fa-f]+)')
METH_RE = re.compile(r'^\s*(?:(?:public|private|protected|internal|static|virtual|override|sealed|'
                     r'abstract|extern|unsafe|new|async|partial)\s+)*'
                     r'[\w<>\[\],.`? ]+?\s+([A-Za-z_][\w`]*)\s*\(')
DEFINE_RE = re.compile(r'^#define\s+(?P<name>RR_\w+)(?P<pad>\s+)(?P<value>0x[0-9A-Fa-f]+)(?P<suffix>u|ull|ULL|U)?(?P<rest>.*)$')


def strip_code(line):
    """Blank out string/char literals and trailing comments for brace counting."""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c in '"\'':
            quote, i = c, i + 1
            while i < n:
                if line[i] == '\\':
                    i += 2
                    continue
                if line[i] == quote:
                    i += 1
                    break
                i += 1
            out.append('""')
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out)


def parse_dump(path):
    classes, by_simple = {}, collections.defaultdict(list)
    lines = pathlib.Path(path).read_text(encoding='utf-8', errors='ignore').split('\n')
    depth = 0
    ns = ''
    cur = None
    pending_rva = None
    for line in lines:
        s = line.strip()
        if s.startswith('// Namespace:'):
            ns = s.split(':', 1)[1].strip()
            continue
        code = strip_code(line)
        opens, closes = code.count('{'), code.count('}')
        if depth == 0:
            m = CLASS_RE.match(code)
            if m:
                cur = {'ns': ns, 'name': m.group(2), 'fields': {}, 'methods': {}}
                key = (ns, cur['name'])
                if key not in classes:
                    classes[key] = cur
                    by_simple[cur['name']].append(key)
            depth += opens - closes
            continue
        if depth == 1 and cur is not None:
            rm = RVA_RE.match(s)
            if rm:
                pending_rva = int(rm.group(1), 16)
            else:
                fm = FIELD_RE.match(line)
                if fm:
                    cur['fields'].setdefault(fm.group('name'), int(fm.group('off'), 16))
                    pending_rva = None
                elif pending_rva is not None and '(' in code:
                    mm = METH_RE.match(code)
                    if mm:
                        cur['methods'].setdefault(mm.group(1), pending_rva)
                    pending_rva = None
        depth += opens - closes
        if depth <= 0:
            depth = 0
            cur = None
    return classes, by_simple


def variants(field):
    yield field
    if not field.startswith('<'):
        yield '<%s>k__BackingField' % field
    if not field.startswith('_'):
        yield '_' + field[0].lower() + field[1:]
    if field.endswith('_1'):
        yield field[:-2]
    yield field.lstrip('_')


def resolve(classes, by_simple, cls, field, ns):
    hits = []
    for key in by_simple.get(cls, []):
        rec = classes[key]
        for candidate in variants(field):
            if candidate in rec['fields'] or candidate in rec['methods']:
                hits.append((key, rec, candidate))
                break
    if not hits:
        return None
    if len(hits) > 1 and ns:
        for hit in hits:
            if hit[0][0] == ns:
                return hit
    hits.sort(key=lambda h: -len(h[1]['fields']))
    return hits[0]


def read_defines(text):
    out = {}
    for line in text.splitlines():
        m = DEFINE_RE.match(line)
        if m:
            out[m.group('name')] = int(m.group('value'), 16)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dump', type=pathlib.Path, default=DEFAULT_DUMP)
    ap.add_argument('--header-dir', type=pathlib.Path, default=HEADER_DIR)
    ap.add_argument('--check', action='store_true', help='report only; exit 1 on drift')
    args = ap.parse_args()

    if not args.dump.is_file():
        print('ERROR: dump not found: %s' % args.dump, file=sys.stderr)
        return 2
    classes, by_simple = parse_dump(args.dump)
    print('parsed %d classes from %s' % (len(classes), args.dump))

    specs = {row[0]: row[1:] for row in SPECS}
    changed, missing, unknown, same = [], [], [], 0
    texts = {}
    for name in HEADERS:
        path = args.header_dir / name
        if not path.is_file():
            print('ERROR: header not found: %s' % path, file=sys.stderr)
            return 2
        texts[name] = path.read_text(encoding='utf-8', errors='replace')

    for name, text in texts.items():
        lines = text.split('\n')
        for i, line in enumerate(lines):
            m = DEFINE_RE.match(line)
            if not m:
                continue
            macro = m.group('name')
            old = int(m.group('value'), 16)
            if macro not in specs:
                unknown.append(macro)
                continue
            hit = resolve(classes, by_simple, *specs[macro])
            if hit is None:
                missing.append((macro, old, specs[macro]))
                continue
            rec, field = hit[1], hit[2]
            new = rec['methods'][field] if field in rec['methods'] else rec['fields'][field]
            if new == old:
                same += 1
                continue
            changed.append((macro, old, new, name))
            if not args.check:
                lines[i] = '#define %s%s0x%X%s%s' % (macro, m.group('pad'), new,
                                                     m.group('suffix') or '', m.group('rest'))
        if not args.check:
            (args.header_dir / name).write_text('\n'.join(lines), encoding='utf-8')

    for macro, old, new, name in changed:
        print('%-32s 0x%X -> 0x%X  (%s)' % (macro, old, new, name))
    for macro, old, spec in missing:
        print('MISSING %-28s 0x%X  (%s.%s not in dump)' % (macro, old, spec[0], spec[1]))
    if unknown:
        print('no spec for: %s' % ', '.join(sorted(set(unknown))))
    print('%d unchanged, %d updated, %d missing, %d unspecified'
          % (same, len(changed), len(missing), len(set(unknown))))
    if args.check and (changed or missing):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
