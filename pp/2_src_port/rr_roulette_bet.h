/* rr_roulette_bet.h - Roulette auto-bet for ROB RUN.
 *
 * Places a bet on the winning number (or its color / dozen) the instant the
 * WinningNumber field is revealed.  Uses CreateRemoteThread to call the game's
 * own RouletteModel.AddBet function so the bet goes through the normal client
 * path and is submitted to the server.
 *
 * Required offsets (all verified against dump.cs 2026-11-12):
 *   RouletteModel.AddBet   RVA 0x48E4BB0 (RR_RVA_ADDBET)
 *   RouletteBetDescriptions static fields:
 *     Straight[N]  = sf + 0x40 + N*8  (N = 0..36)
 *     Dozen_1_12   = sf + 0x4C8
 *     Dozen_13_24  = sf + 0x4D0
 *     Dozen_25_36  = sf + 0x4D8
 *     Red          = sf + 0x508
 *     Black        = sf + 0x510
 *   RouletteChipDescriptions static fields:
 *     Chip1k   = sf + 0x08
 *     Chip5k   = sf + 0x10
 *     Chip25k  = sf + 0x18
 *     Chip50k  = sf + 0x20
 *     Chip100k = sf + 0x28
 */
#ifndef RR_ROULETTE_BET_H
#define RR_ROULETTE_BET_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Chip size index (must match the HTML UI order). */
#define RR_CHIP_1K    0
#define RR_CHIP_5K    1
#define RR_CHIP_25K   2
#define RR_CHIP_50K   3
#define RR_CHIP_100K  4

/* Bet mode. */
#define RR_BET_NUMBER  0   /* straight bet on the winning number */
#define RR_BET_COLOR   1   /* red / black (green = 0 → skip)    */
#define RR_BET_DOZEN   2   /* dozen 1-12 / 13-24 / 25-36        */

typedef struct RR_BET_CONFIG {
    int enabled;       /* 0 = disabled                          */
    int chip_index;    /* RR_CHIP_* constant                    */
    int repeat;        /* how many chips to stack (1-20)        */
    int mode;          /* RR_BET_NUMBER / COLOR / DOZEN         */
} RR_BET_CONFIG;

/* Call once per winning-number reveal.
 *
 * world_ent     : WorldEntitiesModel pointer (from game_world_addr())
 * winning       : 0-36
 * cfg           : caller-owned bet configuration
 * local_char_id : character-id of the local player (from rr_local_player()
 *                 → BattleCharacterModel+0x38); pass 0 to skip the placement.
 *
 * Returns 1 if a placement was attempted, 0 if skipped (wrong phase, bad
 * pointers, green number for a color-bet, etc.).
 */
int rr_roulette_place_bet(uint64_t world_ent, int winning,
                          const RR_BET_CONFIG *cfg, int32_t local_char_id);

/* Cache the klass pointers needed for static-field access.  Call once after
 * attach when you have a live RouletteModel available, or let place_bet()
 * discover them lazily on the first call. */
void rr_roulette_bet_reset_cache(void);

/* ---------------------------------------------------------------------------
 * Discovery helpers, shared with rr_roulette_sniper.c.
 *
 * These expose the expensive part of place_bet() (model lookup, static-field
 * discovery, module lookup) so the sniper can pay for it once and keep only
 * the pointer arithmetic on the hot path.  All of them are cheap once warm.
 * --------------------------------------------------------------------------*/

/* Cached first-live RouletteModel*, or 0. */
uint64_t rr_roulette_model_ptr(void);

/* Cached RouletteBetDescriptions static-fields blob, or 0. */
uint64_t rr_roulette_bet_sf_ptr(void);

/* Run the one-time discovery for this world/model/config.
 * Returns 1 on success.  Idempotent; safe to call every round. */
int rr_roulette_bet_prepare(uint64_t world_ent, const RR_BET_CONFIG *cfg,
                            int32_t local_char_id);

/* RouletteBetDescription* for `winning` (0-36) under `mode` (RR_BET_*).
 * Returns 0 when the number cannot be expressed as that bet (0 for colour). */
uint64_t rr_roulette_bet_desc(int winning, int mode);

/* RouletteChipDescription* for a RR_CHIP_* index, or 0. */
uint64_t rr_roulette_chip_desc(int chip_index);

/* Chip description resolved by the last rr_roulette_bet_prepare() call. */
uint64_t rr_roulette_prepared_chip(void);

/* Absolute VA of RouletteModel.AddBet inside the game, or 0. */
uint64_t rr_roulette_addbet_va(void);

#ifdef __cplusplus
}
#endif

#endif /* RR_ROULETTE_BET_H */
