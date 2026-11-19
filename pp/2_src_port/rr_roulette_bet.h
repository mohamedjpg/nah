/* rr_roulette_bet.h - Roulette auto-bet for ROB RUN.
 *
 * Places a bet on the winning number (or its color / dozen) the instant the
 * WinningNumber field is revealed.  Uses CreateRemoteThread to call the game's
 * own RouletteModel.AddBet function so the bet goes through the normal client
 * path and is submitted to the server.
 *
 * Required offsets (all verified against dump.cs 2026-11-12):
 *   RouletteModel.AddBet   RVA 0x489C8A0
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

#ifdef __cplusplus
}
#endif

#endif /* RR_ROULETTE_BET_H */
