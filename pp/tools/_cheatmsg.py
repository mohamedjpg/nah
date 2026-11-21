"""Does client code ever SEND CheatRouletteSetWinningNumberMessage?

Scans the image for references to the message's ctor / get_Number, and resolves
callers to managed method names.
"""
import json, struct, bisect

DLL = r'D:\tools2\dumpss\robrun\newasmbly\GameAssembly.dll'
SCRIPT = r'D:\tools2\dumpss\robrun\newasmbly\script.json'
data = open(DLL, 'rb').read()

e = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, e+6)[0]
optsz = struct.unpack_from('<H', data, e+0x14)[0]
sec = e + 24 + optsz
sections = []
for i in range(nsec):
    o = sec + i*40
    name = data[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o+8)
    sections.append((name, vaddr, vsize, raddr, rsize))

TARGETS = {
    0x49f48c0: 'CheatRouletteSetWinningNumberMessage..ctor',
    0x49f4970: 'CheatRouletteSetWinningNumberMessage.get_Number',
    0x49f49c0: 'CheatRouletteSetWinningNumberMessage.get_Type',
}

callers = {}
for tname, tva, tvsz, traw, trsz in sections:
    if tname not in ('.text', 'il2cpp'):
        continue
    blob = data[traw:traw+trsz]
    i = 0
    n = len(blob)
    while True:
        i = blob.find(b'\xe8', i)
        if i < 0 or i + 5 > n:
            break
        rel = struct.unpack_from('<i', blob, i+1)[0]
        tgt = tva + i + 5 + rel
        if tgt in TARGETS:
            callers.setdefault(tgt, set()).add(tva + i)
        i += 1

print('loading script.json ...')
s = json.load(open(SCRIPT, encoding='utf-8'))
addrs = sorted(((m['Address'], m['Name']) for m in s['ScriptMethod']), key=lambda t: t[0])
keys = [a for a, _ in addrs]

def name_of(rva):
    i = bisect.bisect_right(keys, rva) - 1
    if i < 0:
        return None
    a, nm = addrs[i]
    return nm if a == rva else '%s + 0x%X' % (nm, rva - a)

print()
for tgt in sorted(TARGETS):
    sites = callers.get(tgt, set())
    print('=== %s : %d direct call site(s)' % (TARGETS[tgt], len(sites)))
    for c in sorted(sites):
        print('   0x%-9X %s' % (c, name_of(c)))
    print()

if not callers:
    print('=> No managed code constructs or reads this message directly.')
    print('   It is reachable only through the generic message dispatcher.')
