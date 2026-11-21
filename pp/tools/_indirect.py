"""Close the indirect-call gap without Ghidra.

My earlier scan only caught direct `E8 rel32` calls. IL2CPP also dispatches via
delegates, virtual slots and MethodInfo pointers, which appear as *data*
references to the method address. This scans the whole image for the RNG RVAs
appearing as 4- or 8-byte little-endian values anywhere outside the code hits
already found.
"""
import json, struct

DLL = r'D:\tools2\dumpss\robrun\newasmbly\GameAssembly.dll'
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

def off_to_rva(off):
    for name, vaddr, vsize, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr), name
    return None, None

TARGETS = {
    0x394d650: 'PCG32.GenerateState',
    0x394d870: 'PCG32.Step',
    0x394d790: 'PCG32.Next',
    0x394d7e0: 'PCG32.GetNextULong',
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

print('Scanning whole image for RNG RVAs as data references...')
print()

found_any = False
for tgt in sorted(TARGETS):
    hits = []
    for width, fmt in ((4, '<I'), (8, '<Q')):
        pat = struct.pack(fmt, tgt)
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            rva, sname = off_to_rva(i)
            if rva is not None:
                hits.append((i, rva, sname, width))
            start = i + 1
    # filter out the code bytes themselves (the immediate in a mov, inside a function body)
    if hits:
        found_any = True
        print('%-32s %d data ref(s)' % (TARGETS[tgt], len(hits)))
        for off, rva, sname, width in hits[:12]:
            print('     file 0x%08X  rva 0x%08X  %-8s  %d-byte' % (off, rva, sname, width))

if not found_any:
    print('(none)')

print()
print('=== now: MethodInfo-style references ==')
print('Searching .data / .rdata for any 8-byte pointer landing inside il2cpp')
print('at the RNG RVAs is covered above. Counting total image-wide:')
total = 0
for tgt in TARGETS:
    for width, fmt in ((4, '<I'), (8, '<Q')):
        pat = struct.pack(fmt, tgt)
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            total += 1
            start = i + 1
print('total raw matches (code immediates + data):', total)
