/* rr_roulette.h - Roulette model reader for ROB RUN.
 *
 * Reads the first active RouletteModel from WorldEntitiesModel._rouletteModels
 * (offset 0x478) and exposes the winning number, phase index and phase-end
 * timestamp so the menu can display them before bets close.
 *
 * Memory chain:
 *   WorldEntitiesModel._rouletteModels  +0x478  Dictionary<int, RouletteModel>
 *   RouletteModel.<Phase>k__BackingField +0x20   IPrimitiveModel<RoulettePhaseDescription>
 *   RouletteModel.<PhaseEndTs>k__BF      +0x28   IPrimitiveModel<long>
 *   RouletteModel.<WinningNumber>k__BF   +0x30   IPrimitiveModel<int>
 *
 *   IPrimitiveModel<T> (replicated) : value at object +0x18
 *   RoulettePhaseDescription.Index  : EnumItem.Index at object +0x28
 *
 * Phase indices (RoulettePhaseDescriptions static order):
 *   0 = Bets, 1 = Rolling, 2 = Dolly, 3 = Reward  (index from EnumItem.Index)
 */
#ifndef RR_ROULETTE_H
#define RR_ROULETTE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Snapshot of the first active roulette entity.
 * winning_number: -1 = not yet revealed, 0-36 = pocket number.
 * phase_index   :  0=Bets, 1=Rolling, 2=Dolly, 3=Reward, -1=unknown.
 * phase_end_ms  :  server Unix-ms timestamp when the current phase ends,
 *                  0 when unreadable.
 * valid         :  1 if the roulette dict was readable and contained entries.
 */
typedef struct RR_ROULETTE {
    int32_t  winning_number;
    int32_t  phase_index;
    int64_t  phase_end_ms;
    int      valid;
    int      roulette_count;   /* total entries in the dict */
} RR_ROULETTE;

/* Read roulette state from the live world.
 * world_ent must be the WorldEntitiesModel pointer (from game_world_addr
 * or the equivalent WorldEntitiesModel static field traversal).
 * Returns 1 on success, 0 on failure. */
int rr_roulette_read(uint64_t world_ent, RR_ROULETTE *out);

#ifdef __cplusplus
}
#endif

#endif /* RR_ROULETTE_H */
