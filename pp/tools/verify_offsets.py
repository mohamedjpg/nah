"""Verify every #define in robrun_offsets.h / robrun_sdk_offsets.h against dump.cs.

Reads the headers, extracts each RR_* macro, resolves it through a spec table
built from the dump index, and reports:
  * macros whose value disagrees with the dump        (WRONG)
  * macros the dump cannot resolve                    (UNRESOLVED)
  * RR_* macros referenced in .c but never defined    (MISSING)
  * defines that are never referenced anywhere        (UNUSED)

    python verify_offsets.py                 # report
    python verify_offsets.py --strict        # exit 1 on WRONG/UNRESOLVED/MISSING
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / '2_src_port'
INDEX = HERE.parent / 'offsets' / 'dump_index.json'
HEADERS = ('robrun_offsets.h', 'robrun_sdk_offsets.h')

# macro -> (fully-qualified class, field). Only instance/static *fields*.
SPEC = {
    # generic wrappers - not in the metadata, checked by hand
    'RR_OFF_PRIM_VALUE':  ('Framework.Replication.Data.Primitive.BasePrimitiveData<T>', None),
    'RR_OFF_REF_VALUE':   ('Framework.Replication.Data.Primitive.BasePrimitiveData<T>', None),
    'RR_OFF_PM_DATA':     ('Models.Models.PrimitiveModel.PrimitiveModel<T>', None),
    'RR_OFF_DESC_NAME':   ('Framework.Replication.EnumItem.EnumItem', None),
    'RR_OFF_ENUM_INDEX':  ('Framework.Replication.EnumItem.EnumItem', '<Index>k__BackingField'),

    'RR_OFF_WORLD_ENTITIES':      ('Models.Models.WorldModel.WorldModel', '<WorldEntitiesModel>k__BackingField'),
    'RR_OFF_WEM_BATTLE_CHARS':    ('Models.Models.WorldEntities.WorldEntitiesModel', '_battleCharacters'),
    'RR_OFF_WEM_VEHICLES':        ('Models.Models.WorldEntities.WorldEntitiesModel', '_vehicles'),
    'RR_OFF_WEM_ROULETTES':       ('Models.Models.WorldEntities.WorldEntitiesModel', '_rouletteModels'),
    'RR_OFF_WEM_CONTAINERS':      ('Models.Models.WorldEntities.WorldEntitiesModel', '_containers'),
    'RR_OFF_WEM_DROPPED_LOOT':    ('Models.Models.WorldEntities.WorldEntitiesModel', '_loots'),
    'RR_OFF_WEM_VEHICLE_LOOT':    ('Models.Models.WorldEntities.WorldEntitiesModel', '_vehicleLoots'),
    'RR_OFF_WEM_DOORS':           ('Models.Models.WorldEntities.WorldEntitiesModel', '_doors'),
    'RR_OFF_WEM_CARS':            ('Models.Models.WorldEntities.WorldEntitiesModel', '_cars'),
    'RR_OFF_WEM_HELICOPTERS':     ('Models.Models.WorldEntities.WorldEntitiesModel', '_helicopters'),
    'RR_OFF_WEM_HIDE_OBJECTS':    ('Models.Models.WorldEntities.WorldEntitiesModel', '_hideObjects'),

    'RR_OFF_CHAR_ID':             ('Models.Models.BattleCharacter.BattleCharacterModel', '<Id>k__BackingField'),
    'RR_OFF_CHAR_DATA':           ('Models.Models.BattleCharacter.BattleCharacterModel', '<Data>k__BackingField'),
    'RR_OFF_CHAR_CONFIG':         ('Models.Models.BattleCharacter.BattleCharacterModel', '<Config>k__BackingField'),
    'RR_OFF_CHAR_TRANSFORM':      ('Models.Models.BattleCharacter.BattleCharacterModel', '<Transform>k__BackingField'),
    'RR_OFF_CHAR_REPL_TRANSFORM': ('Models.Models.BattleCharacter.BattleCharacterModel', '<ReplicatedTransform>k__BackingField'),
    'RR_OFF_CHAR_LOOK_DIR':       ('Models.Models.BattleCharacter.BattleCharacterModel', '<LookDirection>k__BackingField'),
    'RR_OFF_LOOK_MODEL':          ('Models.Models.BattleCharacter.BattleCharacterModel', '<LookDirection>k__BackingField'),
    'RR_OFF_CHAR_ISDEAD':         ('Models.Models.BattleCharacter.BattleCharacterModel', '<IsDead>k__BackingField'),
    'RR_OFF_CHAR_PRIVATE':        ('Models.Models.BattleCharacter.BattleCharacterModel', '<PrivateModel>k__BackingField'),
    'RR_OFF_CHAR_SKELETON':       ('Models.Models.BattleCharacter.BattleCharacterModel', '<SkeletonModel>k__BackingField'),
    'RR_OFF_CHAR_WEAPON':         ('Models.Models.BattleCharacter.BattleCharacterModel', '<Weapon>k__BackingField'),
    'RR_OFF_CHAR_CROUCH':         ('Models.Models.BattleCharacter.BattleCharacterModel', '<CrouchModel>k__BackingField'),
    'RR_OFF_CHAR_INVEH':          ('Models.Models.BattleCharacter.BattleCharacterModel', '<InVehicleModel>k__BackingField'),
    'RR_OFF_CHAR_STATE':          ('Models.Models.BattleCharacter.BattleCharacterModel', '<StateModel>k__BackingField'),
    'RR_OFF_CHAR_STANCE':         ('Models.Models.BattleCharacter.BattleCharacterModel', '<BattleStanceModel>k__BackingField'),
    'RR_OFF_CHAR_PBM':            ('Models.Models.BattleCharacter.BattleCharacterModel', '<PlayerBattleModel>k__BackingField'),

    'RR_OFF_DATA_COMMON':         ('Models.Data.BattleCharacterData', '<CommonData>k__BackingField'),
    'RR_OFF_DATA_PRIVATE':        ('Models.Data.BattleCharacterData', '<PrivateData>k__BackingField'),
    'RR_OFF_DATA_PUBLIC':         ('Models.Data.BattleCharacterData', '<PublicData>k__BackingField'),
    'RR_OFF_COMMON_ROLE':         ('Models.Data.BattleCharacterCommonData', '<Role>k__BackingField'),
    'RR_OFF_COMMON_ITEM_IN_HANDS':('Models.Data.BattleCharacterCommonData', '<ItemInHands>k__BackingField'),
    'RR_OFF_PRIVATE_HEALTH':      ('Models.Data.BattleCharacterPrivateData', '<Health>k__BackingField'),
    'RR_OFF_PUBLIC_ARMOR':        ('Models.Data.BattleCharacterPublicData', '<HasArmor>k__BackingField'),
    'RR_OFF_WEAPON_ITEM':         ('Models.Models.WeaponModel.WeaponModel', '_itemInHands'),
    'RR_OFF_CROUCH_BOOL':         ('Models.Models.Crouch.CrouchModel', '_isCrouching'),
    'RR_OFF_STANCE_REF':          ('Models.Models.BattleStance.BattleStanceModel', '_battleStance'),
    'RR_OFF_PBM_DATA':            ('Models.Models.PlayerBattle.PlayerBattleModel', '<Data>k__BackingField'),
    'RR_OFF_INVEH_ID':            ('Models.Models.InVehicle.InVehicleModel', '_entityId'),
    'RR_OFF_INVEH_TYPE':          ('Models.Models.InVehicle.InVehicleModel', '_vehicleType'),
    'RR_OFF_STATE_HIDDEN':        ('Models.Models.BattleCharacterStateModel.BattleCharacterStateModel', '_characterHiddenStateModel'),
    'RR_OFF_HIDDEN_ID_DATA':      ('Models.Models.CharacterHideObjectState.CharacterHideObjectStateModel', '_hideObjectEntityIdData'),
    'RR_OFF_HEALTH_VALUE':        ('Models.Models.Health.HealthModel', '_health'),
    'RR_OFF_HEALTH_DEAD':         ('Models.Models.Health.HealthModel', '_isDead'),
    'RR_OFF_HEALTH_MAX':          ('Models.Models.Health.HealthModel', '_maxAmount'),

    'RR_OFF_CTM_X':               ('Models.Models.TransformModel.CharacterTransformModel', '<X>k__BackingField'),
    'RR_OFF_CTM_Y':               ('Models.Models.TransformModel.CharacterTransformModel', '<Y>k__BackingField'),
    'RR_OFF_CTM_Z':               ('Models.Models.TransformModel.CharacterTransformModel', '<Z>k__BackingField'),
    'RR_OFF_CTM_PITCH':           ('Models.Models.TransformModel.CharacterTransformModel', '<Pitch>k__BackingField'),
    'RR_OFF_CTM_YAW':             ('Models.Models.TransformModel.CharacterTransformModel', '<Yaw>k__BackingField'),
    'RR_OFF_CTM_ROLL':            ('Models.Models.TransformModel.CharacterTransformModel', '<Roll>k__BackingField'),
    'RR_OFF_TRANSFORM_X':         ('Models.Models.TransformModel.TransformModel', '_x'),
    'RR_OFF_TRANSFORM_Y':         ('Models.Models.TransformModel.TransformModel', '_y'),
    'RR_OFF_TRANSFORM_Z':         ('Models.Models.TransformModel.TransformModel', '_z'),
    'RR_OFF_TRANSFORM_RX':        ('Models.Models.TransformModel.TransformModel', '_rx'),
    'RR_OFF_TRANSFORM_RY':        ('Models.Models.TransformModel.TransformModel', '_ry'),
    'RR_OFF_TRANSFORM_RZ':        ('Models.Models.TransformModel.TransformModel', '_rz'),
    'RR_OFF_RTRANSFORM_POS':      ('Models.Models.CharacterReplicatedTransform.CharacterReplicatedTransformModel', '_position'),
    'RR_OFF_RTRANSFORM_RX':       ('Models.Models.CharacterReplicatedTransform.CharacterReplicatedTransformModel', '_rx'),
    'RR_OFF_RTRANSFORM_RY':       ('Models.Models.CharacterReplicatedTransform.CharacterReplicatedTransformModel', '_ry'),
    'RR_OFF_RTRANSFORM_RZ':       ('Models.Models.CharacterReplicatedTransform.CharacterReplicatedTransformModel', '_rz'),
    'RR_OFF_POS_X':               ('Models.Models.PositionModel.PositionModel', '<X>k__BackingField'),
    'RR_OFF_POS_Y':               ('Models.Models.PositionModel.PositionModel', '<Y>k__BackingField'),
    'RR_OFF_POS_Z':               ('Models.Models.PositionModel.PositionModel', '<Z>k__BackingField'),
    'RR_OFF_INTERACT_POS_X':      ('Models.Models.InteractPosition.InteractPositionModel', '<X>k__BackingField'),
    'RR_OFF_INTERACT_POS_Y':      ('Models.Models.InteractPosition.InteractPositionModel', '<Y>k__BackingField'),
    'RR_OFF_INTERACT_POS_Z':      ('Models.Models.InteractPosition.InteractPositionModel', '<Z>k__BackingField'),

    'RR_OFF_CAM_POS':             ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<Position>k__BackingField'),
    'RR_OFF_CAM_ROT':             ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<Orientation>k__BackingField'),
    'RR_OFF_CAM_FWD':             ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<Forward>k__BackingField'),
    'RR_OFF_CAM_RIGHT':           ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<Right>k__BackingField'),
    'RR_OFF_CAM_UP':              ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<Up>k__BackingField'),
    'RR_OFF_CAM_DIST':            ('Game.Battle.Entities.Player.Camera.BattleCameraModel', '<DistanceToFollowTarget>k__BackingField'),

    'RR_OFF_RM_PHASE':            ('Models.Models.Roulette.RouletteModel', '<Phase>k__BackingField'),
    'RR_OFF_RM_PHASE_END':        ('Models.Models.Roulette.RouletteModel', '<PhaseEndTs>k__BackingField'),
    'RR_OFF_RM_WIN_NUMBER':       ('Models.Models.Roulette.RouletteModel', '<WinningNumber>k__BackingField'),
    'RR_OFF_RM_BETS_BY_CHAR':     ('Models.Models.Roulette.RouletteModel', '_betsByCharacter'),

    'RR_OFF_CONTAINER_POS':       ('Models.Models.Container.ContainerModel', '<PositionModel>k__BackingField'),
    'RR_OFF_DOOR_STATE':          ('Models.Models.Door.DoorModel', '<State>k__BackingField'),
    'RR_OFF_DOOR_POS':            ('Models.Models.Door.DoorModel', '<Position>k__BackingField'),
    'RR_OFF_DOOR_STATE_DATA':     ('Models.Models.DoorState.DoorStateModel', '_state'),
    'RR_OFF_DROPPED_LOOT_POS':    ('Models.Models.LootModel.LootModel', '<InteractPositionModel>k__BackingField'),
    'RR_OFF_VEHICLE_LOOT_POS':    ('Models.Models.VehicleLootModel.VehicleLootModel', '<InteractPositionModel>k__BackingField'),
    'RR_OFF_HIDE_DESC':           ('Models.Models.HideObject.HideObjectModel', '<Description>k__BackingField'),
    'RR_OFF_HIDE_OCCUPANT':       ('Models.Models.HideObject.HideObjectModel', '_entityId'),
    'RR_OFF_HIDE_DESC_ID':        ('Models.References.HideObject.LocationHideObjectDescription', '<EntityId>k__BackingField'),
    'RR_OFF_HIDE_DESC_TYPE':      ('Models.References.HideObject.LocationHideObjectDescription', '<HideObjectDescriptionFunc>k__BackingField'),
    'RR_OFF_HIDE_DESC_POS':       ('Models.References.HideObject.LocationHideObjectDescription', '<Position>k__BackingField'),
    'RR_OFF_HIDE_DESC_ROT':       ('Models.References.HideObject.LocationHideObjectDescription', '<Orientation>k__BackingField'),
    'RR_OFF_HIDE_DESC_INTERACT':  ('Models.References.HideObject.LocationHideObjectDescription', '<InteractPoint>k__BackingField'),

    'RR_OFF_BATTLE_ENTITIES':     ('Game.Battle.BattleModel', '<BattleEntitiesModel>k__BackingField'),
    'RR_OFF_BATTLE_CAMERA':       ('Game.Battle.BattleModel', '<BattleCameraModel>k__BackingField'),
    'RR_OFF_BATTLE_AIM':          ('Game.Battle.BattleModel', '<AimTargetModel>k__BackingField'),
    'RR_OFF_BATTLE_VOICE_ROOM':   ('Game.Battle.BattleModel', '<VoiceChatBattleRoomModel>k__BackingField'),
    'RR_OFF_BATTLE_PLAYER_SLOTS': ('Game.Battle.BattleModel', '<BattleCharacterSlotsModel>k__BackingField'),
    'RR_OFF_BATTLE_WORLD_B':      ('Game.Battle.BattleModel', '<WorldEntitiesModel>k__BackingField'),
    'RR_OFF_BATTLE_WORLD':        ('Game.Battle.BattleEntitiesModel', '_worldEntitiesModel'),
    'RR_OFF_BATTLE_MODELS':       ('Game.Battle.BattleEntitiesModel', '_models'),
    'RR_OFF_BATTLE_SLOTS':        ('Game.Battle.BattleEntitiesModel', '_characterSlotModel'),
    'RR_OFF_VIEWS_BATTLE':        ('Game.Battle.BattleEntitiesUpdater', '_battleEntitiesModel'),
    'RR_OFF_VIEWS_MODEL':         ('Game.Battle.BattleEntitiesUpdater', '_battleModel'),
    'RR_OFF_VIEWS_CHARACTERS':    ('Game.Battle.BattleEntitiesUpdater', '_characterEntityViews'),
    'RR_OFF_VIEWS_CARS':          ('Game.Battle.BattleEntitiesUpdater', '_carEntityViews'),
    'RR_OFF_VIEWS_HELICOPTERS':   ('Game.Battle.BattleEntitiesUpdater', '_helicopterEntityViews'),
    'RR_OFF_AIM_BATTLE':          ('Game.Battle.Entities.Player.Updaters.BattleAimTargetUpdater', '_battleEntitiesModel'),
    'RR_OFF_AIM_BRAIN':           ('Game.Battle.Entities.Player.Updaters.BattleAimTargetUpdater', '_cinemachineBrain'),

    'RR_OFF_SLOTS_DICTIONARY':    ('Models.Models.BattleCharacterSlots.BattleCharacterSlotsModel', '_slots'),
    'RR_OFF_SLOT_DATA':           ('Models.Models.BattleCharacterSlots.BattleCharacterSlotModel', '_data'),
    'RR_OFF_SLOT_DESC':           ('Models.Models.BattleCharacterSlots.BattleCharacterSlotModel', '<Description>k__BackingField'),
    'RR_OFF_SLOT_ENTITY_ID':      ('Models.Data.BattleCharacterSlotData', '<EntityId>k__BackingField'),
    'RR_OFF_SLOT_NICKNAME':       ('Models.Data.BattleCharacterSlotData', '<Nickname>k__BackingField'),
    'RR_OFF_SLOT_USER_ID':        ('Models.Data.BattleCharacterSlotData', '<EOSProductUserId>k__BackingField'),

    'RR_OFF_SEATS_DATA':          ('Models.Models.VehicleSeats.VehicleSeatsModel', '_data'),
    'RR_OFF_SEAT_OCCUPIED':       ('Models.Data.Vehicle.VehicleSeatData', '<Occupied>k__BackingField'),
    'RR_OFF_SEAT_ENTITY_ID':      ('Models.Data.Vehicle.VehicleSeatData', '<EntityId>k__BackingField'),
    'RR_OFF_CAR_ID':              ('Models.Models.Car.CarModel', '<Id>k__BackingField'),
    'RR_OFF_CAR_OWNER_ROLE':      ('Models.Models.Car.CarModel', '<OwnerRole>k__BackingField'),
    'RR_OFF_CAR_DESC':            ('Models.Models.Car.CarModel', '<Description>k__BackingField'),
    'RR_OFF_CAR_TRANSFORM':       ('Models.Models.Car.CarModel', '<Transform>k__BackingField'),
    'RR_OFF_CAR_SEATS':           ('Models.Models.Car.CarModel', '<Seats>k__BackingField'),
    'RR_OFF_HELI_ID':             ('Models.Models.Helicopter.HelicopterModel', '<Id>k__BackingField'),
    'RR_OFF_HELI_OWNER_ROLE':     ('Models.Models.Helicopter.HelicopterModel', '<OwnerRole>k__BackingField'),
    'RR_OFF_HELI_DESC':           ('Models.Models.Helicopter.HelicopterModel', '<Description>k__BackingField'),
    'RR_OFF_HELI_TRANSFORM':      ('Models.Models.Helicopter.HelicopterModel', '<Transform>k__BackingField'),
    'RR_OFF_HELI_SEATS':          ('Models.Models.Helicopter.HelicopterModel', '<Seats>k__BackingField'),

    'RR_OFF_ENTRY_GAME':          ('Start.UnityEntry', '_game'),
    'RR_OFF_GAME_MODEL':          ('Game.Game', '<GameModel>k__BackingField'),
    'RR_OFF_GAME_BATTLE':         ('Game.GameModel', '_battleModel'),

    'RR_OFF_VOICE_ROOM_PARTICIPANTS': ('Game.Global.VoiceChat.VoiceChatRoomModel', 'ParticipantsModel'),
    'RR_OFF_VOICE_STRING_MAP':    ('Game.Global.VoiceChat.VoiceChatParticipantsModel', '_participantStringIdToModels'),
    'RR_OFF_VOICE_SLOT':          ('Game.Battle.VoiceChat.VoiceChatBattleParticipantModel', '<SlotDescription>k__BackingField'),
    'RR_OFF_VOICE_HIDE_ID':       ('Game.Battle.VoiceChat.VoiceChatBattleParticipantModel', '<HideObjectEntityId>k__BackingField'),
    'RR_OFF_VOICE_USER_ID':       ('Game.Global.VoiceChat.VoiceChatRoomParticipantModel', '<ProductUserIdString>k__BackingField'),
    'RR_OFF_VOICE_SPEAKING':      ('Game.Global.VoiceChat.VoiceChatRoomParticipantModel', '<IsSpeaking>k__BackingField'),

    'RR_SF_BET_STRAIGHT0':        ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Straight0'),
    'RR_SF_BET_DOZEN_1_12':       ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Dozen_1_12'),
    'RR_SF_BET_DOZEN_13_24':      ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Dozen_13_24'),
    'RR_SF_BET_DOZEN_25_36':      ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Dozen_25_36'),
    'RR_SF_BET_RED':              ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Red'),
    'RR_SF_BET_BLACK':            ('Models.ReferencesProject.Descriptions.Roulette.RouletteBetDescriptions', 'Black'),
    'RR_SF_CHIP_1K':              ('Models.ReferencesProject.Descriptions.Roulette.RouletteChipDescriptions', '<Chip1k>k__BackingField'),
    'RR_SF_CHIP_5K':              ('Models.ReferencesProject.Descriptions.Roulette.RouletteChipDescriptions', '<Chip5k>k__BackingField'),
    'RR_SF_CHIP_25K':             ('Models.ReferencesProject.Descriptions.Roulette.RouletteChipDescriptions', '<Chip25k>k__BackingField'),
    'RR_SF_CHIP_50K':             ('Models.ReferencesProject.Descriptions.Roulette.RouletteChipDescriptions', '<Chip50k>k__BackingField'),
    'RR_SF_CHIP_100K':            ('Models.ReferencesProject.Descriptions.Roulette.RouletteChipDescriptions', '<Chip100k>k__BackingField'),
}

# Method RVAs, verified against script.json ScriptMethod[].Address.
RVA_SPEC = {
    'RR_RVA_ADDBET':       0x48E4BB0,
    'RR_RVA_RM_WIN_NUMBER': 0x7BB030,
    'RR_RVA_RM_PHASE':      0x7AB150,
    'RR_RVA_RM_PHASE_END':  0x7AA000,
    'RR_RVA_WEM_ROULETTES': 0x4636E50,
}

# Static-storage globals: heuristic, only consumed by --probe. Never verified
# against dump.cs because the value is not in the metadata.
SF_GLOBAL = {'RR_SF_WORLDMODEL', 'RR_SF_WORLDENTITIESMODEL',
             'RR_SF_BATTLECHARACTERMODEL', 'RR_SF_BATTLECAMERAMODEL'}

DEFINE = re.compile(r'^\s*#\s*define\s+(RR_(?:OFF|RVA|SF)_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+)')
TOKEN = re.compile(r'\bRR_(?:OFF|RVA|SF)_[A-Z0-9_]+\b')
COMMENT = re.compile(r'/\*.*?\*/|//[^\n]*', re.S)


def strip_comments(text):
    """Blank out comments so a macro named only in prose is not a reference."""
    return COMMENT.sub(lambda m: '\n' * m.group(0).count('\n'), text)


def source_files():
    return (sorted(SRC.glob('*.[ch]')) + sorted(SRC.glob('*.cpp')))


def read_headers():
    values, where = {}, {}
    for name in HEADERS:
        path = SRC / name
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            m = DEFINE.match(line)
            if m:
                macro, val = m.group(1), int(m.group(2), 16)
                if macro in values and values[macro] != val:
                    print('CONFLICT %s: 0x%X in %s vs 0x%X in %s'
                          % (macro, values[macro], where[macro], val, name))
                values[macro] = val
                where[macro] = name
    return values, where


def read_all_defines():
    """Headers plus .c-local defines, so a macro defined next to its reader counts."""
    values = {}
    for path in source_files():
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            m = DEFINE.match(line)
            if m:
                values.setdefault(m.group(1), int(m.group(2), 16))
    return values


def read_references():
    refs = set()
    for path in source_files():
        text = strip_comments(path.read_text(encoding='utf-8', errors='replace'))
        for line in text.splitlines():
            if DEFINE.match(line):
                continue
            refs.update(TOKEN.findall(line))
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=Path, default=INDEX)
    ap.add_argument('--strict', action='store_true')
    args = ap.parse_args()

    index = json.loads(args.index.read_text(encoding='utf-8'))
    values, where = read_headers()
    all_defs = read_all_defines()
    refs = read_references()

    wrong, unresolved, unverified = [], [], []
    for macro, val in sorted(values.items()):
        if macro in RVA_SPEC:
            if val != RVA_SPEC[macro]:
                wrong.append((macro, val, RVA_SPEC[macro], 'script.json RVA'))
            continue
        if macro in SF_GLOBAL:
            unverified.append((macro, val, 'static-storage global (not in metadata)'))
            continue
        spec = SPEC.get(macro)
        if spec is None:
            unresolved.append((macro, val, 'no spec row'))
            continue
        klass, field = spec
        if field is None:
            unverified.append((macro, val, 'generic wrapper, hand-checked'))
            continue
        rec = index.get(klass)
        if rec is None:
            unresolved.append((macro, val, 'class %s not in dump' % klass))
            continue
        fld = rec['fields'].get(field)
        if fld is None:
            unresolved.append((macro, val, '%s.%s not in dump' % (klass, field)))
            continue
        if fld['offset'] != val:
            wrong.append((macro, val, fld['offset'], '%s.%s' % (klass, field)))

    missing = sorted(r for r in refs if r not in all_defs)
    unused = sorted(m for m in values if m not in refs and m not in SF_GLOBAL)

    print('macros defined : %d' % len(values))
    print('macros used    : %d' % len(refs))
    print()
    if wrong:
        print('=== WRONG VALUE (%d) ===' % len(wrong))
        for macro, have, want, src in wrong:
            print('  %-32s header 0x%-6X dump 0x%-6X  %s' % (macro, have, want, src))
    if unresolved:
        print('=== UNRESOLVED (%d) ===' % len(unresolved))
        for macro, val, why in unresolved:
            print('  %-32s 0x%-6X  %s' % (macro, val, why))
    if missing:
        print('=== REFERENCED BUT NOT DEFINED (%d) ===' % len(missing))
        for macro in missing:
            print('  ' + macro)
    if unverified:
        print('=== NOT DERIVABLE FROM dump.cs (%d) ===' % len(unverified))
        for macro, val, why in unverified:
            print('  %-32s 0x%-6X  %s' % (macro, val, why))
    if unused:
        print('=== DEFINED BUT UNREFERENCED (%d) ===' % len(unused))
        for macro in unused:
            print('  ' + macro)
    if not (wrong or unresolved or missing):
        print('OK - every derivable macro matches the dump, nothing referenced is missing.')

    if args.strict and (wrong or unresolved or missing):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
