/* GENERATED from dump.cs (newasmbly). Do not edit.
 * Supplemental managed instance fields resolved from the Il2CppDumper dump.
 * Synced 2026-11-21 against newasmbly/dump.cs (GameAssembly.dll e4b191f5...).
 */
#ifndef ROBRUN_SDK_OFFSETS_H
#define ROBRUN_SDK_OFFSETS_H

// WorldEntitiesModel
#define RR_OFF_WEM_CONTAINERS            0x20u
#define RR_OFF_WEM_DROPPED_LOOT          0x38u
#define RR_OFF_WEM_VEHICLE_LOOT          0x40u
#define RR_OFF_WEM_DOORS                 0x48u
#define RR_OFF_WEM_CARS                  0x60u
#define RR_OFF_WEM_HELICOPTERS           0x68u
#define RR_OFF_WEM_HIDE_OBJECTS          0x1B0u
#define RR_OFF_WEM_ROULETTES             0x478u

// Container
#define RR_OFF_CONTAINER_POS             0x28u
// STALE: ContainerModel has no inventory field in the 2026-11-21 dump.
// Unused in src; do not trust until re-derived from the current build.
#define RR_OFF_CONTAINER_INV             0x30u

// Door
#define RR_OFF_DOOR_STATE                0x30u
#define RR_OFF_DOOR_POS                  0x38u
#define RR_OFF_DOOR_STATE_DATA           0x10u

// Dropped loot / Vehicle loot
#define RR_OFF_DROPPED_LOOT_POS          0x28u
#define RR_OFF_VEHICLE_LOOT_POS          0x28u

// Position
#define RR_OFF_POS_X                     0x10u
#define RR_OFF_POS_Y                     0x14u
#define RR_OFF_POS_Z                     0x18u

// BattleCharacterModel - new dump offsets
#define RR_OFF_CHAR_SKELETON             0x138u
#define RR_OFF_CHAR_INVEH                0x1C8u
#define RR_OFF_CHAR_STATE                0x1E0u
#define RR_OFF_CHAR_LOOK_DIR             0x70u

// Common data
#define RR_OFF_COMMON_ITEM_IN_HANDS      0xB8u

// InVehicle
#define RR_OFF_INVEH_ID                  0x10u
#define RR_OFF_INVEH_TYPE                0x20u
// STALE: InVehicleModel only has _entityId/_seatSlot/_vehicleType in the
// 2026-11-21 dump. Unused in src; do not trust until re-derived.
#define RR_OFF_INVEH_VEHICLE             0x30u

// State
#define RR_OFF_STATE_HIDDEN              0x20u

// HideObject
#define RR_OFF_HIDDEN_ID_DATA            0x10u
#define RR_OFF_HIDE_DESC                 0x18u
#define RR_OFF_HIDE_DESC_ID              0x20u
#define RR_OFF_HIDE_DESC_POS             0x30u
#define RR_OFF_HIDE_DESC_TYPE            0x28u
#define RR_OFF_HIDE_DESC_ROT             0x3Cu
#define RR_OFF_HIDE_DESC_INTERACT        0x4Cu
#define RR_OFF_HIDE_OCCUPANT             0x10u

// Battle
#define RR_OFF_BATTLE_VOICE_ROOM         0x630u
#define RR_OFF_BATTLE_PLAYER_SLOTS       0x4D0u
#define RR_OFF_BATTLE_ENTITIES           0x90u
#define RR_OFF_BATTLE_CAMERA             0x358u
#define RR_OFF_BATTLE_AIM                0x198u
#define RR_OFF_BATTLE_WORLD              0x60u
#define RR_OFF_BATTLE_MODELS             0x50u
#define RR_OFF_BATTLE_SLOTS              0x80u

// Slots
#define RR_OFF_SLOTS_DICTIONARY          0x10u
#define RR_OFF_SLOT_DATA                 0x10u
#define RR_OFF_SLOT_DESC                 0x18u
#define RR_OFF_SLOT_ENTITY_ID            0x20u
#define RR_OFF_SLOT_NICKNAME             0x30u
#define RR_OFF_SLOT_USER_ID              0x40u

// Seats
#define RR_OFF_SEATS_DATA                0x10u
#define RR_OFF_SEAT_OCCUPIED             0x20u
#define RR_OFF_SEAT_ENTITY_ID            0x28u

// Car
#define RR_OFF_CAR_ID                    0x10u
#define RR_OFF_CAR_OWNER_ROLE            0x48u
#define RR_OFF_CAR_DESC                  0x78u
#define RR_OFF_CAR_TRANSFORM             0xC0u
#define RR_OFF_CAR_SEATS                 0xE0u

// Helicopter
#define RR_OFF_HELI_ID                   0x10u
#define RR_OFF_HELI_OWNER_ROLE           0xE8u
#define RR_OFF_HELI_DESC                 0x48u
#define RR_OFF_HELI_TRANSFORM            0x70u
#define RR_OFF_HELI_SEATS                0x90u

// UnityEntry / Game / Battle
#define RR_OFF_ENTRY_GAME                0x28u
#define RR_OFF_GAME_MODEL                0xD8u
#define RR_OFF_GAME_BATTLE               0x10u

// Views
#define RR_OFF_VIEWS_BATTLE              0x18u
#define RR_OFF_VIEWS_MODEL               0x70u
#define RR_OFF_VIEWS_CHARACTERS          0x110u
#define RR_OFF_VIEWS_CARS                0x118u
#define RR_OFF_VIEWS_HELICOPTERS         0x120u

// Aim
#define RR_OFF_AIM_BATTLE                0x30u
#define RR_OFF_AIM_BRAIN                 0x48u

// Voice
#define RR_OFF_VOICE_ROOM_PARTICIPANTS   0x38u
#define RR_OFF_VOICE_STRING_MAP          0x18u
#define RR_OFF_VOICE_SLOT                0x38u
#define RR_OFF_VOICE_HIDE_ID             0x64u
#define RR_OFF_VOICE_USER_ID             0x18u
#define RR_OFF_VOICE_SPEAKING            0x21u

#endif /* ROBRUN_SDK_OFFSETS_H */