/* rr_roulette.c - Roulette model reader for ROB RUN.
 *
 * Reads the Dictionary<int, RouletteModel> at WorldEntitiesModel + 0x478.
 * C# Dictionary layout (il2cpp, this runtime):
 *   +0x10  entries array pointer  (game_dict_offset = 0x10)
 *   +0x18  _count  (int32)
 *   Each entry stride 0x18:  hashCode +0x00, key(int) +0x08, value(ptr) +0x10
 *
 * RouletteModel object layout (all offsets are field offsets on the managed heap;
 * the il2cpp object header is 0x10 bytes, so field[0x20] is at obj+0x10+0x20):
 *   <Phase>k__BackingField       field 0x20  → IPrimitiveModel<RoulettePhaseDescription>*
 *   <PhaseEndTs>k__BackingField  field 0x28  → IPrimitiveModel<long>*
 *   <WinningNumber>k__BackingField field 0x30 → IPrimitiveModel<int>*
 *
 * IPrimitiveModel<T> (replicated variants): value at object +0x18.
 * RoulettePhaseDescription.Index (EnumItem.Index): int at object +0x28
 *   (il2cpp header 0x10 + Identified.id-string ptr 0x08 + EnumItem.Index field 0x18 → 0x10+0x18=0x28).
 */
#include "rr_roulette.h"
#include "rr_mem.h"

/* Offset of the backing field *within* the RouletteModel object body.
 * The actual memory address is: roulette_obj_ptr + field_offset
 * (il2cpp object header is already baked into these offsets as declared
 * in the dump, so we use them directly as struct member offsets from the
 * start of the managed object — matching how the game's own code addresses
 * them, with the header at [0..0x10) and fields starting at 0x10).        */
#define RM_PHASE_OFF        0x20u   /* IPrimitiveModel<RoulettePhaseDescription>* */
#define RM_PHASE_END_OFF    0x28u   /* IPrimitiveModel<long>*                     */
#define RM_WIN_NUMBER_OFF   0x30u   /* IPrimitiveModel<int>*                      */

/* Value inside a replicated IPrimitiveModel<T> object (matches RR_OFF_PRIM_VALUE). */
#define PRIM_VALUE_OFF  0x18u

/* EnumItem.Index field offset within the EnumItem object.
 * Identified has no instance fields; MyEnumItem inherits EnumItem;
 * EnumItem.<Index>k__BackingField is at field offset 0x18.
 * With il2cpp header: enum_item_ptr + 0x10 + 0x18 = enum_item_ptr + 0x28. */
#define ENUM_INDEX_OFF  0x28u

/* il2cpp minimum pointer validation. */
#define PL(p) ((p) > 0x10000ULL && (p) < 0x7FFFFFFFFFFFULL)

/* WorldEntitiesModel._rouletteModels: Dictionary<int, RouletteModel> */
#define WEM_ROULETTE_DICT_OFF  0x478u

/* C# Dictionary inner layout — matches rr_unity.h U_DICT_* constants.
 * The entries field holds a pointer to an IL2CPP array object; the actual
 * entry data starts at array+0x20 (U_ARR_DATA), skipping the array header. */
#define DICT_ENTRIES_OFF  0x18u   /* ptr to Entry[] array object (U_DICT_ENTRIES)     */
#define DICT_COUNT_OFF    0x20u   /* int _count                   (U_DICT_COUNT)       */
#define DICT_ARR_DATA     0x20u   /* offset past IL2CPP array header (U_ARR_DATA)      */
#define DICT_ENTRY_STRIDE 0x18u   /* sizeof(Entry<int, RouletteModel>)                 */
#define DICT_ENTRY_KEY    0x08u   /* int key   within entry                            */
#define DICT_ENTRY_VAL    0x10u   /* TValue    within entry (pointer for a class)      */

int rr_roulette_read(uint64_t world_ent, RR_ROULETTE *out)
{
    if (!out) return 0;
    out->valid          = 0;
    out->winning_number = -1;
    out->phase_index    = -1;
    out->phase_end_ms   = 0;
    out->roulette_count = 0;

    if (!PL(world_ent)) return 0;

    /* Step 1: Read the Dictionary<int, RouletteModel> pointer. */
    uint64_t roulette_dict = rr_u64(world_ent + WEM_ROULETTE_DICT_OFF);
    if (!PL(roulette_dict)) return 0;

    /* Step 2: Read the inner entries array pointer and count. */
    uint64_t arr = rr_u64(roulette_dict + DICT_ENTRIES_OFF);
    if (!PL(arr)) return 0;
    uint64_t entries = arr + DICT_ARR_DATA;   /* skip IL2CPP array header */

    int32_t count = rr_i32(roulette_dict + DICT_COUNT_OFF);
    if (count <= 0 || count > 64) return 0;   /* sanity: at most a handful of roulette tables */

    out->roulette_count = count;
    out->valid = 1;

    /* Step 3: Walk entries, pick the first valid RouletteModel. */
    uint64_t roulette_model = 0;
    for (int i = 0; i < count && i < 64; i++) {
        uint64_t entry_base = entries + (uint64_t)i * DICT_ENTRY_STRIDE;
        /* hashCode at +0x00: skip tombstones (hashCode < 0). */
        int32_t hash = rr_i32(entry_base);
        if (hash < 0) continue;
        uint64_t val = rr_u64(entry_base + DICT_ENTRY_VAL);
        if (PL(val)) {
            roulette_model = val;
            break;
        }
    }

    if (!PL(roulette_model)) return 1;  /* valid dict, no live entry yet */

    /* Step 4: Read WinningNumber.
     *   RouletteModel.<WinningNumber>k__BackingField = field 0x30
     *   The field holds an IPrimitiveModel<int>* (a reference-type object ptr).
     *   The replicated primitive stores the int value at object +0x18.
     */
    uint64_t win_prim = rr_u64(roulette_model + RM_WIN_NUMBER_OFF);
    if (PL(win_prim)) {
        int32_t win = rr_i32(win_prim + PRIM_VALUE_OFF);
        if (rr_ok()) out->winning_number = win;
    }

    /* Step 5: Read Phase.
     *   RouletteModel.<Phase>k__BackingField = field 0x20
     *   IPrimitiveModel<RoulettePhaseDescription>*
     *   Value at prim+0x18 is a RoulettePhaseDescription* (reference).
     *   RoulettePhaseDescription.Index (EnumItem) = object +0x28.
     */
    uint64_t phase_prim = rr_u64(roulette_model + RM_PHASE_OFF);
    if (PL(phase_prim)) {
        uint64_t phase_desc = rr_u64(phase_prim + PRIM_VALUE_OFF);
        if (PL(phase_desc)) {
            int32_t idx = rr_i32(phase_desc + ENUM_INDEX_OFF);
            if (rr_ok() && idx >= 0 && idx <= 10) out->phase_index = idx;
        }
    }

    /* Step 6: Read PhaseEndTs.
     *   RouletteModel.<PhaseEndTs>k__BackingField = field 0x28
     *   IPrimitiveModel<long>* → value at prim+0x18 (long, 8 bytes).
     */
    uint64_t ts_prim = rr_u64(roulette_model + RM_PHASE_END_OFF);
    if (PL(ts_prim)) {
        int64_t ts = 0;
        if (rr_read(ts_prim + PRIM_VALUE_OFF, &ts, sizeof(ts))) {
            out->phase_end_ms = ts;
        }
    }

    return 1;
}
