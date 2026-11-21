/* menu_webview.cpp - WebView2 host for the embedded HTML settings menu.
 *
 * A dedicated window thread hosts the page compiled into app.rc. BR_Config
 * provides settings shared with the overlay. Messages are strings:
 *   HTML -> host: set:<key>:<int>, col:<index>:r,g,b, act:save|load,
 *                 copy:<text>, drag:<x>,<y>,<dx>,<dy>, dragend:, close:, hello:
 *   host -> HTML: state:<json>, telem:<json>, toast:<text>
 * See msg_cb() for commands and build_state_json() for the returned fields.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <cstdlib>

#include "menu_bridge.h"
#include "app_resources.h"
#include "wv2_cb.h"
#include "rr_game.h"
#include "rr_mem.h"
#include "rr_unity.h"
#include "rr_roulette.h"
#include "rr_roulette_bet.h"
#include "rr_roulette_sniper.h"
#include "robrun_offsets.h"

/* Include the COM declarations before the WebView2 SDK header. */
#include <objbase.h>
#include <rpc.h>
#include <rpcndr.h>
#include <combaseapi.h>
#include "WebView2.h"
#include "wv2_cb_impl.h"
#pragma comment(lib, "WebView2Loader.dll.lib")

/* Menu window state. */
static HWND              g_hwnd   = NULL;
static ICoreWebView2Environment*         g_env  = nullptr;
static ICoreWebView2*                   g_wv   = nullptr;
static ICoreWebView2Controller*          g_ctl  = nullptr;

static HANDLE  g_thread     = NULL;
static DWORD   g_thread_id  = 0;
static volatile LONG g_quit = 0;
static volatile LONG g_visible = 1;
static bool    g_dragging   = false;
static bool    g_page_ready = false;
static HRESULT g_start_error = S_OK;
static HWND    g_prev_fg = NULL;
static POINT   g_drag_origin= {0,0};   /* Window position at the start of a drag. */

static const int WIN_W = 976;
static const int WIN_H = 640;

static void menu_log(const char* stage, HRESULT hr) {
    if (FILE* f = fopen("wv2_error.log", "a")) {
        fprintf(f, "%lu Port menu: %s (0x%08lX)\n",
                GetTickCount(), stage, static_cast<unsigned long>(hr));
        fclose(f);
    }
}

static void menu_failed(const char* stage, HRESULT hr) {
    g_start_error = FAILED(hr) ? hr : E_FAIL;
    menu_log(stage, g_start_error);
    InvalidateRect(g_hwnd, NULL, TRUE);
}

static HRESULT navigate_menu(ICoreWebView2* webview) {
    HMODULE module = GetModuleHandleW(NULL);
    HRSRC resource = FindResourceW(module, MAKEINTRESOURCEW(IDR_MENU_HTML), MAKEINTRESOURCEW(10));
    if (!resource) return E_FAIL;
    HGLOBAL data = LoadResource(module, resource);
    const char* bytes = static_cast<const char*>(LockResource(data));
    int size = (int)SizeofResource(module, resource);
    if (!bytes || size <= 0) return E_FAIL;
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, bytes, size, NULL, 0);
    if (!count) return E_FAIL;
    std::wstring html((size_t)count, L'\0');
    if (!MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, bytes, size, &html[0], count))
        return E_FAIL;
    return webview->NavigateToString(html.c_str());
}

/* JSON serialization helpers. */
static void jcat_int(std::string& s, const char* k, int v, bool first=false){
    char b[96]; snprintf(b,sizeof(b),"%s\"%s\":%d", first?"":",",k,v); s+=b;
}
static std::string build_state_json(BR_Config* b) {
    std::string s("{");
#define BR_JSON(field, initial, minimum, maximum) jcat_int(s, #field, b->field, s.size() == 1);
    BR_SETTINGS(BR_JSON)
#undef BR_JSON
    s += ",\"colors\":{";
    for (int i = 0; i < BR_COLOR_COUNT; ++i) {
        char rgb[40];
        snprintf(rgb, sizeof(rgb), "%s\"%d\":[%u,%u,%u]", i ? "," : "", i,
                 (unsigned)b->color[i].rgb[0], (unsigned)b->color[i].rgb[1], (unsigned)b->color[i].rgb[2]);
        s += rgb;
    }
    s += "}}";
    return s;
}

static std::string build_telem_json(BR_Config* b) {
    std::string s("{");
    jcat_int(s,"pid",b->telem_game_pid,1);
    jcat_int(s,"targets",b->telem_targets);
    jcat_int(s,"los",b->telem_los_state);
    /* Roulette fields. */
    jcat_int(s,"rl_valid",b->telem_roulette_valid);
    jcat_int(s,"rl_count",b->telem_roulette_count);
    jcat_int(s,"rl_win",b->telem_roulette_winning);
    jcat_int(s,"rl_phase",b->telem_roulette_phase);
    jcat_int(s,"rl_remaining",b->telem_roulette_remaining);
    /* phase_end as a double (ms timestamp) to avoid int overflow in JS. */
    char pebuf[64];
    snprintf(pebuf, sizeof(pebuf), ",\"rl_end\":%.0f",
             (double)b->telem_roulette_phase_end);
    s += pebuf;
    /* Auto-bet state mirrored to HTML. */
    jcat_int(s,"bet_enabled",b->bet_enabled);
    jcat_int(s,"bet_chip",b->bet_chip);
    jcat_int(s,"bet_count",b->bet_count);
    jcat_int(s,"bet_mode",b->bet_mode);
    jcat_int(s,"bet_last_win",b->bet_last_win);
    s += "}";
    return s;
}

static void wv_send(const std::string& msg){
    if(!g_wv) return;
    std::wstring w(msg.begin(), msg.end());
    g_wv->PostWebMessageAsString(w.c_str());
}

/* Integer setting fields are resolved by name through the shared schema. */
/* Messages sent from the HTML page. */
static HRESULT STDMETHODCALLTYPE msg_cb(ICoreWebView2* sender,
    ICoreWebView2WebMessageReceivedEventArgs* args, void* ctx)
{
    (void)sender;(void)ctx;
    if(!args) return S_OK;
    LPWSTR w = nullptr;
    if(FAILED(args->TryGetWebMessageAsString(&w)) || !w) return S_OK;
    std::string msg;
    for(const wchar_t* p=w; *p; ++p){
        if(*p<128) msg+=(char)*p;
    }
    CoTaskMemFree(w);
    BR_Config* b = br_get();

    /* Split the message at the first colon into command and body. */
    size_t c1 = msg.find(':');
    if(c1==std::string::npos) return S_OK;
    std::string cmd = msg.substr(0,c1), body = msg.substr(c1+1);

    if (cmd == "set") {
        size_t c2 = body.find(':');
        if (c2 != std::string::npos)
            br_config_set(b, body.substr(0,c2).c_str(), atoi(body.substr(c2+1).c_str()));
    }
    else if (cmd == "col") {
        int index, red, green, blue;
        if (sscanf(body.c_str(), "%d:%d,%d,%d", &index, &red, &green, &blue) == 4 &&
            index >= 0 && index < BR_COLOR_COUNT &&
            (unsigned)red <= 255 && (unsigned)green <= 255 && (unsigned)blue <= 255) {
            b->color[index].rgb[0] = (unsigned char)red;
            b->color[index].rgb[1] = (unsigned char)green;
            b->color[index].rgb[2] = (unsigned char)blue;
        }
    }
    else if (cmd == "act") {
        if (body == "save") {
            wv_send(br_config_save() ? "toast:Settings saved" : "toast:Could not save CoreRR.cfg");
        } else if (body == "load") {
            if (br_config_load()) {
                wv_send("state:" + build_state_json(b));
                wv_send("toast:Settings loaded");
            } else {
                wv_send("toast:Could not load CoreRR.cfg");
            }
        }
    }
    else if(cmd=="drag"){
        /* The page sends total displacement from the start of the drag. Apply it
         * to the original window position; adding it to the current position would
         * count earlier movement again.
         */
        int sx=0, sy=0, dx=0, dy=0;
        if(sscanf(body.c_str(),"%d,%d,%d,%d",&sx,&sy,&dx,&dy)==4){
            if(!g_dragging){
                g_dragging=true;
                /* Remember the window position once, when the drag begins. */
                RECT wr; GetWindowRect(g_hwnd,&wr);
                g_drag_origin.x=wr.left; g_drag_origin.y=wr.top;
            }
            SetWindowPos(g_hwnd,NULL,
                         g_drag_origin.x+dx, g_drag_origin.y+dy,
                         0,0, SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE);
            (void)sx; (void)sy;
        }
    }
    else if(cmd=="dragend"){
        g_dragging=false;
        g_drag_origin.x=g_drag_origin.y=0;
    }
    else if(cmd=="close"){
        br_set_menu_visible(0);
    }
    else if(cmd=="bet"){
        /* bet:<field>:<value> - configure auto-bet from HTML. */
        size_t c2 = body.find(':');
        if(c2 != std::string::npos){
            std::string bkey = body.substr(0,c2);
            int bval = atoi(body.substr(c2+1).c_str());
            if(bkey=="enabled"){
                b->bet_enabled = (bval ? 1 : 0);
                if(!bval) b->bet_last_win = -1;
            } else if(bkey=="chip"){
                if(bval>=0 && bval<=4) b->bet_chip = bval;
            } else if(bkey=="count"){
                if(bval>=1 && bval<=20) b->bet_count = bval;
            } else if(bkey=="mode"){
                if(bval>=0 && bval<=2) b->bet_mode = bval;
            }
        }
    }
    else if (cmd == "hello") {
        if (!g_page_ready) menu_log("embedded menu ready", S_OK);
        g_page_ready = true;
        g_start_error = S_OK;
        wv_send("state:" + build_state_json(b));
        wv_send("telem:" + build_telem_json(b));
    }
    return S_OK;
}

/* The WebView2 event handler above applies page commands to shared settings. */

/* Window messages and dragging. */
static LRESULT WINAPI wnd_proc(HWND h, UINT m, WPARAM w, LPARAM l){
    switch(m){
    case WM_DESTROY: PostQuitMessage(0); break;
    case WM_PAINT: {
        PAINTSTRUCT paint;
        HDC dc = BeginPaint(h, &paint);
        if (!g_page_ready) {
            RECT rect;
            GetClientRect(h, &rect);
            FillRect(dc, &rect, static_cast<HBRUSH>(GetStockObject(BLACK_BRUSH)));
            SetTextColor(dc, RGB(241, 235, 251));
            SetBkMode(dc, TRANSPARENT);
            const wchar_t* text = FAILED(g_start_error)
                ? L"Felonious Funnery could not open WebView2. See wv2_error.log. Press F1 to close."
                : L"Loading Felonious Funnery...";
            DrawTextW(dc, text, -1, &rect, DT_SINGLELINE | DT_CENTER | DT_VCENTER);
        }
        EndPaint(h, &paint);
        return 0;
    }
    }
    return DefWindowProcW(h,m,w,l);
}

static HRESULT controller_ready(HRESULT hr, ICoreWebView2Controller* controller) {
    if (FAILED(hr) || !controller) {
        menu_failed("create browser controller", hr);
        return S_OK;
    }
    g_ctl = controller;
    g_ctl->AddRef();
    RECT bounds;
    GetClientRect(g_hwnd, &bounds);
    g_ctl->put_Bounds(bounds);
    g_ctl->put_IsVisible(IsWindowVisible(g_hwnd));

    hr = g_ctl->get_CoreWebView2(&g_wv);
    if (SUCCEEDED(hr) && g_wv) {
        auto handler = MakeMsgCb([](ICoreWebView2* sender, ICoreWebView2WebMessageReceivedEventArgs* args) {
            return msg_cb(sender, args, nullptr);
        });
        EventRegistrationToken token{};
        hr = g_wv->add_WebMessageReceived(handler, &token);
        handler->Release();
        if (SUCCEEDED(hr)) hr = navigate_menu(g_wv);
    } else if (SUCCEEDED(hr)) {
        hr = E_FAIL;
    }
    if (FAILED(hr)) {
        g_ctl->put_IsVisible(FALSE);
        menu_failed("open embedded menu", hr);
    }
    return S_OK;
}

static void start_webview(const wchar_t* data_dir, bool allow_retry);

static void browser_start_failed(HRESULT hr, bool allow_retry) {
    wchar_t fallback[MAX_PATH];
    DWORD length = GetTempPathW(_countof(fallback), fallback);
    if (allow_retry && length && length < _countof(fallback) &&
        swprintf_s(fallback + length, _countof(fallback) - length,
                   L"RRToolPortWebView2_%lu", GetCurrentProcessId()) >= 0) {
        menu_log("retry browser with a separate profile", hr);
        start_webview(fallback, false);
        return;
    }
    menu_failed("create browser environment", hr);
}

static void start_webview(const wchar_t* data_dir, bool allow_retry) {
    auto handler = MakeEnvCb([allow_retry](HRESULT hr, ICoreWebView2Environment* env) -> HRESULT {
        if (FAILED(hr) || !env) {
            browser_start_failed(FAILED(hr) ? hr : E_FAIL, allow_retry);
            return S_OK;
        }
        g_env = env;
        g_env->AddRef();
        auto controller = MakeCtlCb(controller_ready);
        hr = env->CreateCoreWebView2Controller(g_hwnd, controller);
        controller->Release();
        if (FAILED(hr)) menu_failed("request browser controller", hr);
        return S_OK;
    });
    HRESULT hr = CreateCoreWebView2EnvironmentWithOptions(nullptr, data_dir, nullptr, handler);
    handler->Release();
    if (FAILED(hr)) browser_start_failed(hr, allow_retry);
}

/* Menu window thread. */
static DWORD WINAPI menu_thread(LPVOID){
    /* Initialize COM on this thread before creating WebView2. A failed COM
     * initialization can leave the host window visible with no rendered page.
     */
    HRESULT com = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    if (FAILED(com)) { menu_log("initialize COM", com); return 1; }
    WNDCLASSEXW wc={0};
    wc.cbSize=sizeof(wc); wc.style=CS_CLASSDC;
    wc.lpfnWndProc=wnd_proc; wc.hInstance=GetModuleHandleW(NULL);
    wc.lpszClassName=L"mrzvCoreWebMenu";
    wc.hCursor=LoadCursorW(NULL,(LPCWSTR)IDC_ARROW);
    RegisterClassExW(&wc);

    int sw=GetSystemMetrics(SM_CXSCREEN), sh=GetSystemMetrics(SM_CYSCREEN);
    g_hwnd=CreateWindowExW(
        WS_EX_TOPMOST|WS_EX_TOOLWINDOW,
        wc.lpszClassName, L"mrzvCore",
        WS_POPUP,
        sw/2-WIN_W/2, 80, WIN_W, WIN_H,
        NULL,NULL,wc.hInstance,NULL);
    if(!g_hwnd) {
        menu_log("create menu window", HRESULT_FROM_WIN32(GetLastError()));
        UnregisterClassW(wc.lpszClassName, wc.hInstance);
        CoUninitialize();
        return 1;
    }

    wchar_t data_dir[MAX_PATH];
    DWORD length = GetEnvironmentVariableW(L"LOCALAPPDATA", data_dir, _countof(data_dir));
    if (!length || length >= _countof(data_dir))
        length = GetTempPathW(_countof(data_dir), data_dir);
    if (!length || length >= _countof(data_dir) ||
        wcscat_s(data_dir, L"\\RRToolPortWebView2") != 0) {
        menu_failed("resolve browser profile directory", E_FAIL);
    } else {
        start_webview(data_dir, true);
    }

    BR_Config* b = br_get();
    DWORD last_telem=0;
    DWORD last_roulette=0;
    int32_t last_win_seen = -1;   /* track last seen WinningNumber for instant push */
    DWORD shown_at = 0;
    /* Server-time calibration for hyper-fast end-of-Bets-phase polling. */
    int      srv_calibrated = 0;        /* 1 once we have a valid offset          */
    int64_t  srv_offset_ms  = 0;        /* server_ms - local_ms (GetTickCount64)  */
    int64_t  srv_phase_end  = 0;        /* cached phase_end_ms for current round  */
    int32_t  last_phase_seen = -1;      /* detect phase transitions               */
    int32_t  bet_char_id = 0;           /* cached local character id for bets      */

    MSG msg; ZeroMemory(&msg,sizeof(msg));
    while(msg.message!=WM_QUIT && !g_quit){
        if(PeekMessageW(&msg,NULL,0,0,PM_REMOVE)){
            TranslateMessage(&msg); DispatchMessageW(&msg); continue;
        }
        if (!InterlockedCompareExchange(&g_visible, 0, 0)) {
            if (IsWindowVisible(g_hwnd)) {
                if (g_ctl) g_ctl->put_IsVisible(FALSE);
                ShowWindow(g_hwnd, SW_HIDE);
                if (g_prev_fg && IsWindow(g_prev_fg)) SetForegroundWindow(g_prev_fg);
                g_prev_fg = NULL;
            }
            MsgWaitForMultipleObjectsEx(0, NULL, 80, QS_ALLINPUT, MWMO_INPUTAVAILABLE);
            continue;
        }
        if (!IsWindowVisible(g_hwnd)) {
            shown_at = GetTickCount();
            g_prev_fg = GetForegroundWindow();
            SetWindowPos(g_hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                         SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOOWNERZORDER);
            if (g_ctl && SUCCEEDED(g_start_error)) g_ctl->put_IsVisible(TRUE);
        }

        DWORD now=GetTickCount();
        if (!g_page_ready && SUCCEEDED(g_start_error) && now - shown_at > 15000) {
            if (g_ctl) g_ctl->put_IsVisible(FALSE);
            menu_failed("wait for embedded menu", HRESULT_FROM_WIN32(ERROR_TIMEOUT));
        }
        /* Roulette fast-poll.
         * Normal cadence: 50 ms.
         * Hyper cadence:  5 ms when in Bets phase with <= 2000 ms remaining.
         *
         * Server-time calibration: when phase transitions to Bets we record
         *   srv_offset_ms = phase_end_ms - GetTickCount64()
         * and from then on:
         *   remaining_ms  = srv_phase_end - (GetTickCount64() + srv_offset_ms)
         *
         * This turns phase_end_ms into a local-clock deadline without needing
         * any extra game reads.
         */
        {
            ULONGLONG local_now64 = GetTickCount64();
            /* Determine effective poll interval.
             *
             * GetTickCount() is ~15.6 ms granular, which is far too coarse for
             * a sub-tick bet window, so the hyper cadence is gated on the
             * performance counter instead.  Normal: 50 ms.  Final 3 s of Bets:
             * ~0.4 ms. */
            static LARGE_INTEGER qpc_freq = {0};
            static ULONGLONG qpc_last = 0;
            ULONGLONG qpc_now = 0;
            int hyper = 0;
            int due = 0;

            if (!qpc_freq.QuadPart) QueryPerformanceFrequency(&qpc_freq);
            QueryPerformanceCounter((LARGE_INTEGER*)&qpc_now);

            if (srv_calibrated && srv_phase_end > 0 && last_phase_seen == 0) {
                int64_t remaining = srv_phase_end - (int64_t)(local_now64 + (ULONGLONG)srv_offset_ms);
                if (remaining <= 3000) hyper = 1;
            }

            {
                ULONGLONG delta_us = (qpc_freq.QuadPart && qpc_last)
                    ? (qpc_now - qpc_last) * 1000000ULL / (ULONGLONG)qpc_freq.QuadPart
                    : 2000000ULL;
                due = hyper ? (delta_us >= 400ULL) : ((now - last_roulette) > 50);
            }

            if (g_wv && b->telem_game_pid && due) {
                last_roulette = now;
                qpc_last = qpc_now;
                uint64_t wem = game_world_addr();
                if (wem) {
                    RR_ROULETTE rlt;
                    if (rr_roulette_read(wem, &rlt)) {
                        b->telem_roulette_valid     = rlt.valid;
                        b->telem_roulette_count     = rlt.roulette_count;
                        b->telem_roulette_winning   = rlt.winning_number;
                        b->telem_roulette_phase     = rlt.phase_index;
                        b->telem_roulette_phase_end = rlt.phase_end_ms;

                        /* Phase-transition tracking and server-time calibration. */
                        if (rlt.phase_index != last_phase_seen) {
                            if (rlt.phase_index == 0) {
                                /* Entered Bets phase: calibrate server offset. */
                                if (rlt.phase_end_ms > 0) {
                                    srv_offset_ms  = (int64_t)rlt.phase_end_ms - (int64_t)local_now64;
                                    srv_phase_end  = rlt.phase_end_ms;
                                    srv_calibrated = 1;
                                }
                            }
                            last_phase_seen = rlt.phase_index;
                        } else if (rlt.phase_index == 0 && rlt.phase_end_ms != srv_phase_end && rlt.phase_end_ms > 0) {
                            /* phase_end_ms updated mid-Bets (shouldn't happen but keep in sync). */
                            srv_offset_ms = (int64_t)rlt.phase_end_ms - (int64_t)local_now64;
                            srv_phase_end = rlt.phase_end_ms;
                        }

                        /* Store remaining ms for HTML countdown. */
                        {
                            int64_t rem = -1;
                            if (srv_calibrated && srv_phase_end > 0) {
                                rem = srv_phase_end - (int64_t)(local_now64 + (ULONGLONG)srv_offset_ms);
                                if (rem < 0) rem = 0;
                                if (rem > 999999) rem = -1;
                            }
                            b->telem_roulette_remaining = (int32_t)rem;
                        }

                        /* Arm the sniper as soon as bets are open.  This is
                         * where the expensive discovery happens (model walk,
                         * static-field lookup, page alloc, thread start), so it
                         * must never run inside the fire window.  The local
                         * character id is resolved once and cached: it cannot
                         * change while attached, and reading it every 0.4 ms
                         * would cost more than the poll itself. */
                        if (b->bet_enabled && rlt.phase_index == 0) {
                            if (!bet_char_id) {
                                uint64_t lp = rr_local_player();
                                if (lp) {
                                    int32_t tmp = rr_i32(lp + RR_OFF_CHAR_ID);
                                    if (rr_ok()) bet_char_id = tmp;
                                }
                            }
                            if (bet_char_id) {
                                RR_BET_CONFIG bc;
                                bc.enabled    = 1;
                                bc.chip_index = b->bet_chip;
                                bc.repeat     = (b->bet_count >= 1 && b->bet_count <= 20) ? b->bet_count : 1;
                                bc.mode       = (b->bet_mode  >= 0 && b->bet_mode  <= 2)  ? b->bet_mode  : 0;
                                rr_roulette_sniper_arm(wem, &bc, bet_char_id);
                            }
                        }

                        /* Fire the instant the number becomes visible.  No
                         * phase gate here on purpose: checking the phase first
                         * would cost another three reads in the one window
                         * that matters, and AddBet is harmless if the server
                         * has already closed the table. */
                        if (rlt.winning_number >= 0 && rlt.winning_number <= 36 &&
                            last_win_seen < 0 && g_wv) {
                            wv_send("telem:" + build_telem_json(b));
                            if (b->bet_enabled && b->bet_last_win != rlt.winning_number &&
                                rr_roulette_sniper_armed()) {
                                if (rr_roulette_sniper_fire(rlt.winning_number))
                                    b->bet_last_win = rlt.winning_number;
                            }
                        }
                        /* Reset bet_last_win when a new round starts. */
                        if (rlt.winning_number < 0 && last_win_seen >= 0)
                            b->bet_last_win = -1;
                        last_win_seen = rlt.winning_number;
                    }
                }
            }
        }

        /* Regular 500 ms telem tick for all other fields. */
        if(g_wv && now-last_telem>500){
            last_telem=now;
            wv_send("telem:"+build_telem_json(b));
        }
        /* Wake for input immediately instead of leaving messages queued until
           the fixed sleep ends. The timeout still services telemetry. */
        MsgWaitForMultipleObjectsEx(0, NULL, 5, QS_ALLINPUT, MWMO_INPUTAVAILABLE);
    }

    if(g_ctl){ g_ctl->Close(); g_ctl->Release(); g_ctl=nullptr; }
    if(g_wv){ g_wv->Release(); g_wv=nullptr; }
    if(g_env){ g_env->Release(); g_env=nullptr; }
    DestroyWindow(g_hwnd);
    g_hwnd = NULL;
    UnregisterClassW(L"mrzvCoreWebMenu",GetModuleHandleW(NULL));
    CoUninitialize();
    return 0;
}

/* Public menu bridge. */
static BR_Config g_br_inst;
static volatile LONG g_br_inited = 0;

BR_Config* br_get(void){
    if(InterlockedCompareExchange(&g_br_inited,1,0)==0){
        ZeroMemory(&g_br_inst,sizeof(g_br_inst));
        g_br_inst.magic=BR_MAGIC; g_br_inst.version=BR_VERSION;
#define BR_DEFAULT(field, initial, minimum, maximum) g_br_inst.field = initial;
        BR_SETTINGS(BR_DEFAULT)
#undef BR_DEFAULT
        g_br_inst.menu_open = 1;
        static const unsigned char pal[BR_COLOR_COUNT][3] = {
            { 86,168,255},{255, 86, 86},{120,255,140},{ 86,255,246},
            {158,158,158},{255,255,255},{255,255,255},{255,255,255},
            {255,255,255},{255,255,255},{255,255,255},{120,255,140},
            {255,176, 66},{139, 92,246},{220,220,220},
        };
        for(int i=0;i<BR_COLOR_COUNT;i++){
            g_br_inst.color[i].rgb[0]=pal[i][0];
            g_br_inst.color[i].rgb[1]=pal[i][1];
            g_br_inst.color[i].rgb[2]=pal[i][2];
        }
    }
    return &g_br_inst;
}

int br_start_menu(void){
    if(g_thread) return 0;
    g_quit=0;
    g_thread=CreateThread(NULL,0,menu_thread,NULL,0,&g_thread_id);
    return g_thread?0:1;
}
void br_stop_menu(void){
    if(!g_thread) return;
    g_quit=1;
    if(g_hwnd) PostMessageW(g_hwnd,WM_NULL,0,0);
    WaitForSingleObject(g_thread,3000);
    CloseHandle(g_thread); g_thread=NULL;
}
void br_request_toggle(void){
    br_set_menu_visible(!InterlockedCompareExchange(&g_visible, 0, 0));
}

void br_set_menu_visible(int visible) {
    br_get()->menu_open = visible != 0;
    InterlockedExchange(&g_visible, visible != 0);
    if (g_hwnd) PostMessageW(g_hwnd, WM_NULL, 0, 0);
}
