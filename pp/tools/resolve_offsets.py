"""Resolve a macro spec against the dump.cs index and emit both headers.

Usage:
  python resolve_offsets.py --index src/pp/offsets/dump_index.json --write
  python resolve_offsets.py --index ... --check   # report only
"""

import argparse
import json
import sys
from pathlib import Path

# (macro, class, field)  -- class is the short name; resolved by suffix match.
FIELD_SPEC = [
    # --- world graph -------------------------------------------------------
    ('RR_OFF_WORLD_ENTITIES',      'WorldModel', '<WorldEntitiesModel>k__BackingField'),
    ('RR_OFF_WEM_BATTLE_CHARS',    'WorldEntitiesModel', '_battleCharacters'),
    ('RR_OFF_WEM_VEHICLES',        'WorldEntitiesModel', '_vehicles'),
    ('RR_OFF_WEM_ROULETTES',       'WorldEntitiesModel', '_rouletteModels'),
    ('RR_OFF_WEM_CONTAINERS',      'WorldEntitiesModel', '_containers'),
    ('RR_OFF_WEM_DROPPED_LOOT',    'WorldEntitiesModel', '_loots'),
    ('RR_OFF_WEM_VEHICLE_LOOT',    'WorldEntitiesModel', '_vehicleLoots'),
    ('RR_OFF_WEM_DOORS',           'WorldEntitiesModel', '_doors'),
    ('RR_OFF_WEM_CARS',            'WorldEntitiesModel', '_cars'),
    ('RR_OFF_WEM_HELICOPTERS',     'WorldEntitiesModel', '_helicopters'),
    ('RR_OFF_WEM_HIDE_OBJECTS',    'WorldEntitiesModel', '_hideObjects'),

    # --- BattleCharacterModel ---------------------------------------------
    ('RR_OFF_CHAR_ID',             'BattleCharacterModel', '<Id>k__BackingField'),
    ('RR_OFF_CHAR_DATA',           'BattleCharacterModel', '<Data>k__BackingField'),
    ('RR_OFF_CHAR_CONFIG',         'BattleCharacterModel', '<Config>k__BackingField'),
    ('RR_OFF_CHAR_TRANSFORM',      'BattleCharacterModel', '<Transform>k__BackingField'),
    ('RR_OFF_CHAR_REPL_TRANSFORM', 'BattleCharacterModel', '<ReplicatedTransform>k__BackingField'),
    ('RR_OFF_CHAR_ISDEAD',         'BattleCharacterModel', '<IsDead>k__BackingField'),
    ('RR_OFF_CHAR_PRIVATE',        'BattleCharacterModel', '<PrivateModel>k__BackingField'),
    ('RR_OFF_CHAR_WEAPON',         'BattleCharacterModel', '<Weapon>k__BackingField'),
    ('RR_OFF_CHAR_CROUCH',         'BattleCharacterModel', '<CrouchModel>k__BackingField'),
    ('RR_OFF_CHAR_STANCE',         'BattleCharacterModel', '<BattleStanceModel>k__BackingField'),
    ('RR_OFF_CHAR_PBM',            'BattleCharacterModel', '<PlayerBattleModel>k__BackingField'),
    ('RR_OFF_CHAR_SKELETON',       'BattleCharacterModel', '<SkeletonModel>k__BackingField'),
    ('RR_OFF_CHAR_INVEH',          'BattleCharacterModel', '<InVehicleModel>k__BackingField'),
    ('RR_OFF_CHAR_STATE',          'BattleCharacterModel', '<StateModel>k__BackingField'),
    ('RR_OFF_CHAR_LOOK_DIR',       'BattleCharacterModel', '<LookDirection>k__BackingField'),

    # --- character data ----------------------------------------------------
    ('RR_OFF_DATA_COMMON',         'BattleCharacterData', '<CommonData>k__BackingField'),
    ('RR_OFF_DATA_PRIVATE',        'BattleCharacterData', '<PrivateData>k__BackingField'),
    ('RR_OFF_DATA_PUBLIC',         'BattleCharacterData', '<PublicData>k__BackingField'),
    ('RR_OFF_COMMON_ROLE',         'BattleCharacterCommonData', '<Role>k__BackingField'),
    ('RR_OFF_COMMON_ITEM_IN_HANDS','BattleCharacterCommonData', '<ItemInHands>k__BackingField'),
    ('RR_OFF_PRIVATE_HEALTH',      'BattleCharacterPrivateData', '<Health>k__BackingField'),
    ('RR_OFF_PUBLIC_ARMOR',        'BattleCharacterPublicData', '<HasArmor>k__BackingField'),

    # --- sub models --------------------------------------------------------
    ('RR_OFF_WEAPON_ITEM',         'WeaponModel', '<ItemInHands>k__BackingField'),
    ('RR_OFF_CROUCH_BOOL',         'CrouchModel', '<IsCrouching>k__BackingField'),
    ('RR_OFF_STANCE_REF',          'BattleStanceModel', '<BattleStance>k__BackingField'),
    ('RR_OFF_PBM_DATA',            'PlayerBattleModel', '<Data>k__BackingField'),
    ('RR_OFF_INVEH_ID',            'InVehicleModel', '<EntityId>k__BackingField'),
    ('RR_OFF_INVEH_TYPE',          'InVehicleModel', '<VehicleType>k__BackingField'),
    ('RR_OFF_STATE_HIDDEN',        'BattleCharacterStateModel', '<CharacterHiddenStateModel>k__BackingField'),
    ('RR_OFF_HIDDEN_ID_DATA',      'CharacterHideObjectStateModel', '<HideObjectEntityIdData>k__BackingField'),

    # --- camera ------------------------------------------------------------
    ('RR_OFF_CAM_POS',             'BattleCameraModel', '<Position>k__BackingField'),
    ('RR_OFF_CAM_ROT',             'BattleCameraModel', '<Orientation>k__BackingField'),
    ('RR_OFF_CAM_FWD',             'BattleCameraModel', '<Forward>k__BackingField'),
    ('RR_OFF_CAM_RIGHT',           'BattleCameraModel', '<Right>k__BackingField'),
    ('RR_OFF_CAM_UP',              'BattleCameraModel', '<Up>k__BackingField'),
    ('RR_OFF_CAM_DIST',            'BattleCameraModel', '<DistanceToFollowTarget>k__BackingField'),

    # --- transforms --------------------------------------------------------
    ('RR_OFF_CTM_X',               'CharacterTransformModel', '<X>k__BackingField'),
    ('RR_OFF_CTM_Y',               'CharacterTransformModel', '<Y>k__BackingField'),
    ('RR_OFF_CTM_Z',               'CharacterTransformModel', '<Z>k__BackingField'),
    ('RR_OFF_CTM_PITCH',           'CharacterTransformModel', '<Pitch>k__BackingField'),
    ('RR_OFF_CTM_YAW',             'CharacterTransformModel', '<Yaw>k__BackingField'),
    ('RR_OFF_CTM_ROLL',            'CharacterTransformModel', '<Roll>k__BackingField'),
    ('RR_OFF_TRANSFORM_X',         'TransformModel', '_x'),
    ('RR_OFF_TRANSFORM_Y',         'TransformModel', '_y'),
    ('RR_OFF_TRANSFORM_Z',         'TransformModel', '_z'),
    ('RR_OFF_TRANSFORM_RX',        'TransformModel', '_rx'),
    ('RR_OFF_TRANSFORM_RY',        'TransformModel', '_ry'),
    ('RR_OFF_TRANSFORM_RZ',        'TransformModel', '_rz'),
    ('RR_OFF_RTRANSFORM_POS',      'CharacterReplicatedTransformModel', '_position'),
    ('RR_OFF_RTRANSFORM_RX',       'CharacterReplicatedTransformModel', '_rx'),
    ('RR_OFF_RTRANSFORM_RY',       'CharacterReplicatedTransformModel', '_ry'),
    ('RR_OFF_RTRANSFORM_RZ',       'CharacterReplicatedTransformModel', '_rz'),

    # --- positions ---------------------------------------------------------
    ('RR_OFF_POS_X',               'PositionModel', '<X>k__BackingField'),
    ('RR_OFF_POS_Y',               'PositionModel', '<Y>k__BackingField'),
    ('RR_OFF_POS_Z',               'PositionModel', '<Z>k__BackingField'),
    ('RR_OFF_INTERACT_POS_X',      'InteractPositionModel', '<X>k__BackingField'),
    ('RR_OFF_INTERACT_POS_Y',      'InteractPositionModel', '<Y>k__BackingField'),
    ('RR_OFF_INTERACT_POS_Z',      'InteractPositionModel', '<Z>k__BackingField'),

    # --- health ------------------------------------------------------------
    ('RR_OFF_HEALTH_VALUE',        'HealthModel', '<Health>k__BackingField'),
    ('RR_OFF_HEALTH_DEAD',         'HealthModel', '<IsDead>k__BackingField'),
    ('RR_OFF_HEALTH_MAX',          'HealthModel', '<MaxAmount>k__BackingField'),

    # --- world objects -----------------------------------------------------
    ('RR_OFF_CONTAINER_POS',       'ContainerModel', '<PositionModel>k__BackingField'),
    ('RR_OFF_DOOR_STATE',          'DoorModel', '<State>k__BackingField'),
    ('RR_OFF_DOOR_POS',            'DoorModel', '<Position>k__BackingField'),
    ('RR_OFF_DOOR_STATE_DATA',     'DoorStateModel', '_state'),
    ('RR_OFF_DROPPED_LOOT_POS',    'LootModel', '<InteractPositionModel>k__BackingField'),
    ('RR_OFF_VEHICLE_LOOT_POS',    'VehicleLootModel', '<InteractPositionModel>k__BackingField'),
    ('RR_OFF_HIDE_DESC',           'HideObjectModel', '<Description>k__BackingField'),
    ('RR_OFF_HIDE_OCCUPANT',       'HideObjectModel', '<EntityId>k__BackingField'),
    ('RR_OFF_HIDE_DESC_ID',        'LocationHideObjectDescription', '<EntityId>k__BackingField'),
    ('RR_OFF_HIDE_DESC_POS',       'LocationHideObjectDescription', '<Position>k__BackingField'),
    ('RR_OFF_HIDE_DESC_TYPE',      'LocationHideObjectDescription', '<HideObjectDescriptionFunc>k__BackingField'),
    ('RR_OFF_HIDE_DESC_ROT',       'LocationHideObjectDescription', '<Orientation>k__BackingField'),
    ('RR_OFF_HIDE_DESC_INTERACT',  'LocationHideObjectDescription', '<InteractPoint>k__BackingField'),

    # --- battle / game -----------------------------------------------------
    ('RR_OFF_ENTRY_GAME',          'UnityEntry', '_game'),
    ('RR_OFF_GAME_MODEL',          'Game', '<GameModel>k__BackingField'),
    ('RR_OFF_GAME_BATTLE',         'GameModel', '_battleModel'),
    ('RR_OFF_BATTLE_ENTITIES',     'BattleModel', '<BattleEntitiesModel>k__BackingField'),
    ('RR_OFF_BATTLE_CAMERA',       'BattleModel', '<BattleCameraModel>k__BackingField'),
    ('RR_OFF_BATTLE_AIM',          'BattleModel', '<AimTargetModel>k__BackingField'),
    ('RR_OFF_BATTLE_VOICE_ROOM',   'BattleModel', '<VoiceChatBattleRoomModel>k__BackingField'),
    ('RR_OFF_BATTLE_PLAYER_SLOTS', 'BattleModel', '<BattleCharacterSlotsModel>k__BackingField'),
    ('RR_OFF_BATTLE_WORLD',        'BattleEntitiesModel', '_worldEntitiesModel'),
    ('RR_OFF_BATTLE_MODELS',       'BattleEntitiesModel', '_models'),
    ('RR_OFF_BATTLE_SLOTS',        'BattleEntitiesModel', '_characterSlotModel'),
    ('RR_OFF_VIEWS_BATTLE',        'BattleEntitiesUpdater', '_battleEntitiesModel'),
    ('RR_OFF_VIEWS_MODEL',         'BattleEntitiesUpdater', '_battleModel'),
    ('RR_OFF_VIEWS_CHARACTERS',    'BattleEntitiesUpdater', '_characterEntityViews'),
    ('RR_OFF_VIEWS_CARS',          'BattleEntitiesUpdater', '_carEntityViews'),
    ('RR_OFF_VIEWS_HELICOPTERS',   'BattleEntitiesUpdater', '_helicopterEntityViews'),
    ('RR_OFF_AIM_BATTLE',          'BattleAimTargetUpdater', '_battleEntitiesModel'),
    ('RR_OFF_AIM_BRAIN',           'BattleAimTargetUpdater', '_cinemachineBrain'),

    # --- slots -------------------------------------------------------------
    ('RR_OFF_SLOTS_DICTIONARY',    'BattleCharacterSlotsModel', '_slots'),
    ('RR_OFF_SLOT_DATA',           'BattleCharacterSlotModel', '_data'),
    ('RR_OFF_SLOT_DESC',           'BattleCharacterSlotModel', '<Description>k__BackingField'),
    ('RR_OFF_SLOT_ENTITY_ID',      'BattleCharacterSlotData', '<EntityId>k__BackingField'),
    ('RR_OFF_SLOT_NICKNAME',       'BattleCharacterSlotData', '<Nickname>k__BackingField'),
    ('RR_OFF_SLOT_USER_ID',        'BattleCharacterSlotData', '<EOSProductUserId>k__BackingField'),

    # --- vehicles ----------------------------------------------------------
    ('RR_OFF_SEATS_DATA',          'VehicleSeatsModel', '_data'),
    ('RR_OFF_SEAT_OCCUPIED',       'VehicleSeatData', '<Occupied>k__BackingField'),
    ('RR_OFF_SEAT_ENTITY_ID',      'VehicleSeatData', '<EntityId>k__BackingField'),
    ('RR_OFF_CAR_ID',              'CarModel', '<Id>k__BackingField'),
    ('RR_OFF_CAR_OWNER_ROLE',      'CarModel', '<OwnerRole>k__BackingField'),
    ('RR_OFF_CAR_DESC',            'CarModel', '<Description>k__BackingField'),
    ('RR_OFF_CAR_TRANSFORM',       'CarModel', '<Transform>k__BackingField'),
    ('RR_OFF_CAR_SEATS',           'CarModel', '<Seats>k__BackingField'),
    ('RR_OFF_HELI_ID',             'HelicopterModel', '<Id>k__BackingField'),
    ('RR_OFF_HELI_OWNER_ROLE',     'HelicopterModel', '<OwnerRole>k__BackingField'),
    ('RR_OFF_HELI_DESC',           'HelicopterModel', '<Description>k__BackingField'),
    ('RR_OFF_HELI_TRANSFORM',      'HelicopterModel', '<Transform>k__BackingField'),
    ('RR_OFF_HELI_SEATS',          'HelicopterModel', '<Seats>k__BackingField'),

    # --- voice -------------------------------------------------------------
    ('RR_OFF_VOICE_ROOM_PARTICIPANTS', 'VoiceChatRoomModel', '<ParticipantsModel>k__BackingField'),
    ('RR_OFF_VOICE_STRING_MAP',    'VoiceChatParticipantsModel', '_participantStringIdToModels'),
    ('RR_OFF_VOICE_SLOT',          'VoiceChatBattleParticipantModel', '<SlotDescription>k__BackingField'),
    ('RR_OFF_VOICE_HIDE_ID',       'VoiceChatBattleParticipantModel', '<HideObjectEntityId>k__BackingField'),
    ('RR_OFF_VOICE_USER_ID',       'VoiceChatRoomParticipantModel', '<ProductUserIdString>k__BackingField'),
    ('RR_OFF_VOICE_SPEAKING',      'VoiceChatRoomParticipantModel', '<IsSpeaking>k__BackingField'),

    # --- roulette ----------------------------------------------------------
    ('RR_OFF_RM_PHASE',            'RouletteModel', '<Phase>k__BackingField'),
    ('RR_OFF_RM_PHASE_END',        'RouletteModel', '<PhaseEndTs>k__BackingField'),
    ('RR_OFF_RM_WIN_NUMBER',       'RouletteModel', '<WinningNumber>k__BackingField'),
    ('RR_OFF_RM_BETS_BY_CHAR',     'RouletteModel', '_betsByCharacter'),
]

STATIC_SPEC = [
    ('RR_SF_BET_STRAIGHT0',   'RouletteBetDescriptions', 'Straight0'),
    ('RR_SF_BET_DOZEN_1_12',  'RouletteBetDescriptions', 'Dozen_1_12'),
    ('RR_SF_BET_DOZEN_13_24', 'RouletteBetDescriptions', 'Dozen_13_24'),
    ('RR_SF_BET_DOZEN_25_36', 'RouletteBetDescriptions', 'Dozen_25_36'),
    ('RR_SF_BET_RED',         'RouletteBetDescriptions', 'Red'),
    ('RR_SF_BET_BLACK',       'RouletteBetDescriptions', 'Black'),
    ('RR_SF_CHIP_1K',         'RouletteChipDescriptions', '<Chip1k>k__BackingField'),
    ('RR_SF_CHIP_5K',         'RouletteChipDescriptions', '<Chip5k>k__BackingField'),
    ('RR_SF_CHIP_25K',        'RouletteChipDescriptions', '<Chip25k>k__BackingField'),
    ('RR_SF_CHIP_50K',        'RouletteChipDescriptions', '<Chip50k>k__BackingField'),
    ('RR_SF_CHIP_100K',       'RouletteChipDescriptions', '<Chip100k>k__BackingField'),
]

# Static-field holders: macro -> (class, field). Offsets are into the class's
# static storage blob, which Il2CppDumper prints as `// 0xNN` on the field.
STATIC_CLASS_SPEC = [
    ('RR_SF_WORLDMODEL',        'WorldModel'),
    ('RR_SF_WORLDENTITIESMODEL', 'WorldEntitiesModel'),
    ('RR_SF_BATTLECHARACTERMODEL', 'BattleCharacterModel'),
    ('RR_SF_BATTLECAMERAMODEL', 'BattleCameraModel'),
]


def load(index_path):
    return json.loads(Path(index_path).read_text(encoding='utf-8'))


def find_class(index, short):
    hits = [k for k in index if k == short or k.endswith('.' + short)]
    return hits


def resolve(index, macro, klass, field, errors):
    hits = find_class(index, klass)
    if len(hits) != 1:
        errors.append(f'{macro}: class {klass!r} matched {hits or "nothing"}')
        return None
    cls = index[hits[0]]
    f = cls['fields'].get(field)
    if f is None:
        near = [n for n in cls['fields'] if n.lower().lstrip('<').startswith(field.lower().lstrip('<')[:6])]
        errors.append(f'{macro}: {hits[0]}.{field} missing (near: {near})')
        return None
    return f['offset'], hits[0], f['decl']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', default='src/pp/offsets/dump_index.json')
    ap.add_argument('--header', default='src/pp/2_src_port/robrun_offsets.h')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--all', action='store_true', help='dump every field of the spec classes')
    a = ap.parse_args()

    index = load(a.index)
    errors = []
    rows = []
    for macro, klass, field in FIELD_SPEC:
        r = resolve(index, macro, klass, field, errors)
        if r:
            rows.append((macro, r[0], r[1], field))
    for macro, klass, field in STATIC_SPEC:
        r = resolve(index, macro, klass, field, errors)
        if r:
            rows.append((macro, r[0], r[1], field))

    for macro, off, full, field in rows:
        print(f'0x{off:<6X} {macro:32s} {full}.{field}')
    print()
    if errors:
        print(f'=== {len(errors)} ERRORS ===')
        for e in errors:
            print(' ', e)
    else:
        print(f'OK: {len(rows)} macros resolved, 0 errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
