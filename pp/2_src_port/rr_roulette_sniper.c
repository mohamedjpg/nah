/* rr_roulette_sniper.c - Pre-armed low-latency bet trigger for ROB RUN.
 *
 * Problem
 * -------
 * rr_roulette_place_bet() allocates a page, writes shellcode, opens the process
 * and calls CreateRemoteThread on every bet.  That is 5-30 ms, and the first
 * call of a session also pays for discover_chip_sf()'s IL2CPP class scan.
 * When the server writes WinningNumber only a handful of milliseconds before it
 * stops accepting bets, a per-bet thread costs the whole window.
 *
 * Solution
 * --------
 * Pay for everything once:
 *
 *   - one RWX page in the game holds the parameter block and a poll stub,
 *   - one thread started at arm time spins on a "go" flag,
 *   - the bet-description pointers for every pocket are cached host-side,
 *   - fire() is therefore exactly two driver writes and nothing else.
 *
 * Remote layout (one 0x100 page):
 *
 *   0x00  SNIPER_PARAM  (0x40 bytes)
 *   0x40  stub code     (0x5A bytes)
 *
 * SNIPER_PARAM:
 *   +0x00 int64  go           0 = idle, 1 = fire, -1 = exit
 *   +0x08 int64  done         stub sets 1 after AddBet returns
 *   +0x10 u64    roulette_model
 *   +0x18 u64    bet_description        <- rewritten per fire
 *   +0x20 i32    character_id            <- rewritten per fire (blocked in)
 *   +0x24 i32    amount                  <- rewritten per fire (blocked in)
 *   +0x28 u64    chip_description
 *   +0x30 u64    add_bet_fn              (absolute VA)
 *   +0x38 u64    yield_fn                (SwitchToThread, absolute VA)
 *
 * Why the kernel32 VA is valid in another process: system DLLs are mapped from
 * shared image sections, so their base address is randomised once per boot and
 * is identical in every process on the machine.  Resolving SwitchToThread in
 * our own process therefore yields a usable pointer in the game process.
 *
 * Stub ABI (Microsoft x64) — AddBet(this, bet, charId, chip, amount):
 *   rcx = this, rdx = bet, r8d = charId, r9 = chip, [rsp+0x20] = amount
 *
 * The stub loops: idle-yield / fire / exit, driven entirely by the go flag, so
 * the host never has to create a thread on the hot path.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>

#include "rr_roulette_sniper.h"
#include "rr_roulette_bet.h"
#include "rr_roulette.h"
#include "rr_mem.h"

/* ---------------------------------------------------------------------------
 * Parameter block layout — must match the stub's displacements.
 * --------------------------------------------------------------------------*/
#define SNIP_GO        0x00u
#define SNIP_DONE      0x08u
#define SNIP_MODEL     0x10u
#define SNIP_BET       0x18u
#define SNIP_CHAR      0x20u
#define SNIP_AMOUNT    0x24u
#define SNIP_CHIP      0x28u
#define SNIP_ADDBET    0x30u
#define SNIP_YIELD     0x38u

#define PARAM_SIZE     0x40u
#define STUB_OFF       PARAM_SIZE
#define PAGE_SIZE_     0x100u

/* First 0x20 bytes of the block are go/done/model/bet; the per-fire rewrite
 * covers SNIP_BET .. SNIP_AMOUNT inclusive, i.e. 0x18..0x27 = 0x10 bytes. */
#define FIRE_BLK_OFF   SNIP_BET
#define FIRE_BLK_LEN   0x10u

#define PL(p) ((p) > 0x10000ULL && (p) < 0x7FFFFFFFFFFFULL)

/* ---------------------------------------------------------------------------
 * Stub.  Hand assembled; offsets are load-bearing — see the header comment.
 *
 *   0x00  48 8B 41 00              mov  rax, [rcx+0x00]        ; go
 *   0x04  48 85 C0                 test rax, rax
 *   0x07  7F 11                    jg   fire                    (-> 0x1A)
 *   0x09  7C 4C                    jl   exit                    (-> 0x57)
 *   0x0B  51                       push rcx
 *   0x0C  48 83 EC 20              sub  rsp, 0x20
 *   0x10  FF 51 38                 call qword ptr [rcx+0x38]    ; SwitchToThread
 *   0x13  48 83 C4 20              add  rsp, 0x20
 *   0x17  59                       pop  rcx
 *   0x18  EB E6                    jmp  spin                    (-> 0x00)
 *   0x1A  55                       push rbp
 *   0x1B  48 83 EC 30              sub  rsp, 0x30
 *   0x1F  48 89 CD                 mov  rbp, rcx
 *   0x22  48 8B 4D 10              mov  rcx, [rbp+0x10]         ; this
 *   0x26  48 8B 55 18              mov  rdx, [rbp+0x18]         ; bet
 *   0x2A  4C 8B 4D 28              mov  r9,  [rbp+0x28]         ; chip
 *   0x2E  44 8B 45 20              mov  r8d, [rbp+0x20]         ; charId
 *   0x32  8B 45 24                 mov  eax, [rbp+0x24]         ; amount
 *   0x35  48 89 44 24 20           mov  [rsp+0x20], rax         ; 5th arg
 *   0x3A  FF 55 30                 call qword ptr [rbp+0x30]    ; AddBet
 *   0x3D  48 C7 45 08 01 00 00 00  mov  qword [rbp+0x08], 1    ; done
 *   0x45  48 C7 45 00 00 00 00 00  mov  qword [rbp+0x00], 0    ; go
 *   0x4D  48 89 E9                 mov  rcx, rbp
 *   0x50  48 83 C4 30              add  rsp, 0x30
 *   0x54  5D                       pop  rbp
 *   0x55  EB A9                    jmp  spin                    (-> 0x00)
 *   0x57  31 C0                    xor  eax, eax
 *   0x59  C3                       ret
 * --------------------------------------------------------------------------*/
static const uint8_t k_stub[] = {
    0x48, 0x8B, 0x41, 0x00,             /* mov  rax, [rcx+0x00]          */
    0x48, 0x85, 0xC0,                   /* test rax, rax                 */
    0x7F, 0x11,                         /* jg   +0x11  -> 0x1A           */
    0x7C, 0x4C,                         /* jl   +0x4C  -> 0x57           */
    0x51,                               /* push rcx                      */
    0x48, 0x83, 0xEC, 0x20,             /* sub  rsp, 0x20                */
    0xFF, 0x51, 0x38,                   /* call qword ptr [rcx+0x38]     */
    0x48, 0x83, 0xC4, 0x20,             /* add  rsp, 0x20                */
    0x59,                               /* pop  rcx                      */
    0xEB, 0xE6,                         /* jmp  -0x1A  -> 0x00           */
    0x55,                               /* push rbp                      */
    0x48, 0x83, 0xEC, 0x30,             /* sub  rsp, 0x30                */
    0x48, 0x89, 0xCD,                   /* mov  rbp, rcx                 */
    0x48, 0x8B, 0x4D, 0x10,             /* mov  rcx, [rbp+0x10]          */
    0x48, 0x8B, 0x55, 0x18,             /* mov  rdx, [rbp+0x18]          */
    0x4C, 0x8B, 0x4D, 0x28,             /* mov  r9,  [rbp+0x28]          */
    0x44, 0x8B, 0x45, 0x20,             /* mov  r8d, [rbp+0x20]          */
    0x8B, 0x45, 0x24,                   /* mov  eax, [rbp+0x24]          */
    0x48, 0x89, 0x44, 0x24, 0x20,       /* mov  [rsp+0x20], rax          */
    0xFF, 0x55, 0x30,                   /* call qword ptr [rbp+0x30]     */
    0x48, 0xC7, 0x45, 0x08, 0x01, 0x00, 0x00, 0x00,
                                        /* mov  qword [rbp+0x08], 1      */
    0x48, 0xC7, 0x45, 0x00, 0x00, 0x00, 0x00, 0x00,
                                        /* mov  qword [rbp+0x00], 0      */
    0x48, 0x89, 0xE9,                   /* mov  rcx, rbp                 */
    0x48, 0x83, 0xC4, 0x30,             /* add  rsp, 0x30                */
    0x5D,                               /* pop  rbp                      */
    0xEB, 0xA9,                         /* jmp  -0x57  -> 0x00           */
    0x31, 0xC0,                         /* xor  eax, eax                 */
    0xC3                                /* ret                           */
};

/* Compile-time guard: the stub's jg/jl displacements assume this layout. */
typedef char rr_sniper_stub_size_check[(sizeof(k_stub) == 0x5A) ? 1 : -1];

/* ---------------------------------------------------------------------------
 * Cached state.
 * --------------------------------------------------------------------------*/
static uint64_t g_page        = 0;   /* remote page base                    */
static uint64_t g_param       = 0;   /* == g_page                           */
static uint64_t g_stub        = 0;   /* == g_page + STUB_OFF                */
static HANDLE   g_thread      = NULL;
static uint32_t g_thread_pid  = 0;
static int32_t  g_char_id     = 0;
static int32_t  g_amount      = 1;
static int      g_mode        = RR_BET_NUMBER;
static int      g_chip_index  = 0;
static DWORD    g_model_tick  = 0;   /* last RouletteModel* refresh         */
static int      g_fires       = 0;

/* Pocket -> bet-description pointer, resolved once at arm time so the hot path
 * performs no reads at all. */
static uint64_t g_straight[37];
static uint64_t g_color_red, g_color_black;
static uint64_t g_dozen[3];

static int g_armed = 0;

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------*/
static uint64_t resolve_yield_fn(void) {
    HMODULE k32 = GetModuleHandleW(L"kernel32.dll");
    FARPROC fn;

    if (!k32) k32 = LoadLibraryW(L"kernel32.dll");
    if (!k32) return 0;

    fn = GetProcAddress(k32, "SwitchToThread");
    return (uint64_t)(uintptr_t)fn;
}

/* Read the description pointers for the configured mode into the caches. */
static int cache_descriptions(int mode) {
    if (mode == RR_BET_NUMBER) {
        for (int n = 0; n <= 36; n++) {
            g_straight[n] = rr_roulette_bet_desc(n, RR_BET_NUMBER);
            if (!PL(g_straight[n])) return 0;
        }
        return 1;
    }

    if (mode == RR_BET_COLOR) {
        g_color_red   = rr_roulette_bet_desc(1,  RR_BET_COLOR);   /* 1 is red */
        g_color_black = rr_roulette_bet_desc(2,  RR_BET_COLOR);   /* 2 is black */
        return PL(g_color_red) && PL(g_color_black) ? 1 : 0;
    }

    if (mode == RR_BET_DOZEN) {
        g_dozen[0] = rr_roulette_bet_desc(1,  RR_BET_DOZEN);
        g_dozen[1] = rr_roulette_bet_desc(13, RR_BET_DOZEN);
        g_dozen[2] = rr_roulette_bet_desc(25, RR_BET_DOZEN);
        return PL(g_dozen[0]) && PL(g_dozen[1]) && PL(g_dozen[2]) ? 1 : 0;
    }

    return 0;
}

/* Cached description lookup — no remote access. */
static uint64_t desc_from_cache(int winning, int mode) {
    if (winning < 0 || winning > 36) return 0;

    switch (mode) {
    case RR_BET_NUMBER:
        return g_straight[winning];

    case RR_BET_COLOR: {
        static const int red_nums[] = {
            1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
        };
        int is_red = 0;

        if (winning == 0) return 0;   /* green — a colour bet on 0 is invalid */
        for (int i = 0; i < (int)(sizeof(red_nums)/sizeof(red_nums[0])); i++)
            if (red_nums[i] == winning) { is_red = 1; break; }
        return is_red ? g_color_red : g_color_black;
    }

    case RR_BET_DOZEN:
        if (winning == 0) return 0;
        if (winning <= 12) return g_dozen[0];
        if (winning <= 24) return g_dozen[1];
        return g_dozen[2];

    default:
        return 0;
    }
}

/* Write the per-fire block (bet desc + char id + amount) as one request. */
static int write_fire_block(uint64_t bet_desc) {
    uint8_t blk[FIRE_BLK_LEN];

    memset(blk, 0, sizeof(blk));
    memcpy(blk + (SNIP_BET   - FIRE_BLK_OFF), &bet_desc, 8);
    memcpy(blk + (SNIP_CHAR  - FIRE_BLK_OFF), &g_char_id, 4);
    memcpy(blk + (SNIP_AMOUNT- FIRE_BLK_OFF), &g_amount, 4);

    return rr_write(g_param + FIRE_BLK_OFF, blk, sizeof(blk));
}

static int write_flag(uint32_t off, int64_t value) {
    return rr_write(g_param + off, &value, sizeof(value));
}

/* ---------------------------------------------------------------------------
 * arm()
 * --------------------------------------------------------------------------*/
int rr_roulette_sniper_arm(uint64_t world_ent, const RR_BET_CONFIG *cfg,
                           int32_t local_char_id) {
    if (!cfg || !cfg->enabled || local_char_id == 0) return 0;

    /* Already armed: this branch runs on every poll iteration, including the
     * 0.4 ms hyper cadence in the final seconds of Bets, so it must not touch
     * the target unless something actually changed.  The model pointer is the
     * only thing that can drift (player changes table), and it is refreshed at
     * most once a second. */
    if (g_armed && g_thread && g_thread_pid == g_rr_pid) {
        int32_t amount = (cfg->repeat >= 1 && cfg->repeat <= 20) ? cfg->repeat : 1;

        g_char_id = local_char_id;
        g_amount  = amount;

        if (cfg->chip_index != g_chip_index) {
            uint64_t chip;

            g_chip_index = cfg->chip_index;
            chip = rr_roulette_chip_desc(g_chip_index);
            if (!PL(chip)) return 0;
            if (!rr_write(g_param + SNIP_CHIP, &chip, sizeof(chip))) return 0;
        }

        if (cfg->mode != g_mode) {
            g_mode = cfg->mode;
            if (!cache_descriptions(g_mode)) return 0;
        }

        if (GetTickCount() - g_model_tick > 1000) {
            uint64_t model;

            g_model_tick = GetTickCount();
            if (rr_roulette_bet_prepare(world_ent, cfg, local_char_id)) {
                model = rr_roulette_model_ptr();
                if (PL(model) && rr_u64(g_param + SNIP_MODEL) != model)
                    rr_write(g_param + SNIP_MODEL, &model, sizeof(model));
            }
        }

        return 1;
    }

    /* ---- first arm of the session ---- */
    if (!rr_roulette_bet_prepare(world_ent, cfg, local_char_id)) return 0;

    {
        uint64_t model  = rr_roulette_model_ptr();
        uint64_t chip   = rr_roulette_prepared_chip();
        uint64_t addbet = rr_roulette_addbet_va();
        uint64_t yieldf = resolve_yield_fn();
        uint64_t page   = 0;
        uint8_t  blk[PARAM_SIZE];
        int64_t  go = 0;
        HANDLE   hproc;

        if (!PL(model) || !PL(chip) || !PL(addbet) || !yieldf) return 0;

        g_mode    = cfg->mode;
        g_char_id = local_char_id;
        g_amount  = (cfg->repeat >= 1 && cfg->repeat <= 20) ? cfg->repeat : 1;
        g_chip_index = cfg->chip_index;
        g_model_tick = GetTickCount();

        if (!cache_descriptions(g_mode)) return 0;

        /* RWX so the same page is writable by the driver and executable by the
         * game's loader. */
        if (!rr_drv_alloc_remote(g_rr_pid, PAGE_SIZE_, 0x40, &page) || !PL(page))
            return 0;

        memset(blk, 0, sizeof(blk));
        memcpy(blk + SNIP_GO,     &go,      8);
        memcpy(blk + SNIP_MODEL,  &model,   8);
        {
            uint64_t bet = g_straight[0];
            memcpy(blk + SNIP_BET, &bet, 8);
        }
        memcpy(blk + SNIP_CHAR,   &g_char_id, 4);
        memcpy(blk + SNIP_AMOUNT, &g_amount,  4);
        memcpy(blk + SNIP_CHIP,   &chip,    8);
        memcpy(blk + SNIP_ADDBET, &addbet,  8);
        memcpy(blk + SNIP_YIELD,  &yieldf,  8);

        if (!rr_write(page, blk, PARAM_SIZE)) {
            return 0;
        }
        if (!rr_write(page + STUB_OFF, k_stub, sizeof(k_stub))) {
            return 0;
        }

        hproc = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                            PROCESS_VM_OPERATION | PROCESS_VM_READ |
                            PROCESS_VM_WRITE, FALSE, (DWORD)g_rr_pid);
        if (!hproc) return 0;

        g_thread = CreateRemoteThread(hproc, NULL, 0,
                                      (LPTHREAD_START_ROUTINE)(uintptr_t)(page + STUB_OFF),
                                      (LPVOID)(uintptr_t)page, 0, NULL);
        CloseHandle(hproc);

        if (!g_thread) return 0;

        g_page       = page;
        g_param      = page;
        g_stub       = page + STUB_OFF;
        g_thread_pid = g_rr_pid;
        g_armed      = 1;
        g_fires      = 0;
        return 1;
    }
}

/* ---------------------------------------------------------------------------
 * set_model()
 * --------------------------------------------------------------------------*/
int rr_roulette_sniper_set_model(uint64_t roulette_model) {
    if (!g_armed || !PL(roulette_model)) return 0;
    if (rr_u64(g_param + SNIP_MODEL) == roulette_model) return 1;
    return rr_write(g_param + SNIP_MODEL, &roulette_model, sizeof(roulette_model))
           ? 1 : 0;
}

/* ---------------------------------------------------------------------------
 * fire() — the hot path.  Exactly two driver writes, zero remote reads.
 * --------------------------------------------------------------------------*/
int rr_roulette_sniper_fire(int winning) {
    uint64_t bet_desc;

    if (!g_armed || !g_thread) return 0;

    bet_desc = desc_from_cache(winning, g_mode);
    if (!PL(bet_desc)) return 0;

    if (!write_fire_block(bet_desc)) return 0;
    if (!write_flag(SNIP_GO, 1))     return 0;

    g_fires++;
    return 1;
}

int rr_roulette_sniper_armed(void) { return g_armed; }
uint64_t rr_roulette_sniper_param_addr(void) { return g_param; }
int rr_roulette_sniper_fire_count(void) { return g_fires; }

/* ---------------------------------------------------------------------------
 * disarm()
 * --------------------------------------------------------------------------*/
void rr_roulette_sniper_disarm(void) {
    if (!g_armed) return;

    /* Ask the stub to leave its loop.  The stub clears `go` itself after a
     * fire (mov qword [rbp+0x00], 0), so a single -1 can be overwritten if it
     * lands while AddBet is still running and the thread would then spin in the
     * game process forever.  Retry: each pass either observes the thread exit or
     * re-arms the flag for the next loop iteration. */
    for (int attempt = 0; attempt < 8 && g_thread; attempt++) {
        write_flag(SNIP_GO, -1);
        if (WaitForSingleObject(g_thread, 50) == WAIT_OBJECT_0) break;
    }

    if (g_thread) {
        /* Still alive after ~400 ms: the stub is wedged inside AddBet.  Leave
         * the page in place (the driver has no free-page IOCTL) but stop
         * reporting the sniper as armed so no further fire() can touch it. */
        CloseHandle(g_thread);
    }

    g_thread     = NULL;
    g_armed      = 0;
    g_page       = 0;
    g_param      = 0;
    g_stub       = 0;
    g_thread_pid = 0;
    g_chip_index = 0;
    g_model_tick = 0;
    g_fires      = 0;
}
