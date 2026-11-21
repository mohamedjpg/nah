"""Cheap structural sanity checks on the C sources touched by the cheat tab."""
import io, re, sys

BASE = r"D:\tools2\dumpss\robrun\src\pp\2_src_port"
files = ["rr_cheat.c", "rr_cheat.h", "rr_game.c", "rr_game.h", "menu_webview.cpp", "menu_bridge.h"]

bad = 0
for f in files:
    s = io.open(BASE + "\\" + f, encoding="utf-8", errors="replace").read()
    # Strip string literals and comments so braces inside them do not count.
    t = re.sub(r'//[^\n]*', '', s)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'"(\\.|[^"\\])*"', '""', t)
    t = re.sub(r"'(\\.|[^'\\])*'", "''", t)
    b = t.count("{") - t.count("}")
    p = t.count("(") - t.count(")")
    flag = "" if (b == 0 and p == 0) else "  <-- IMBALANCE"
    if flag:
        bad += 1
    print("%-18s braces %+d  parens %+d%s" % (f, b, p, flag))

# rr_cheat.c: every function it calls must be declared in a header it includes.
src = io.open(BASE + r"\rr_cheat.c", encoding="utf-8").read()
includes = re.findall(r'#include "([^"]+)"', src)
print("\nincludes:", includes)

needed = ["game_battle_model", "game_game_model", "rr_read", "rr_u64", "u_is"]
decls = ""
for inc in includes:
    try:
        decls += io.open(BASE + "\\" + inc, encoding="utf-8", errors="replace").read()
    except OSError:
        print("  MISSING HEADER", inc)
        bad += 1
for n in needed:
    if not re.search(r'\b%s\s*\(' % re.escape(n), decls):
        print("  UNDECLARED", n)
        bad += 1
    else:
        print("  declared  ", n)

# The two accessors must actually exist in rr_game.c.
game = io.open(BASE + r"\rr_game.c", encoding="utf-8").read()
for n in ["game_battle_model", "game_game_model"]:
    if not re.search(r'^uint64_t %s\(void\)' % n, game, re.M):
        print("  NOT DEFINED", n)
        bad += 1

# menu_bridge.h telemetry fields must all be read/written consistently.
bridge = io.open(BASE + r"\menu_bridge.h", encoding="utf-8").read()
declared = set(re.findall(r'\b(telem_cheat_[a-z_]+)\b', bridge))
wv = io.open(BASE + r"\menu_webview.cpp", encoding="utf-8").read()
used = set(re.findall(r'\b(telem_cheat_[a-z_]+)\b', wv))
print("\nbridge fields:", len(declared), " used in webview:", len(used))
print("declared-but-unused:", sorted(declared - used))
print("used-but-undeclared:", sorted(used - declared))
if declared - used or used - declared:
    bad += 1

sys.exit(1 if bad else 0)
