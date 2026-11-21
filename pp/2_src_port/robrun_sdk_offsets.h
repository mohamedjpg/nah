/* GENERATED - resolve with tools/resolve_offsets.py
 * Supplemental managed instance fields from the 2026-11-21 dump.cs.
 * Source: newasmbly/dump.cs (GameAssembly.dll e4b191f5..., global-metadata.txt 96a86061...)
 *
 * Every macro here is referenced by at least one .c file; the audit script
 * tools/audit_macros.py enforces that. Offsets that the current dump cannot
 * resolve are listed at the bottom as removed, not guessed.
 */
#ifndef ROBRUN_SDK_OFFSETS_H
#define ROBRUN_SDK_OFFSETS_H

/* ---------------------------------------------------------------------------
 * World objects
 * -------------------------------------------------------------------------*/
/* NOTE: the WorldEntitiesModel dictionaries (_containers, _doors, _cars,
 * _helicopters, _loots, _vehicleLoots, _hideObjects, _vehicles, _rouletteModels)
 * all live in robrun_offsets.h - do not repeat them here, rr_game.c includes
 * both headers and a duplicate define is a redefinition error. */

#define RR_OFF_CONTAINER_POS             0x28u   /* ContainerModel.<PositionModel>              */
#define RR_OFF_DOOR_STATE                0x30u   /* DoorModel.<State>                           */
#define RR_OFF_DOOR_POS                  0x38u   /* DoorModel.<Position>                        */
#define RR_OFF_DOOR_STATE_DATA           0x10u   /* DoorStateModel._state                       */
#define RR_OFF_DROPPED_LOOT_POS          0x28u   /* LootModel.<InteractPositionModel>           */
#define RR_OFF_VEHICLE_LOOT_POS          0x28u   /* VehicleLootModel.<InteractPositionModel>    */

/* HideObjectModel / LocationHideObjectDescription */
#define RR_OFF_HIDE_DESC                 0x18u   /* HideObjectModel.<Description>               */
#define RR_OFF_HIDE_OCCUPANT             0x10u   /* HideObjectModel._entityId                   */
#define RR_OFF_HIDE_DESC_ID              0x20u   /* LocationHideObjectDescription.<EntityId>    */
#define RR_OFF_HIDE_DESC_TYPE            0x28u   /* <HideObjectDescriptionFunc>                 */
#define RR_OFF_HIDE_DESC_POS             0x30u   /* <Position>                                  */
#define RR_OFF_HIDE_DESC_ROT             0x3Cu   /* <Orientation>                               */
#define RR_OFF_HIDE_DESC_INTERACT        0x4Cu   /* <InteractPoint>                             */

/* ---------------------------------------------------------------------------
 * BattleModel
 * -------------------------------------------------------------------------*/
#define RR_OFF_BATTLE_ENTITIES           0x90u   /* <BattleEntitiesModel>                       */
#define RR_OFF_BATTLE_AIM                0x198u  /* <AimTargetModel>                            */
#define RR_OFF_BATTLE_CAMERA             0x358u  /* <BattleCameraModel>                         */
#define RR_OFF_BATTLE_PLAYER_SLOTS       0x4D0u  /* <BattleCharacterSlotsModel>                 */
#define RR_OFF_BATTLE_VOICE_ROOM         0x630u  /* <VoiceChatBattleRoomModel>                  */
/* BattleModel.<WorldEntitiesModel> - duplicate of BattleEntitiesModel._worldEntitiesModel.
 * rr_game.c uses it as a fallback when the BattleEntitiesModel link is not up yet. */
#define RR_OFF_BATTLE_WORLD_B            0x518u

/* BattleEntitiesModel */
#define RR_OFF_BATTLE_WORLD              0x60u   /* _worldEntitiesModel                         */
#define RR_OFF_BATTLE_MODELS             0x50u   /* _models                                     */
#define RR_OFF_BATTLE_SLOTS              0x80u   /* _characterSlotModel                         */

/* ---------------------------------------------------------------------------
 * Updaters
 * -------------------------------------------------------------------------*/
#define RR_OFF_VIEWS_BATTLE              0x18u   /* BattleEntitiesUpdater._battleEntitiesModel  */
#define RR_OFF_VIEWS_MODEL               0x70u   /* ._battleModel                               */
#define RR_OFF_VIEWS_CHARACTERS          0x110u  /* ._characterEntityViews                      */
#define RR_OFF_VIEWS_CARS                0x118u  /* ._carEntityViews                            */
#define RR_OFF_VIEWS_HELICOPTERS         0x120u  /* ._helicopterEntityViews                     */
#define RR_OFF_AIM_BATTLE                0x30u   /* BattleAimTargetUpdater._battleEntitiesModel */
#define RR_OFF_AIM_BRAIN                 0x48u   /* ._cinemachineBrain                          */

/* ---------------------------------------------------------------------------
 * Character slots
 * -------------------------------------------------------------------------*/
#define RR_OFF_SLOTS_DICTIONARY          0x10u   /* BattleCharacterSlotsModel._slots            */
#define RR_OFF_SLOT_DATA                 0x10u   /* BattleCharacterSlotModel._data              */
#define RR_OFF_SLOT_DESC                 0x18u   /* .<Description>                              */
#define RR_OFF_SLOT_ENTITY_ID            0x20u   /* BattleCharacterSlotData.<EntityId>          */
#define RR_OFF_SLOT_NICKNAME             0x30u   /* .<Nickname>                                 */
#define RR_OFF_SLOT_USER_ID              0x40u   /* .<EOSProductUserId>                         */

/* ---------------------------------------------------------------------------
 * Vehicles
 * -------------------------------------------------------------------------*/
#define RR_OFF_SEATS_DATA                0x10u   /* VehicleSeatsModel._data                     */
#define RR_OFF_SEAT_OCCUPIED             0x20u   /* VehicleSeatData.<Occupied>                  */
#define RR_OFF_SEAT_ENTITY_ID            0x28u   /* VehicleSeatData.<EntityId>                  */
#define RR_OFF_CAR_ID                    0x10u   /* CarModel.<Id>                               */
#define RR_OFF_CAR_OWNER_ROLE            0x48u   /* .<OwnerRole>                                */
#define RR_OFF_CAR_DESC                  0x78u   /* .<Description>                              */
#define RR_OFF_CAR_TRANSFORM             0xC0u   /* .<Transform>                                */
#define RR_OFF_CAR_SEATS                 0xE0u   /* .<Seats>                                    */
#define RR_OFF_HELI_ID                   0x10u   /* HelicopterModel.<Id>                        */
#define RR_OFF_HELI_DESC                 0x48u   /* .<Description>                              */
#define RR_OFF_HELI_TRANSFORM            0x70u   /* .<Transform>                                */
#define RR_OFF_HELI_SEATS                0x90u   /* .<Seats>                                    */
#define RR_OFF_HELI_OWNER_ROLE           0xE8u   /* .<OwnerRole>                                */

/* ---------------------------------------------------------------------------
 * UnityEntry / Game
 * -------------------------------------------------------------------------*/
#define RR_OFF_ENTRY_GAME                0x28u   /* UnityEntry._game                           */
#define RR_OFF_GAME_MODEL                0xD8u   /* Game.<GameModel>                           */
#define RR_OFF_GAME_BATTLE               0x10u   /* GameModel._battleModel                     */

/* ---------------------------------------------------------------------------
 * Voice chat
 * -------------------------------------------------------------------------*/
#define RR_OFF_VOICE_ROOM_PARTICIPANTS   0x38u   /* VoiceChatRoomModel.ParticipantsModel       */
#define RR_OFF_VOICE_STRING_MAP          0x18u   /* VoiceChatParticipantsModel._participantStringIdToModels */
#define RR_OFF_VOICE_SLOT                0x38u   /* VoiceChatBattleParticipantModel.<SlotDescription>       */
#define RR_OFF_VOICE_HIDE_ID             0x64u   /* .<HideObjectEntityId>                                   */
#define RR_OFF_VOICE_USER_ID             0x18u   /* VoiceChatRoomParticipantModel.<ProductUserIdString>     */
#define RR_OFF_VOICE_SPEAKING            0x21u   /* .<IsSpeaking>                                           */

/* ---------------------------------------------------------------------------
 * REMOVED - the 2026-11-21 dump has no such field. Kept as a note only.
 *
 *   RR_OFF_CONTAINER_INV   (was 0x30) ContainerModel has no inventory field;
 *                                     inventories hang off WorldEntitiesModel
 *                                     (_containerInventories @ 0x168).
 *   RR_OFF_INVEH_VEHICLE   (was 0x30) InVehicleModel is only
 *                                     _entityId 0x10 / _seatSlot 0x18 /
 *                                     _vehicleType 0x20. Use _entityId.
 * -------------------------------------------------------------------------*/

#endif /* ROBRUN_SDK_OFFSETS_H */
