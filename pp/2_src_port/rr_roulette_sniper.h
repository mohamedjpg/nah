/* rr_roulette_sniper.h - Pre-armed low-latency bet trigger for ROB RUN.
 *
 * Why this exists
 * ---------------
 * rr_roulette_place_bet() does a CreateRemoteThread + page alloc + class-scan
 * on every call.  Measured end-to-end that is 5-30 ms, and the first call of a
 * session is far worse because discover_chip_sf() walks the IL2CPP class list.
 * If the server replicates WinningNumber only a few ms before it closes bets,
 * that is the difference between a filled ticket and a rejection.
 *
 * The sniper inverts it:
 *
 *   1. arm()      once per session: resolve every pointer, allocate one page in
 *                 the game, write a persistent poll stub, start ONE thread that
 *                 sleeps in SwitchToThread() waiting on a "go" flag.
 *   2. fire()     hot path: two small driver writes.  No allocation, no thread
 *                 creation, no discovery.  Median latency is a few tens of us.
 *   3. disarm()   on detach: tell the stub to exit and drop the cached state.
 *
 * The stub, the parameter block and the ABI are described in rr_roulette_sniper.c.
 *
 * Arm/fire are safe to call from the poll thread; fire() is a no-op unless the
 * sniper is armed and the game is attached.
 */
#ifndef RR_ROULETTE_SNIPER_H
#define RR_ROULETTE_SNIPER_H

#include <stdint.h>

#include "rr_roulette_bet.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Arm the sniper for the first live roulette model in the world.
 *
 * world_ent     : WorldEntitiesModel pointer (from game_world_addr())
 * cfg           : bet configuration (chip + repeat + mode), copied internally
 * local_char_id : local player character id
 *
 * Idempotent.  Calling it again re-reads the model pointer and the chip index,
 * which is what you want when the player moves between roulette tables.
 * Returns 1 on success, 0 if any pointer could not be resolved.
 */
int rr_roulette_sniper_arm(uint64_t world_ent,
                           const RR_BET_CONFIG *cfg,
                           int32_t local_char_id);

/* Re-point the armed stub at a (possibly new) RouletteModel.  Cheap: one read
 * plus, when the pointer moved, one 8-byte write.  Returns 1 if armed. */
int rr_roulette_sniper_set_model(uint64_t roulette_model);

/* Hot path.  Places the configured bet on `winning` (0-36).
 *
 * Two driver writes: the bet-description pointer, then the go flag.
 * Returns
 *    1  the stub was signalled
 *    0  not armed, bad number (e.g. 0 with a colour bet), or a write failed
 */
int rr_roulette_sniper_fire(int winning);

/* 1 when the stub is alive and armed. */
int rr_roulette_sniper_armed(void);

/* Address of the parameter block in the game, for diagnostics / the HTML
 * telemetry panel.  Zero when not armed. */
uint64_t rr_roulette_sniper_param_addr(void);

/* Number of successful fires this session (diagnostics). */
int rr_roulette_sniper_fire_count(void);

/* Tell the stub to exit and drop all cached state.  Safe to call repeatedly.
 * The remote page is not freed (the driver has no free IOCTL); the stub exits
 * and the page stays allocated until the game exits. */
void rr_roulette_sniper_disarm(void);

#ifdef __cplusplus
}
#endif

#endif /* RR_ROULETTE_SNIPER_H */
