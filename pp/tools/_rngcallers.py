"""Find callers of the RNG functions and resolve them to managed method names.

Scans .text for E8 rel32 calls whose target is one of the PCG32 / RandomUtils /
RandomModel entry points, then maps the caller RVA back to a method name using
script.json's ScriptMethod table.
"""
import json, struct, re

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

def rva_to_off(rva):
    for name, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None

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
    0x62685e0: 'PcgRandom..ctor',
    0x6268540: 'PcgRandom.GetUInt',
    0x6268590: 'PcgRandom.Step',
}

# scan .text only
tname, tva, tvsz, traw, trsz = [s for s in sections if s[0] == '.text'][0]
text = data[traw:traw+trsz]
print('.text rva 0x%X size 0x%X' % (tva, trsz))

callers = {}   # target_rva -> set of caller rvas
i = 0
n = len(text)
while True:
    i = text.find(b'\xe8', i)
    if i < 0 or i + 5 > n:
        break
    rel = struct.unpack_from('<i', text, i+1)[0]
    tgt = tva + i + 5 + rel
    if tgt in TARGETS:
        callers.setdefault(tgt, set()).add(tva + i)
    i += 1

print()
total = 0
for tgt in sorted(callers):
    print('=== %-40s (0x%X): %d call sites' % (TARGETS[tgt], tgt, len(callers[tgt])))
    total += len(callers[tgt])
print('total call sites:', total)

# save for name resolution
json.dump({str(k): sorted(v) for k, v in callers.items()}, open(r'src\pp\offsets\rng_callers.json', 'w'), indent=1)
print('wrote src/pp/offsets/rng_callers.json')
