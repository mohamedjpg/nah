// Auto-generated from dump.cs (newasmbly) - DO NOT EDIT
// Synced 2026-11-21 against newasmbly/dump.cs + newasmbly/script.json
// (GameAssembly.dll e4b191f5..., global-metadata.dat 96a86061...).
#pragma once

// World and entity graph.
#define RR_OFF_WORLD_ENTITIES       0x38u
#define RR_OFF_WEM_BATTLE_CHARS     0x18u
#define RR_OFF_WEM_VEHICLES         0x58u
#define RR_OFF_WEM_ROULETTES        0x478u

// BattleCharacterModel fields (all CompilerGenerated backing fields)
#define RR_OFF_CHAR_ID              0x38u
#define RR_OFF_CHAR_DATA            0x40u
#define RR_OFF_CHAR_CONFIG          0x48u
#define RR_OFF_CHAR_TRANSFORM       0x58u
#define RR_OFF_CHAR_REPL_TRANSFORM  0x60u
#define RR_OFF_CHAR_ISDEAD          0xF0u
#define RR_OFF_CHAR_PRIVATE         0x10u
#define RR_OFF_CHAR_WEAPON          0x150u
#define RR_OFF_CHAR_CROUCH          0x160u
#define RR_OFF_CHAR_STANCE          0x1F0u
#define RR_OFF_CHAR_PBM             0x258u

// RouletteModel fields (same as before - no change)
#define RR_OFF_RM_PHASE             0x20u
#define RR_OFF_RM_PHASE_END         0x28u
#define RR_OFF_RM_WIN_NUMBER        0x30u
#define RR_OFF_RM_BETS_BY_CHAR      0x18u

// AddBet RVA
#define RR_RVA_ADDBET               0x48E4BB0ull

// Static field offsets - RouletteBetDescriptions
#define RR_SF_BET_STRAIGHT0         0x40u
#define RR_SF_BET_DOZEN_1_12        0x4C8u
#define RR_SF_BET_DOZEN_13_24       0x4D0u
#define RR_SF_BET_DOZEN_25_36       0x4D8u
#define RR_SF_BET_RED               0x508u
#define RR_SF_BET_BLACK             0x510u

// Static field offsets - RouletteChipDescriptions (CompilerGenerated backing fields)
#define RR_SF_CHIP_1K               0x8u
#define RR_SF_CHIP_5K               0x10u
#define RR_SF_CHIP_25K              0x18u
#define RR_SF_CHIP_50K              0x20u
#define RR_SF_CHIP_100K             0x28u