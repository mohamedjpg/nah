"""Confirm the capability list names every Cheat*Message class the build ships."""
import io, json, re, sys

IDX = r"D:\tools2\dumpss\robrun\src\pp\offsets\dump_index.json"
HTML = r"D:\tools2\dumpss\robrun\src\pp\2_src_port\menu.html"

data = json.load(open(IDX, encoding="utf-8"))
by_name = {}
for fq, c in data.items():
    by_name.setdefault(c.get("name"), fq)

html = io.open(HTML, encoding="utf-8").read()
block = html[html.index("function ctCapabilitiesHTML"):]
block = block[:block.index("bridge && bridge.addEventListener")]
listed = set(re.findall(r'"(Cheat[A-Za-z]+Message)"', block))

# Any class whose name matches Cheat*Message and derives from the Message family.
def is_message(decl):
    return bool(re.search(r':\s*\w*Message\b', decl))

all_msgs = {c["name"] for c in data.values()
            if re.fullmatch(r'Cheat[A-Za-z]+Message', c.get("name") or "")
            and is_message(c.get("decl", ""))}

missing_from_dump = sorted(n for n in listed if n not in by_name)
not_a_message = sorted(n for n in listed if n in by_name
                       and not is_message(data[by_name[n]]["decl"]))
unlisted = sorted(all_msgs - listed)

print("listed      :", len(listed))
print("in metadata :", len(all_msgs))
print("missing from dump :", missing_from_dump)
print("not Message       :", not_a_message)
print("unlisted          :", unlisted)
print("duplicates in block:", len(re.findall(r'"(Cheat[A-Za-z]+Message)"', block)) - len(listed))

bad = missing_from_dump or not_a_message or unlisted
sys.exit(1 if bad else 0)
