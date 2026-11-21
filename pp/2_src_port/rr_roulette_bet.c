/* rr_roulette_bet.c - Roulette auto-bet implementation for ROB RUN.
 *
 * Strategy
 * --------
 * This is an external cheat with no injected DLL.  To trigger a real bet we
 * write a small x64 shellcode stub into the game process (via the driver's
 * WM_IO_ALLOC + IOCTL_WRITE), then call it with CreateRemoteThread.  The stub
 * calls RouletteModel.AddBet(this, betDesc, charId, chipDesc, amount) which is
 * the game's own managed-to-native bridge so the bet is handled identically to
 * a UI click.
 *
 * Obtaining description pointers
 * --------------------------------
 * RouletteBetDescriptions and RouletteChipDescriptions are static IL2CPP
 * classes.  Their klass pointers are obtained by reading the class field of a
 * live RouletteBetDescription or RouletteChipDescription instance that the
 * roulette model already holds.  Once we have the klass we call
 * u_static_fields() (klass + U_CLASS_STATIC = klass + 0xB8) to reach the
 * static-fields blob, then index into it with the offsets from dump.cs.
 *
 * Shellcode ABI (Microsoft x64 calling convention)
 * -------------------------------------------------
 * AddBet(RouletteModel* this, RouletteBetDescription* bet,
 *        int characterId, RouletteChipDescription* chip, int amount)
 *
 * RCX = this  (roulette model pointer)
 * RDX = bet   (RouletteBetDescription*)
 * R8  = characterId (int, zero-extended)
 * R9  = chip  (RouletteChipDescription*)
 * [RSP+0x28] = amount (int, 5th arg by value on stack shadow space + 8)
 *
 * The stub is called via CreateRemoteThread with the PARAM_BLOCK* as lpParam.
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>

#include "rr_roulette_bet.h"
#include "rr_roulette.h"
#include "rr_mem.h"
#include "rr_unity.h"
#include "rr_game.h"
#include "robrun_offsets.h"

/* ---------------------------------------------------------------------------
 * Offsets sourced from the generated header, which is regenerated from the
 * current dump.cs. The local names stay so the call sites read the same; the
 * values are not duplicated, so a re-dump only needs robrun_offsets.h
 * refreshed (dump 2026-11-21: AddBet RVA moved 0x489C8A0 -> 0x48E4BB0).
 * --------------------------------------------------------------------------*/

/* WorldEntitiesModel._rouletteModels */
#define WEM_ROULETTE_DICT   RR_OFF_WEM_ROULETTES

/* RouletteModel fields (from rr_roulette.c). */
#define RM_PHASE_OFF        RR_OFF_RM_PHASE
#define RM_PHASE_END_OFF    RR_OFF_RM_PHASE_END
#define RM_WIN_NUMBER_OFF   RR_OFF_RM_WIN_NUMBER
#define RM_BETS_BY_CHAR     RR_OFF_RM_BETS_BY_CHAR

/* AddBet RVA inside GameAssembly.dll */
#define ADD_BET_RVA         RR_RVA_ADDBET

/* IL2CPP object header size. */
#define OBJ_HDR             0x10u

/* PrimitiveModel<T> two-hop layout (same as rr_roulette.c). */
#define PM_DATA_OFF         (OBJ_HDR + 0x00u)  /* 0x10 */
#define PD_VALUE_OFF        0x18u

/* EnumItem.<Index>k__BackingField: field offset 0x18 is already the memory
 * offset (dump.cs offsets include the 0x10 object header). */
#define ENUM_INDEX_OFF      0x18u

/* RouletteBetDescriptions static-field offsets. */
#define RBDS_STRAIGHT0      RR_SF_BET_STRAIGHT0   /* Straight[N] = 0x40 + N*8 */
#define RBDS_DOZEN_1_12     RR_SF_BET_DOZEN_1_12
#define RBDS_DOZEN_13_24    RR_SF_BET_DOZEN_13_24
#define RBDS_DOZEN_25_36    RR_SF_BET_DOZEN_25_36
#define RBDS_RED            RR_SF_BET_RED
#define RBDS_BLACK          RR_SF_BET_BLACK

/* RouletteChipDescriptions static-field offsets. */
#define RCDS_CHIP1K         RR_SF_CHIP_1K
#define RCDS_CHIP5K         RR_SF_CHIP_5K
#define RCDS_CHIP25K        RR_SF_CHIP_25K
#define RCDS_CHIP50K        RR_SF_CHIP_50K
#define RCDS_CHIP100K       RR_SF_CHIP_100K

/* Phase indices from RoulettePhaseDescriptions. */
#define PHASE_BETS          0

/* ---------------------------------------------------------------------------
 * Cached pointers — invalidated on game reattach.
 * --------------------------------------------------------------------------*/

static uint64_t g_roulette_model  = 0;   /* first live RouletteModel*     */
static uint64_t g_bet_sf          = 0;   /* RouletteBetDescriptions sf    */
static uint64_t g_chip_sf         = 0;   /* RouletteChipDescriptions sf   */
static uint64_t g_addbet_va       = 0;   /* GameAssembly + ADD_BET_RVA    */
static uint64_t g_prep_chip       = 0;   /* resolved chip desc for sniper */

void rr_roulette_bet_reset_cache(void) {
    g_roulette_model = 0;
    g_bet_sf         = 0;
    g_chip_sf        = 0;
    g_addbet_va      = 0;
    g_prep_chip      = 0;
}

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------*/

static int pl(uint64_t p) {
    return p >= 0x10000ULL && p < 0x00007FFFFFFFFFFFULL;
}

/* Read the first live RouletteModel* from WorldEntitiesModel._rouletteModels. */
static uint64_t find_roulette_model(uint64_t world_ent) {
    if (!pl(world_ent)) return 0;
    uint64_t dict = rr_u64(world_ent + WEM_ROULETTE_DICT);
    if (!pl(dict)) return 0;

    int count = 0;
    uint64_t entries = 0;
    int stride = 0;
    if (!u_dict(dict, &count, &entries, &stride) || count <= 0 || stride != 0x18)
        return 0;

    for (int i = 0; i < count && i < 64; i++) {
        uint8_t entry[0x18];
        if (!rr_read(entries + (uint64_t)i * 0x18, entry, sizeof(entry))) continue;
        int32_t hash;
        uint64_t val;
        memcpy(&hash, entry + 0x00, 4);
        memcpy(&val,  entry + 0x10, 8);
        if (hash < 0) continue;
        if (pl(val)) return val;
    }
    return 0;
}

/* Get static-fields blobs by reading the klass from a live instance stored in
 * the roulette model's existing bet dictionary.  If we cannot find a live bet
 * description we fall back to scanning through the roulette model's Phase
 * PrimitiveModel, whose klass chain leads us to the assembly's type registry.
 *
 * Fallback: get a live RouletteBetDescription from the BetsByCharacter dict.
 * If the dict is empty (nobody has bet yet) we cannot discover the klass this
 * way — in that case we return 0 and callers must retry later.
 */
static uint64_t discover_bet_sf(uint64_t roulette_model) {
    if (!pl(roulette_model)) return 0;

    /* _betsByCharacter at RouletteModel+0x18 →
     *   Dictionary<int, HashSet<RouletteBetDescription>>
     * We need a RouletteBetDescription* to get its klass.
     * Walk: dict entries → HashSet<RouletteBetDescription> → its backing
     * array → first element. */
    uint64_t bbc = rr_u64(roulette_model + RM_BETS_BY_CHAR);
    if (!pl(bbc)) return 0;

    int cnt = 0; uint64_t ents = 0; int str = 0;
    if (!u_dict(bbc, &cnt, &ents, &str) || cnt <= 0) return 0;

    for (int i = 0; i < cnt && i < 32; i++) {
        uint8_t entry[0x18];
        if (!rr_read(ents + (uint64_t)i * (uint64_t)str, entry, sizeof(entry))) continue;
        int32_t hash; memcpy(&hash, entry, 4);
        if (hash < 0) continue;
        /* Value is a HashSet<RouletteBetDescription>* at entry+0x10. */
        uint64_t hset; memcpy(&hset, entry + 0x10, 8);
        if (!pl(hset)) continue;
        /* HashSet stores its backing array at field 0x10 (after obj header). */
        uint64_t backing_arr = rr_u64(hset + OBJ_HDR);
        if (!pl(backing_arr)) continue;
        /* Array elements start at U_ARR_DATA (0x20), each is a pointer (8 B). */
        int alen = 0; uint64_t adat = 0;
        alen = u_array(backing_arr, &adat);
        if (alen <= 0 || !pl(adat)) continue;
        uint64_t bet_desc = rr_u64(adat);
        if (!pl(bet_desc)) continue;
        /* Got a live RouletteBetDescription instance — its klass is at obj+0. */
        uint64_t klass = rr_u64(bet_desc);
        if (!pl(klass)) continue;
        uint64_t sf = u_static_fields(klass);
        if (pl(sf)) return sf;
    }
    return 0;
}

/* Discover chip static fields by reading a klass from an existing
 * RouletteChipDescription.  We obtain one from the roulette model's
 * _data._betsByBetDescription dictionary.  If unavailable we return 0. */
static uint64_t discover_chip_sf(uint64_t roulette_model) {
    if (!pl(roulette_model)) return 0;

    /* RouletteData at RouletteModel+0x10. */
    uint64_t rdata = rr_u64(roulette_model + OBJ_HDR);
    if (!pl(rdata)) return 0;

    /* RouletteBetData fields: DictionaryData<int,LongData> —
     * it has _dictionary at field 0x0 → obj+0x10. */
    /* Actually RouletteData._betsByBetDescription is not straightforward.
     * Alternative: get klass from a live instance via _betsByCharacter data.
     * We already have bet_sf pointing to RouletteBetDescriptions static fields.
     * RouletteBetDescriptions and RouletteChipDescriptions are both static
     * classes in the same assembly; their klasses are adjacent in the static
     * registration.  Read Chip1k from RouletteChipDescriptions static fields
     * by finding the klass of a chip from the roulette model's
     * _selectedChipDescription (if any) or from an inventory slot.
     *
     * Simplest fallback: scan the existing static objects we know about.
     * We get a RouletteChipDescription pointer by reading the
     * PrimitiveModel<RouletteChipDescription> at RouletteModel+some_offset
     * (not in dump).  Skip for now — use bet_sf + known chip offset alignment.
     *
     * REAL approach: once g_bet_sf is known, read the value at
     * g_bet_sf + RBDS_STRAIGHT0 to get Straight0 (a RouletteBetDescription*).
     * That's already a known class.  RouletteChipDescriptions TypeInfo is at
     * a fixed offset from the game module.  We can find it by scanning the
     * static-fields region for a pointer whose object's class-name string
     * matches "RouletteChipDescription".
     *
     * For now: scan the static-fields blob itself for pointers to objects
     * whose u_klass class-name == "RouletteChipDescription". */

    /* Try reading Chip1k/5k/25k by scanning the region around g_bet_sf. */
    if (!pl(g_bet_sf)) return 0;

    /* The RouletteChipDescriptions static-fields blob is a separate allocation.
     * We locate it by finding a live RouletteChipDescription via the game's
     * inventory model.  As a pragmatic alternative: scan 0x10000 bytes starting
     * at a likely aligned address before g_bet_sf (they tend to be allocated
     * close together by the IL2CPP runtime) looking for an object whose klass
     * reports "RouletteChipDescription". */

    /* Practical: read the pointer at g_bet_sf + RBDS_STRAIGHT0 (Straight0).
     * From Straight0's klass, we know its TypeInfo.  The chip klass lives in
     * the same Il2CppCodeRegistration table.  Walk ±4096 TypeInfo entries. */
    uint64_t s0 = rr_u64(g_bet_sf + RBDS_STRAIGHT0);
    if (!pl(s0)) return 0;
    uint64_t bet_klass = rr_u64(s0);  /* klass of Straight0 == RouletteBetDescription klass */
    if (!pl(bet_klass)) return 0;

    /* Chip descriptions live in the same type namespace.  Their klass lives
     * within ±32 TypeInfo slots (each is 8 bytes in the type array).
     * But TypeInfo entries are not necessarily contiguous — scan by name. */
    char name[64];
    for (int delta = -256; delta <= 256; delta++) {
        uint64_t candidate_klass = bet_klass + (int64_t)delta * 0x100;
        if (!pl(candidate_klass)) continue;
        uint64_t sf_candidate = rr_u64(candidate_klass + 0xB8u);
        if (!pl(sf_candidate)) continue;
        /* Read what should be Chip1k at offset 0x08. */
        uint64_t chip1k_cand = rr_u64(sf_candidate + 0x08u);
        if (!pl(chip1k_cand)) continue;
        /* Check its klass name. */
        uint64_t ck = rr_u64(chip1k_cand);
        if (!pl(ck)) continue;
        if (u_class_name(ck, name, sizeof(name)) && strcmp(name, "RouletteChipDescription") == 0)
            return sf_candidate;
    }
    return 0;
}

/* ---------------------------------------------------------------------------
 * Shellcode for x64: calls AddBet then returns.
 *
 * Calling convention: stub is invoked as a thread function:
 *   DWORD WINAPI stub(LPVOID param)  → RCX = &PARAM_BLOCK
 *
 * Layout of the parameter block written into game memory:
 *   [+0x00] uint64_t roulette_model
 *   [+0x08] uint64_t bet_description
 *   [+0x10] int32_t  character_id
 *   [+0x14] int32_t  amount
 *   [+0x18] uint64_t chip_description
 *   [+0x20] uint64_t add_bet_fn  (absolute VA = image_base + RVA)
 *
 * x64 shellcode (position-independent, reads params from [rcx+offset]):
 * --------------------------------------------------------------------------*/
#pragma pack(push,1)
typedef struct {
    uint64_t roulette_model;
    uint64_t bet_description;
    int32_t  character_id;
    int32_t  amount;
    uint64_t chip_description;
    uint64_t add_bet_fn;
} PARAM_BLOCK;
#pragma pack(pop)

/* Pre-assembled shellcode (48 bytes):
 *
 *   ; RCX = PARAM_BLOCK*
 *   push  rbp
 *   sub   rsp, 0x40           ; shadow + 5th-arg slot
 *   mov   rbp, rcx            ; save param ptr
 *   mov   rcx, [rbp+0x00]    ; arg1 = roulette_model
 *   mov   rdx, [rbp+0x08]    ; arg2 = bet_description
 *   mov   r8d, [rbp+0x10]    ; arg3 = character_id (int)
 *   mov   r9,  [rbp+0x18]    ; arg4 = chip_description
 *   mov   eax, [rbp+0x14]    ; arg5 = amount (int)
 *   mov   [rsp+0x20], rax    ; 5th arg on stack (home space above shadow)
 *   call  [rbp+0x20]          ; call add_bet_fn
 *   xor   eax, eax
 *   add   rsp, 0x40
 *   pop   rbp
 *   ret
 */
static const uint8_t k_shellcode[] = {
    0x55,                                           /* push  rbp               */
    0x48, 0x83, 0xEC, 0x40,                         /* sub   rsp, 0x40         */
    0x48, 0x89, 0xCD,                               /* mov   rbp, rcx          */
    0x48, 0x8B, 0x4D, 0x00,                         /* mov   rcx, [rbp+0x00]   */
    0x48, 0x8B, 0x55, 0x08,                         /* mov   rdx, [rbp+0x08]   */
    0x44, 0x8B, 0x45, 0x10,                         /* mov   r8d, [rbp+0x10]   */
    0x4C, 0x8B, 0x4D, 0x18,                         /* mov   r9,  [rbp+0x18]   */
    0x8B, 0x45, 0x14,                               /* mov   eax, [rbp+0x14]   */
    0x48, 0x89, 0x44, 0x24, 0x20,                   /* mov   [rsp+0x20], rax   */
    0xFF, 0x55, 0x20,                               /* call  [rbp+0x20]        */
    0x31, 0xC0,                                     /* xor   eax, eax          */
    0x48, 0x83, 0xC4, 0x40,                         /* add   rsp, 0x40         */
    0x5D,                                           /* pop   rbp               */
    0xC3                                            /* ret                     */
};

#define SHELLCODE_SIZE sizeof(k_shellcode)
#define PARAM_SIZE     sizeof(PARAM_BLOCK)

/* Total remote allocation: shellcode + param block (8-byte aligned). */
#define ALLOC_SIZE   (SHELLCODE_SIZE + 8 + PARAM_SIZE)

/* ---------------------------------------------------------------------------
 * rr_roulette_place_bet()
 * --------------------------------------------------------------------------*/

int rr_roulette_place_bet(uint64_t world_ent, int winning,
                          const RR_BET_CONFIG *cfg, int32_t local_char_id) {
    if (!cfg || !cfg->enabled) return 0;
    if (winning < 0 || winning > 36) return 0;
    if (local_char_id == 0) return 0;

    /* ---- 1. Find the roulette model ---- */
    if (!pl(g_roulette_model))
        g_roulette_model = find_roulette_model(world_ent);
    if (!pl(g_roulette_model)) return 0;

    /* ---- 2. Verify we're in the Bets phase ---- */
    {
        uint64_t phase_prim = rr_u64(g_roulette_model + RM_PHASE_OFF);
        if (pl(phase_prim)) {
            uint64_t data_ptr = rr_u64(phase_prim + PM_DATA_OFF);
            if (pl(data_ptr)) {
                uint64_t phase_desc = rr_u64(data_ptr + PD_VALUE_OFF);
                if (pl(phase_desc)) {
                    int32_t idx = rr_i32(phase_desc + ENUM_INDEX_OFF);
                    /* Only place bet during Bets phase (index 0).
                     * Also allow unknown (-1) in case phase was just set. */
                    if (rr_ok() && idx != PHASE_BETS && idx != -1)
                        return 0;
                }
            }
        }
    }

    /* ---- 3. Discover static-fields blobs (lazy, cached) ---- */
    if (!pl(g_bet_sf))
        g_bet_sf = discover_bet_sf(g_roulette_model);
    if (!pl(g_bet_sf)) return 0;

    if (!pl(g_chip_sf))
        g_chip_sf = discover_chip_sf(g_roulette_model);
    if (!pl(g_chip_sf)) return 0;

    /* ---- 4. Resolve the bet description ---- */
    uint64_t bet_desc = 0;
    switch (cfg->mode) {
        case RR_BET_NUMBER:
            if (winning < 0 || winning > 36) return 0;
            bet_desc = rr_u64(g_bet_sf + RBDS_STRAIGHT0 + (uint64_t)winning * 8u);
            break;
        case RR_BET_COLOR:
            if (winning == 0) return 0;   /* green — no color bet */
            {
                static const int red_nums[] = {
                    1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
                };
                int is_red = 0;
                for (int i = 0; i < (int)(sizeof(red_nums)/sizeof(red_nums[0])); i++)
                    if (red_nums[i] == winning) { is_red = 1; break; }
                bet_desc = rr_u64(g_bet_sf + (is_red ? RBDS_RED : RBDS_BLACK));
            }
            break;
        case RR_BET_DOZEN:
            if (winning == 0) return 0;
            if      (winning <= 12) bet_desc = rr_u64(g_bet_sf + RBDS_DOZEN_1_12);
            else if (winning <= 24) bet_desc = rr_u64(g_bet_sf + RBDS_DOZEN_13_24);
            else                    bet_desc = rr_u64(g_bet_sf + RBDS_DOZEN_25_36);
            break;
        default:
            return 0;
    }
    if (!pl(bet_desc)) return 0;

    /* ---- 5. Resolve chip description ---- */
    static const uint32_t chip_offsets[] = {
        RCDS_CHIP1K, RCDS_CHIP5K, RCDS_CHIP25K, RCDS_CHIP50K, RCDS_CHIP100K
    };
    int ci = cfg->chip_index;
    if (ci < 0 || ci > 4) ci = 0;
    uint64_t chip_desc = rr_u64(g_chip_sf + chip_offsets[ci]);
    if (!pl(chip_desc)) return 0;

    /* ---- 6. Get the game module base ---- */
    uint64_t ga_base = 0;
    uint32_t ga_size = 0;
    if (!rr_module("GameAssembly.dll", &ga_base, &ga_size) || !ga_base) return 0;
    uint64_t add_bet_va = ga_base + ADD_BET_RVA;

    /* ---- 7. Determine repeat count ---- */
    int repeat = cfg->repeat;
    if (repeat < 1)  repeat = 1;
    if (repeat > 20) repeat = 20;

    /* ---- 8. Build param block ---- */
    PARAM_BLOCK pb;
    pb.roulette_model  = g_roulette_model;
    pb.bet_description = bet_desc;
    pb.character_id    = local_char_id;
    pb.amount          = repeat;        /* pass repeat directly — MaxAmountPerChip = 4095 */
    pb.chip_description = chip_desc;
    pb.add_bet_fn      = add_bet_va;

    /* ---- 9. Allocate remote memory and write shellcode + params ---- */
    uint64_t remote_mem = 0;
    /* PAGE_EXECUTE_READWRITE = 0x40 */
    if (!rr_drv_alloc_remote(g_rr_pid, ALLOC_SIZE, 0x40, &remote_mem) || !remote_mem)
        return 0;

    /* Write shellcode first. */
    if (!rr_write(remote_mem, k_shellcode, SHELLCODE_SIZE)) return 0;

    /* Param block follows, 8-byte aligned. */
    uint64_t param_addr = (remote_mem + SHELLCODE_SIZE + 7) & ~(uint64_t)7;
    if (!rr_write(param_addr, &pb, sizeof(pb))) return 0;

    /* ---- 10. CreateRemoteThread → runs the stub with param_addr as lpParam ---- */
    HANDLE hproc = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                               PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE,
                               FALSE, (DWORD)g_rr_pid);
    if (!hproc) return 0;

    HANDLE hthread = CreateRemoteThread(
        hproc, NULL, 0,
        (LPTHREAD_START_ROUTINE)(uintptr_t)remote_mem,
        (LPVOID)(uintptr_t)param_addr,
        0, NULL);

    int placed = 0;
    if (hthread) {
        /* Wait up to 1 s for the bet to execute. */
        WaitForSingleObject(hthread, 1000);
        CloseHandle(hthread);
        placed = 1;
    }
    CloseHandle(hproc);

    /* NOTE: We intentionally do NOT free the remote memory here because
     * the thread might still be in a cleanup epilogue.  The game process
     * is long-lived and the small leaked allocation is acceptable. */
    return placed;
}

/* ---------------------------------------------------------------------------
 * Discovery helpers shared with rr_roulette_sniper.c.
 *
 * place_bet() above rebuilds all of this on every call because it has to run
 * standalone.  The sniper instead pays for it once at arm time and then only
 * touches cached pointers, so these entry points expose the individual steps.
 * --------------------------------------------------------------------------*/

uint64_t rr_roulette_model_ptr(void) { return g_roulette_model; }
uint64_t rr_roulette_bet_sf_ptr(void) { return g_bet_sf; }
uint64_t rr_roulette_addbet_va(void) { return g_addbet_va; }
uint64_t rr_roulette_prepared_chip(void) { return g_prep_chip; }

uint64_t rr_roulette_chip_desc(int chip_index) {
    static const uint32_t chip_offsets[] = {
        RCDS_CHIP1K, RCDS_CHIP5K, RCDS_CHIP25K, RCDS_CHIP50K, RCDS_CHIP100K
    };

    if (!pl(g_chip_sf)) return 0;

    int ci = chip_index;
    if (ci < 0 || ci > 4) ci = 0;
    return rr_u64(g_chip_sf + chip_offsets[ci]);
}

uint64_t rr_roulette_bet_desc(int winning, int mode) {
    if (!pl(g_bet_sf)) return 0;

    switch (mode) {
    case RR_BET_NUMBER:
        if (winning < 0 || winning > 36) return 0;
        return rr_u64(g_bet_sf + RBDS_STRAIGHT0 + (uint64_t)winning * 8u);

    case RR_BET_COLOR: {
        static const int red_nums[] = {
            1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
        };
        int is_red = 0;

        if (winning <= 0 || winning > 36) return 0;   /* 0 is green — no colour bet */
        for (int i = 0; i < (int)(sizeof(red_nums)/sizeof(red_nums[0])); i++)
            if (red_nums[i] == winning) { is_red = 1; break; }
        return rr_u64(g_bet_sf + (is_red ? RBDS_RED : RBDS_BLACK));
    }

    case RR_BET_DOZEN:
        if (winning <= 0 || winning > 36) return 0;
        if      (winning <= 12) return rr_u64(g_bet_sf + RBDS_DOZEN_1_12);
        else if (winning <= 24) return rr_u64(g_bet_sf + RBDS_DOZEN_13_24);
        else                    return rr_u64(g_bet_sf + RBDS_DOZEN_25_36);

    default:
        return 0;
    }
}

int rr_roulette_bet_prepare(uint64_t world_ent, const RR_BET_CONFIG *cfg,
                            int32_t local_char_id) {
    if (!cfg || local_char_id == 0) return 0;

    /* Re-resolve the model every time: the player may have walked to a
     * different table, and a stale RouletteModel* would silently bet into a
     * dead entity.  A dict walk is a handful of reads and only happens once
     * per Bets phase. */
    g_roulette_model = find_roulette_model(world_ent);
    if (!pl(g_roulette_model)) return 0;

    if (!pl(g_bet_sf))  g_bet_sf  = discover_bet_sf(g_roulette_model);
    if (!pl(g_bet_sf))  return 0;

    if (!pl(g_chip_sf)) g_chip_sf = discover_chip_sf(g_roulette_model);
    if (!pl(g_chip_sf)) return 0;

    g_prep_chip = rr_roulette_chip_desc(cfg->chip_index);
    if (!pl(g_prep_chip)) return 0;

    if (!pl(g_addbet_va)) {
        uint64_t base = 0;
        uint32_t size = 0;

        if (!rr_module("GameAssembly.dll", &base, &size) || !base) return 0;
        g_addbet_va = base + ADD_BET_RVA;
    }

    return pl(g_addbet_va) ? 1 : 0;
}
