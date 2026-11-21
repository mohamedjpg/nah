/* rr_cheat.c - Read-only survey of the game's own cheat/developer models.
 *
 * Strictly read-only. Nothing here writes to the game, constructs a message or
 * calls a method. The point is to answer "is this realm a developer realm?"
 * before any detectable action, not to perform one.
 *
 * Offsets (dump 2026-11-21, verified against dump_index.json):
 *   BattleModel.<CheatModel>                0x360  ICheatModel
 *   ICheatModel.IsEnabled                   0x10   bool
 *   BattleModel.<CheatSpawnCarModel>        0x80
 *   BattleModel.<CheatSpawnHelicopterModel> 0x88
 *   GameModel.<NetworkStatusModel>          0x88
 *   NetworkStatusModel.CheatActivated       0x27   bool
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>

#include "rr_cheat.h"
#include "rr_game.h"
#include "rr_mem.h"
#include "rr_unity.h"

/* Offsets are local rather than in robrun_offsets.h: that header is regenerated
 * from a fresh dump, and these few are used by nothing else. The comment on each
 * names the exact metadata field so a re-dump can be checked by eye. */
#define BM_CHEAT_MODEL        0x360u   /* BattleModel.<CheatModel>k__BackingField */
#define BM_CHEAT_SPAWN_CAR    0x80u    /* BattleModel.<CheatSpawnCarModel>k__...   */
#define BM_CHEAT_SPAWN_HELI   0x88u    /* BattleModel.<CheatSpawnHelicopterModel> */
#define CHEATMODEL_IS_ENABLED 0x10u    /* CheatModel.<IsEnabled>k__BackingField   */
#define GM_NETWORK_STATUS     0x88u    /* GameModel.<NetworkStatusModel>k__...    */
#define NSM_CHEAT_ACTIVATED   0x27u    /* NetworkStatusModel.CheatActivated       */

static int read_bool_field(uint64_t obj, uint32_t off, int* out) {
    uint8_t v = 0;
    if (!PL(obj) || !rr_read(obj + off, &v, sizeof(v))) return 0;
    *out = v ? 1 : 0;
    return 1;
}

int rr_cheat_read(RR_CHEAT_STATE* out) {
    if (!out) return 0;
    memset(out, 0, sizeof(*out));
    out->roulette_cheat_number = -1;

    /* BattleModel, not the BattleEntitiesModel that game_scene_debug reports:
     * every field below hangs off BattleModel. */
    uint64_t battle = game_battle_model();
    if (!PL(battle) || !u_is(battle, "BattleModel")) return 0;

    out->have_battle = 1;
    out->battle      = battle;

    /* The master gate. A failed read is reported as gate_known = 0 rather than
     * as "disabled", so the UI never claims a realm is safe when it merely
     * could not read the flag. CheatModel is the only ICheatModel implementation
     * in the dump, so the class check is exact rather than a guess. */
    uint64_t cm = rr_u64(battle + BM_CHEAT_MODEL);
    if (PL(cm) && u_is(cm, "CheatModel")) {
        out->cheat_model = cm;
        out->gate_known  = read_bool_field(cm, CHEATMODEL_IS_ENABLED,
                                           &out->is_enabled);
    }

    /* Corroboration from the network layer: the server tells the client whether
     * cheats were activated for this session. Independent of the model above,
     * so a disagreement is meaningful. */
    {
        uint64_t game_model = game_game_model();
        if (PL(game_model) && u_is(game_model, "GameModel")) {
            uint64_t nsm = rr_u64(game_model + GM_NETWORK_STATUS);
            if (PL(nsm) && u_is(nsm, "NetworkStatusModel"))
                out->net_known = read_bool_field(nsm, NSM_CHEAT_ACTIVATED,
                                                 &out->net_cheat_activated);
        }
    }

    /* Which models the gate would unlock. Reported independently of the gate so
     * the tab can list capabilities even while disabled. Class-checked, because
     * a bare non-null pointer is also what a stale offset produces. */
    {
        uint64_t car = rr_u64(battle + BM_CHEAT_SPAWN_CAR);
        if (PL(car) && u_is(car, "CheatSpawnCarModel")) {
            out->spawn_car_model   = car;
            out->spawn_car_present = 1;
        }
        uint64_t heli = rr_u64(battle + BM_CHEAT_SPAWN_HELI);
        if (PL(heli) && u_is(heli, "CheatSpawnHelicopterModel")) {
            out->spawn_heli_model   = heli;
            out->spawn_heli_present = 1;
        }
    }

    /* RouletteCheatModel has no owner field anywhere in the metadata: it is
     * reachable only from the message dispatcher, so there is no pointer chain
     * to follow. Report unknown instead of guessing at an address. */
    out->roulette_cheat_known   = 0;
    out->roulette_cheat_enabled = 0;

    return 1;
}
