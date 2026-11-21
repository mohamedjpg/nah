/* rr_cheat.h - Read-only survey of the game's own cheat/developer models.
 *
 * The dump shows the client ships a full cheat surface gated on a single flag:
 *
 *   BattleModel.<CheatModel>      0x360   ICheatModel.IsEnabled  +0x10
 *   BattleModel.<CheatSpawnCarModel>        0x80
 *   BattleModel.<CheatSpawnHelicopterModel> 0x88
 *   GameModel.<NetworkStatusModel>  0x88   .CheatActivated        +0x27
 *   RouletteCheatModel             no owner field, message-only
 *
 * On a developer realm the server sets IsEnabled. Everywhere else it is false
 * and the cheat messages are validated server-side, so this module NEVER writes
 * and never sends anything. It reports what the current realm has enabled so the
 * overlay can show which actions are actually legitimate here.
 *
 * The value is diagnostic: it tells you whether a realm is a dev realm before
 * you risk a detectable action, rather than after.
 */
#ifndef RR_CHEAT_H
#define RR_CHEAT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct RR_CHEAT_STATE {
    int      have_battle;      /* 1 = BattleModel resolved                     */
    uint64_t battle;           /* BattleModel*                                 */
    uint64_t cheat_model;      /* ICheatModel*                                 */
    int      is_enabled;       /* ICheatModel.IsEnabled   (the master gate)    */
    int      gate_known;       /* 1 = is_enabled was actually read             */

    /* Secondary signals that corroborate a developer realm. */
    int      net_cheat_activated;   /* NetworkStatusModel.CheatActivated        */
    int      net_known;

    /* Models the gate would unlock. Presence is reported separately from the
     * gate so the UI can show what exists even when disabled. */
    uint64_t spawn_car_model;       /* BattleModel.<CheatSpawnCarModel>  +0x80  */
    uint64_t spawn_heli_model;      /* BattleModel.<CheatSpawnHelicopterModel>  */
    int      spawn_car_present;
    int      spawn_heli_present;

    /* RouletteCheatModel has no owner field anywhere in the metadata; it is
     * reachable only through the message dispatcher. Left in the struct so the
     * UI can distinguish "no chain exists" from "chain exists but is off"; both
     * are currently 0 / -1 and are never populated by rr_cheat_read(). */
    int      roulette_cheat_known;
    int      roulette_cheat_enabled;
    int      roulette_cheat_number;  /* CheatWinningNumber, -1 when unknown     */
} RR_CHEAT_STATE;

/* Fill `out` from the live battle model. Read-only: performs no writes.
 * Returns 1 when at least the battle model resolved, 0 otherwise. */
int rr_cheat_read(RR_CHEAT_STATE* out);

#ifdef __cplusplus
}
#endif

#endif /* RR_CHEAT_H */
