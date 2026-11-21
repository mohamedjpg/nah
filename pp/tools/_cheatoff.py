"""Verify the six offsets hardcoded in rr_cheat.c against dump_index.json."""
import json, sys

IDX = r"D:\tools2\dumpss\robrun\src\pp\offsets\dump_index.json"
data = json.load(open(IDX, encoding="utf-8"))

def field(cls, name):
    c = data.get(cls)
    if c is None:
        return ("NO CLASS", None)
    f = c["fields"].get(name)
    if f is None:
        return ("NO FIELD", None)
    return ("ok", f["offset"])

checks = [
    ("BattleModel.<CheatModel>",              "Game.Battle.BattleModel", "<CheatModel>k__BackingField", 0x360),
    ("BattleModel.<CheatSpawnCarModel>",      "Game.Battle.BattleModel", "<CheatSpawnCarModel>k__BackingField", 0x80),
    ("BattleModel.<CheatSpawnHelicopterModel>","Game.Battle.BattleModel", "<CheatSpawnHelicopterModel>k__BackingField", 0x88),
    ("CheatModel.<IsEnabled>",                "ClientCore.Models.CheatModel.CheatModel", "<IsEnabled>k__BackingField", 0x10),
    ("GameModel.<NetworkStatusModel>",        "Game.GameModel", "<NetworkStatusModel>k__BackingField", 0x88),
    ("NetworkStatusModel.CheatActivated",     "Game.Shared.NetworkStatusModel", "CheatActivated", 0x27),
]

bad = 0
for label, cls, name, want in checks:
    status, got = field(cls, name)
    ok = (status == "ok" and got == want)
    if not ok:
        bad += 1
    print("%-42s %-8s dump=%-6s header=0x%X %s" % (
        label, status, got if got is None else hex(got), want, "OK" if ok else "MISMATCH"))

# Also confirm BattleModel is not a parent of the Cheat fields by accident and
# that the class really is the one the entry chain resolves.
print()
print("BattleModel field count:", len(data["Game.Battle.BattleModel"]["fields"]))
print("GameModel  field count:", len(data["Game.GameModel"]["fields"]))
sys.exit(1 if bad else 0)
