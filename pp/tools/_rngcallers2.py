"""Find callers of RNG entry points inside the il2cpp section, then name them."""
import json, struct

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
    0x394d650: 'PCG32.GenerateState',
    0x394d870: 'PCG32.Step',
    0x394d790: 'PCG32.Next/GetNextUInt/GetNextInt',
    0x394d7e0: 'PCG32.GetNextULong/GetNextLong',
    0x394d730: 'PCG32.GetNextFloat',
    0x394d670: 'PCG32.GetNextDouble',
    0x4a3e3c0: 'RandomUtils.GenerateSeed',
    0x4a3e450: 'RandomUtils.GetNextInt',
    0x4a3e460: 'RandomUtils.GetNextLong',
    0x4a3e440: 'RandomUtils.GetNextFloat',
    0x4a3e430: 'RandomUtils.GetNextDouble',
    0x48d7fd0: 'RandomModel.GetNextLong',
    0x48d7f10: 'RandomModel.GetNextInt',
    0x48d7e50: 'RandomModel.GetNextFloat',
    0x48d7d80: 'RandomModel.CheckProbability',
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

print('total call sites:', sum(len(v) for v in callers.values()))
for tgt in sorted(callers):
    print('%-42s %d' % (TARGETS[tgt], len(callers[tgt])))

# resolve caller RVA -> method name using script.json
print()
print('loading script.json ...')
s = json.load(open(SCRIPT, encoding='utf-8'))
meth = s['ScriptMethod']
print('ScriptMethod entries:', len(meth))

# build sorted list of (address, name)
addrs = sorted(((m['Address'], m['Name']) for m in meth), key=lambda t: t[0])
import bisect
keys = [a for a, _ in addrs]

def name_of(rva):
    i = bisect.bisect_right(keys, rva) - 1
    if i < 0:
        return None
    a, nm = addrs[i]
    return nm if a == rva else '%s + 0x%X' % (nm, rva - a)

out = {}
for tgt, sites in callers.items():
    print()
    print('=== callers of %s ===' % TARGETS[tgt])
    for c in sorted(sites):
        nm = name_of(c)
        print('   0x%-9X %s' % (c, nm))
        out.setdefault(TARGETS[tgt], []).append({'rva': c, 'name': nm})

json.dump(out, open(r'src\pp\offsets\rng_callers.json', 'w'), indent=1)
print()
print('wrote src/pp/offsets/rng_callers.json')
