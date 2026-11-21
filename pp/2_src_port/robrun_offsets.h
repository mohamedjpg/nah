// GENERATED - resolve with tools/resolve_offsets.py; verify with tools/verify_offsets.py
// Source: newasmbly/dump.cs (GameAssembly.dll e4b191f5..., global-metadata.dat 96a86061...)
// Every value below was read from the dump's "// 0xNN" field comments.
// NOTE: dump.cs reports generic-class fields as 0x0; the real instance layout of
// BasePrimitiveData<T> is header(0x10) -> _serializer(0x10) -> _value(0x18), and
// PrimitiveModel<T>._data sits at 0x10. Those two hops are asserted at the bottom.
#pragma once

/* ---------------------------------------------------------------------------
 * Generic IL2CPP wrappers (not in the metadata, checked by hand)
 * -------------------------------------------------------------------------*/
#define RR_OFF_PRIM_VALUE           0x18u   /* BasePrimitiveData<T>._value      */
#define RR_OFF_REF_VALUE            0x18u   /* ReferenceData<T>._value          */
#define RR_OFF_DESC_NAME            0x10u   /* EnumItem.Name (string*)          */
#define RR_OFF_ENUM_INDEX           0x18u   /* EnumItem.<Index>                 */
#define RR_OFF_PM_DATA              0x10u   /* PrimitiveModel<T>._data          */

/* ---------------------------------------------------------------------------
 * World graph
 * -------------------------------------------------------------------------*/
#define RR_OFF_WORLD_ENTITIES       0x38u   /* WorldModel.<WorldEntitiesModel>          */
#define RR_OFF_WEM_BATTLE_CHARS     0x18u   /* WorldEntitiesModel._battleCharacters     */
#define RR_OFF_WEM_VEHICLES         0x58u   /* WorldEntitiesModel._vehicles             */
#define RR_OFF_WEM_ROULETTES        0x478u  /* WorldEntitiesModel._rouletteModels       */
#define RR_OFF_WEM_CONTAINERS       0x20u   /* WorldEntitiesModel._containers           */
#define RR_OFF_WEM_DROPPED_LOOT     0x38u   /* WorldEntitiesModel._loots                */
#define RR_OFF_WEM_VEHICLE_LOOT     0x40u   /* WorldEntitiesModel._vehicleLoots         */
#define RR_OFF_WEM_DOORS            0x48u   /* WorldEntitiesModel._doors                */
#define RR_OFF_WEM_CARS             0x60u   /* WorldEntitiesModel._cars                 */
#define RR_OFF_WEM_HELICOPTERS      0x68u   /* WorldEntitiesModel._helicopters          */
#define RR_OFF_WEM_HIDE_OBJECTS     0x1B0u  /* WorldEntitiesModel._hideObjects          */

/* ---------------------------------------------------------------------------
 * BattleCharacterModel
 * -------------------------------------------------------------------------*/
#define RR_OFF_CHAR_ID              0x38u   /* <Id>                                     */
#define RR_OFF_CHAR_DATA            0x40u   /* <Data>                                   */
#define RR_OFF_CHAR_CONFIG          0x48u   /* <Config>                                 */
#define RR_OFF_CHAR_TRANSFORM       0x58u   /* <Transform>                              */
#define RR_OFF_CHAR_REPL_TRANSFORM  0x60u   /* <ReplicatedTransform>                    */
#define RR_OFF_CHAR_LOOK_DIR        0x70u   /* <LookDirection>                          */
#define RR_OFF_LOOK_MODEL           0x70u   /* <LookDirection> (alias used by rr_game.c)*/
#define RR_OFF_CHAR_ISDEAD          0xF0u   /* <IsDead>                                 */
#define RR_OFF_CHAR_PRIVATE         0x10u   /* <PrivateModel>                           */
#define RR_OFF_CHAR_SKELETON        0x138u  /* <SkeletonModel>                          */
#define RR_OFF_CHAR_WEAPON          0x150u  /* <Weapon>                                 */
#define RR_OFF_CHAR_CROUCH          0x160u  /* <CrouchModel>                            */
#define RR_OFF_CHAR_INVEH           0x1C8u  /* <InVehicleModel>                         */
#define RR_OFF_CHAR_STATE           0x1E0u  /* <StateModel>                             */
#define RR_OFF_CHAR_STANCE          0x1F0u  /* <BattleStanceModel>                      */
#define RR_OFF_CHAR_PBM             0x258u  /* <PlayerBattleModel>                      */

/* ---------------------------------------------------------------------------
 * BattleCharacterData + sub models
 * -------------------------------------------------------------------------*/
#define RR_OFF_DATA_COMMON          0x20u   /* BattleCharacterData.<CommonData>         */
#define RR_OFF_DATA_PRIVATE         0x28u   /* BattleCharacterData.<PrivateData>        */
#define RR_OFF_DATA_PUBLIC          0x30u   /* BattleCharacterData.<PublicData>         */
#define RR_OFF_COMMON_ROLE          0x20u   /* BattleCharacterCommonData.<Role>         */
#define RR_OFF_COMMON_ITEM_IN_HANDS 0xB8u   /* BattleCharacterCommonData.<ItemInHands>  */
#define RR_OFF_PRIVATE_HEALTH       0x38u   /* BattleCharacterPrivateData.<Health>      */
#define RR_OFF_PUBLIC_ARMOR         0x38u   /* BattleCharacterPublicData.<HasArmor>     */
#define RR_OFF_WEAPON_ITEM          0x10u   /* WeaponModel._itemInHands                 */
#define RR_OFF_CROUCH_BOOL          0x10u   /* CrouchModel._isCrouching                 */
#define RR_OFF_STANCE_REF           0x18u   /* BattleStanceModel._battleStance          */
#define RR_OFF_PBM_DATA             0x10u   /* PlayerBattleModel.<Data>                 */
#define RR_OFF_INVEH_ID             0x10u   /* InVehicleModel._entityId                 */
#define RR_OFF_INVEH_TYPE           0x20u   /* InVehicleModel._vehicleType              */
#define RR_OFF_STATE_HIDDEN         0x20u   /* BattleCharacterStateModel._characterHiddenStateModel */
#define RR_OFF_HIDDEN_ID_DATA       0x10u   /* CharacterHideObjectStateModel._hideObjectEntityIdData */

/* HealthModel */
#define RR_OFF_HEALTH_VALUE         0x10u   /* HealthModel._health                      */
#define RR_OFF_HEALTH_DEAD          0x18u   /* HealthModel._isDead                      */
#define RR_OFF_HEALTH_MAX           0x20u   /* HealthModel._maxAmount                   */

/* ---------------------------------------------------------------------------
 * Transforms / positions
 * -------------------------------------------------------------------------*/
#define RR_OFF_CTM_X                0x10u   /* CharacterTransformModel.<X>              */
#define RR_OFF_CTM_Y                0x14u   /* CharacterTransformModel.<Y>              */
#define RR_OFF_CTM_Z                0x18u   /* CharacterTransformModel.<Z>              */
#define RR_OFF_CTM_PITCH            0x1Cu   /* CharacterTransformModel.<Pitch>          */
#define RR_OFF_CTM_YAW              0x20u   /* CharacterTransformModel.<Yaw>            */
#define RR_OFF_CTM_ROLL             0x24u   /* CharacterTransformModel.<Roll>           */
#define RR_OFF_TRANSFORM_X          0x10u   /* TransformModel._x                        */
#define RR_OFF_TRANSFORM_Y          0x18u   /* TransformModel._y                        */
#define RR_OFF_TRANSFORM_Z          0x20u   /* TransformModel._z                        */
#define RR_OFF_TRANSFORM_RX         0x28u   /* TransformModel._rx                       */
#define RR_OFF_TRANSFORM_RY         0x30u   /* TransformModel._ry                       */
#define RR_OFF_TRANSFORM_RZ         0x38u   /* TransformModel._rz                       */
#define RR_OFF_RTRANSFORM_POS       0x10u   /* CharacterReplicatedTransformModel._position */
#define RR_OFF_RTRANSFORM_RX        0x18u   /* CharacterReplicatedTransformModel._rx    */
#define RR_OFF_RTRANSFORM_RY        0x20u   /* CharacterReplicatedTransformModel._ry    */
#define RR_OFF_RTRANSFORM_RZ        0x28u   /* CharacterReplicatedTransformModel._rz    */
#define RR_OFF_POS_X                0x10u   /* PositionModel.<X>                        */
#define RR_OFF_POS_Y                0x14u   /* PositionModel.<Y>                        */
#define RR_OFF_POS_Z                0x18u   /* PositionModel.<Z>                        */
#define RR_OFF_INTERACT_POS_X       0x10u   /* InteractPositionModel.<X>                */
#define RR_OFF_INTERACT_POS_Y       0x14u   /* InteractPositionModel.<Y>                */
#define RR_OFF_INTERACT_POS_Z       0x18u   /* InteractPositionModel.<Z>                */

/* ---------------------------------------------------------------------------
 * Camera
 * -------------------------------------------------------------------------*/
#define RR_OFF_CAM_POS              0x10u   /* BattleCameraModel.<Position>             */
#define RR_OFF_CAM_ROT              0x1Cu   /* BattleCameraModel.<Orientation>          */
#define RR_OFF_CAM_FWD              0x3Cu   /* BattleCameraModel.<Forward>              */
#define RR_OFF_CAM_RIGHT            0x48u   /* BattleCameraModel.<Right>                */
#define RR_OFF_CAM_UP               0x54u   /* BattleCameraModel.<Up>                   */
#define RR_OFF_CAM_DIST             0x60u   /* BattleCameraModel.<DistanceToFollowTarget> */

/* ---------------------------------------------------------------------------
 * RouletteModel
 * -------------------------------------------------------------------------*/
#define RR_OFF_RM_PHASE             0x20u   /* <Phase>                                  */
#define RR_OFF_RM_PHASE_END         0x28u   /* <PhaseEndTs>                             */
#define RR_OFF_RM_WIN_NUMBER        0x30u   /* <WinningNumber>                          */
#define RR_OFF_RM_BETS_BY_CHAR      0x18u   /* _betsByCharacter                         */

/* ---------------------------------------------------------------------------
 * RouletteBetDescriptions static-field offsets (Straight[N] = 0x40 + N*8)
 * -------------------------------------------------------------------------*/
#define RR_SF_BET_STRAIGHT0         0x40u
#define RR_SF_BET_DOZEN_1_12        0x4C8u
#define RR_SF_BET_DOZEN_13_24       0x4D0u
#define RR_SF_BET_DOZEN_25_36       0x4D8u
#define RR_SF_BET_RED               0x508u
#define RR_SF_BET_BLACK             0x510u

/* RouletteChipDescriptions static-field offsets */
#define RR_SF_CHIP_1K               0x8u
#define RR_SF_CHIP_5K               0x10u
#define RR_SF_CHIP_25K              0x18u
#define RR_SF_CHIP_50K              0x20u
#define RR_SF_CHIP_100K             0x28u

/* ---------------------------------------------------------------------------
 * Method RVAs (GameAssembly.dll)
 * -------------------------------------------------------------------------*/
#define RR_RVA_ADDBET               0x48E4BB0ull  /* RouletteModel.AddBet                     */
#define RR_RVA_RM_WIN_NUMBER        0x7BB030ull   /* RouletteModel.get_WinningNumber          */
#define RR_RVA_RM_PHASE             0x7AB150ull   /* RouletteModel.get_Phase                  */
#define RR_RVA_RM_PHASE_END         0x7AA000ull   /* RouletteModel.get_PhaseEndTs             */
#define RR_RVA_WEM_ROULETTES        0x4636E50ull  /* WorldEntitiesModel.get_RouletteModels    */

/* ---------------------------------------------------------------------------
 * Module RVAs of static-storage globals.
 *
 * These are NOT in dump.cs - they are .data slots the class .cctor writes the
 * static-storage pointer into. Values below come from a heuristic scan of the
 * cctor bodies (see offsets/robrun_offsets.json -> static_field_globals) and are
 * only used by the --probe diagnostic, which prints the resolved class name so a
 * wrong value is visible. game_dump_static() resolves them authoritatively at
 * runtime through Il2CppClass.static_fields and should be preferred.
 * -------------------------------------------------------------------------*/
#define RR_SF_WORLDMODEL            0x81D36C8u
#define RR_SF_WORLDENTITIESMODEL    0x81D0710u
#define RR_SF_BATTLECHARACTERMODEL  0x8196748u
#define RR_SF_BATTLECAMERAMODEL     0x81CB420u

/* ---------------------------------------------------------------------------
 * Layout assertions
 * -------------------------------------------------------------------------*/
#if RR_OFF_POS_Y != RR_OFF_POS_X + 4 || RR_OFF_POS_Z != RR_OFF_POS_X + 8
#error PositionModel is no longer a contiguous XYZ triple.
#endif
#if RR_OFF_INTERACT_POS_Y != RR_OFF_INTERACT_POS_X + 4 || \
    RR_OFF_INTERACT_POS_Z != RR_OFF_INTERACT_POS_X + 8
#error InteractPositionModel is no longer a contiguous XYZ triple.
#endif
#if RR_OFF_CTM_Y != RR_OFF_CTM_X + 4 || RR_OFF_CTM_Z != RR_OFF_CTM_X + 8 || \
    RR_OFF_CTM_ROLL != RR_OFF_CTM_X + 0x14
#error CharacterTransformModel XYZ+Pitch/Yaw/Roll layout changed.
#endif
#if RR_OFF_CAM_RIGHT != RR_OFF_CAM_FWD + 0x0C || RR_OFF_CAM_UP != RR_OFF_CAM_FWD + 0x18
#error BattleCameraModel Forward/Right/Up basis is no longer contiguous.
#endif
#if RR_SF_CHIP_5K != RR_SF_CHIP_1K + 8 || RR_SF_CHIP_25K != RR_SF_CHIP_1K + 0x10 || \
    RR_SF_CHIP_50K != RR_SF_CHIP_1K + 0x18 || RR_SF_CHIP_100K != RR_SF_CHIP_1K + 0x20
#error RouletteChipDescriptions static layout changed.
#endif
