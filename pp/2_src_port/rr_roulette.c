/* rr_roulette.c - Roulette model reader for ROB RUN.
 *
 * Memory chain (all offsets verified against dump.cs):
 *
 *   WorldEntitiesModel._rouletteModels  offset 0x478
 *     Dictionary<int, RouletteModel>  (walked with u_dict())
 *
 *   RouletteModel fields (dump.cs line 159431):
 *     0x20  <Phase>k__BackingField       PrimitiveModel<RoulettePhaseDescription>*
 *     0x28  <PhaseEndTs>k__BackingField  PrimitiveModel<long>*
 *     0x30  <WinningNumber>k__BackingField PrimitiveModel<int>*
 *
 *   Two concrete IPrimitiveModel<T> implementations exist (dump.cs line 163517):
 *
 *   A) NoReplicationPrimitiveModel<T>
 *      Value field // 0x0  → stored at obj+0x10 (after 0x10-byte il2cpp header)
 *      Read:  obj + 0x10  → value directly
 *
 *   B) PrimitiveModel<T>  (network-replicated, used for WinningNumber/Phase/PhaseEndTs)
 *      _data field // 0x0  → obj+0x10 holds an IPrimitiveData<T>* (e.g. IntData)
 *      Then IPrimitiveData value at _data + 0x18  (RR_OFF_PRIM_VALUE, measured)
 *      Read:  obj+0x10 → data_ptr,  data_ptr+0x18 → value
 *
 *   We try (B) first (most likely for replicated models), then fall back to (A).
 *
 *   RoulettePhaseDescription.Index (EnumItem):
 *      After resolving the Phase PrimitiveModel, the value is a pointer to
 *      a RoulettePhaseDescription (reference type EnumItem subclass).
 *      EnumItem.<Index>k__BackingField is at field 0x18 → obj+0x28.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>

#include "rr_roulette.h"
#include "rr_mem.h"
#include "rr_unity.h"

/* WorldEntitiesModel._rouletteModels offset. */
#define WEM_ROULETTE_DICT_OFF  0x478u

/* RouletteModel backing field offsets (field offset = memory offset directly). */
#define RM_PHASE_OFF        0x20u
#define RM_PHASE_END_OFF    0x28u
#define RM_WIN_NUMBER_OFF   0x30u

/* IL2CPP object layout constants. */
#define IL2CPP_HDR         0x10u   /* klass + monitor pointers = 16 bytes */

/* PrimitiveModel<T>._data is field // 0x0 → at obj + IL2CPP_HDR. */
#define PM_DATA_OFF        (IL2CPP_HDR + 0x00u)   /* 0x10 */
/* IPrimitiveData<T> value offset (measured, same as RR_OFF_PRIM_VALUE). */
#define PD_VALUE_OFF       0x18u

/* NoReplicationPrimitiveModel<T>.Value is field // 0x0 → at obj + IL2CPP_HDR. */
#define NRPM_VALUE_OFF     (IL2CPP_HDR + 0x00u)   /* 0x10 */

/* EnumItem.<Index>k__BackingField is field // 0x18 → at obj + 0x28. */
#define ENUM_INDEX_OFF     0x28u

/* Minimum plausible pointer. */
#define PL(p) ((p) > 0x10000ULL && (p) < 0x7FFFFFFFFFFFULL)

/* ---------------------------------------------------------------------------
 * read_prim_int()
 * Reads an int from either PrimitiveModel<int> or NoReplicationPrimitiveModel<int>.
 * Returns 1 on success, 0 on failure.
 * --------------------------------------------------------------------------*/
static int read_prim_int(uint64_t prim_obj, int32_t *out)
{
    if (!PL(prim_obj) || !out) return 0;

    /* Try PrimitiveModel<T> (network replicated):
     *   _data ptr at prim_obj + 0x10, then value at _data + 0x18. */
    uint64_t data_ptr = rr_u64(prim_obj + PM_DATA_OFF);
    if (PL(data_ptr)) {
        int32_t v = rr_i32(data_ptr + PD_VALUE_OFF);
        if (rr_ok()) { *out = v; return 1; }
    }

    /* Fallback: NoReplicationPrimitiveModel<T>:
     *   value sits directly at prim_obj + 0x10. */
    {
        int32_t v = rr_i32(prim_obj + NRPM_VALUE_OFF);
        if (rr_ok()) { *out = v; return 1; }
    }

    return 0;
}

/* read_prim_long(): same two-hop pattern for long fields. */
static int read_prim_long(uint64_t prim_obj, int64_t *out)
{
    if (!PL(prim_obj) || !out) return 0;

    uint64_t data_ptr = rr_u64(prim_obj + PM_DATA_OFF);
    if (PL(data_ptr)) {
        int64_t v = 0;
        if (rr_read(data_ptr + PD_VALUE_OFF, &v, sizeof(v)) && rr_ok()) {
            *out = v; return 1;
        }
    }

    /* Fallback: value directly at obj+0x10 (8 bytes). */
    {
        int64_t v = 0;
        if (rr_read(prim_obj + NRPM_VALUE_OFF, &v, sizeof(v)) && rr_ok()) {
            *out = v; return 1;
        }
    }

    return 0;
}

/* read_prim_ref(): resolve PrimitiveModel<RefType> → pointer to the ref object.
 * For a reference-type T, the _data value IS a pointer, 8 bytes at PD_VALUE_OFF. */
static uint64_t read_prim_ref(uint64_t prim_obj)
{
    if (!PL(prim_obj)) return 0;

    uint64_t data_ptr = rr_u64(prim_obj + PM_DATA_OFF);
    if (PL(data_ptr)) {
        uint64_t ref = rr_u64(data_ptr + PD_VALUE_OFF);
        if (PL(ref)) return ref;
    }

    /* Fallback: ref pointer at obj+0x10. */
    uint64_t ref = rr_u64(prim_obj + NRPM_VALUE_OFF);
    return PL(ref) ? ref : 0;
}

/* ---------------------------------------------------------------------------
 * rr_roulette_read()
 * --------------------------------------------------------------------------*/
int rr_roulette_read(uint64_t world_ent, RR_ROULETTE *out)
{
    if (!out) return 0;
    out->valid          = 0;
    out->winning_number = -1;
    out->phase_index    = -1;
    out->phase_end_ms   = 0;
    out->roulette_count = 0;

    if (!PL(world_ent)) return 0;

    /* Step 1: Get the Dictionary<int, RouletteModel> at WEM+0x478. */
    uint64_t roulette_dict = rr_u64(world_ent + WEM_ROULETTE_DICT_OFF);
    if (!PL(roulette_dict)) return 0;

    /* Step 2: Walk the dictionary using u_dict() — same as the rest of the game code.
     * u_dict handles: entries ptr at +0x18, count at +0x20, adds U_ARR_DATA (0x20)
     * to skip the IL2CPP array header. */
    int count = 0;
    uint64_t entries = 0;
    int stride = 0;
    if (!u_dict(roulette_dict, &count, &entries, &stride) || count <= 0 || count > 64)
        return 0;
    if (stride != 0x18) return 0;  /* Entry<int,RouletteModel> must be 0x18 */

    out->roulette_count = count;
    out->valid = 1;

    /* Step 3: Find the first live RouletteModel entry (hash >= 0, valid ptr). */
    uint64_t roulette_model = 0;
    for (int i = 0; i < count && i < 64; i++) {
        uint8_t entry[0x18];
        if (!rr_read(entries + (uint64_t)i * 0x18, entry, sizeof(entry))) continue;
        int32_t hash;
        uint64_t val;
        memcpy(&hash, entry + 0x00, 4);
        memcpy(&val,  entry + 0x10, 8);
        if (hash < 0) continue;   /* tombstone / unused */
        if (PL(val)) { roulette_model = val; break; }
    }

    if (!roulette_model) return 1;  /* valid dict but no live table yet */

    /* Step 4: WinningNumber — PrimitiveModel<int>* at RouletteModel+0x30. */
    {
        uint64_t win_prim = rr_u64(roulette_model + RM_WIN_NUMBER_OFF);
        int32_t win = -1;
        if (read_prim_int(win_prim, &win))
            out->winning_number = win;
    }

    /* Step 5: Phase — PrimitiveModel<RoulettePhaseDescription>* at RouletteModel+0x20.
     * The value is a RoulettePhaseDescription* (reference type).
     * RoulettePhaseDescription is an EnumItem; its Index field is at obj+0x28. */
    {
        uint64_t phase_prim = rr_u64(roulette_model + RM_PHASE_OFF);
        uint64_t phase_desc = read_prim_ref(phase_prim);
        if (PL(phase_desc)) {
            int32_t idx = rr_i32(phase_desc + ENUM_INDEX_OFF);
            if (rr_ok() && idx >= 0 && idx <= 10)
                out->phase_index = idx;
        }
    }

    /* Step 6: PhaseEndTs — PrimitiveModel<long>* at RouletteModel+0x28. */
    {
        uint64_t ts_prim = rr_u64(roulette_model + RM_PHASE_END_OFF);
        int64_t ts = 0;
        if (read_prim_long(ts_prim, &ts))
            out->phase_end_ms = ts;
    }

    return 1;
}
