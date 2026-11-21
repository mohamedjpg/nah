"""Check VA-form (preferred-base + RVA) references, which is how IL2CPP stores
MethodInfo->methodPointer and static delegate targets."""
import struct

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

PREF = 0x180000000
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
}

print('=== 8-byte VA-form references (0x180000000 + RVA) ===')
print()
any_hit = False
for tgt in sorted(TARGETS):
    va = PREF + tgt
    pat = struct.pack('<Q', va)
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        rva, sname = off_to_rva(i)
        hits.append((i, rva, sname))
        start = i + 1
    if hits:
        any_hit = True
        print('%-32s %d ref(s)' % (TARGETS[tgt], len(hits)))
        for off, rva, sname in hits[:10]:
            print('     file 0x%08X  rva 0x%08X  %s' % (off, rva, sname))

if not any_hit:
    print('(none found)')
    print()
    print('=> These RNG methods are never referenced as MethodInfo pointers or')
    print('   delegate targets either. They are called directly only.')

print()
print('=== sanity: does this scan method work at all? ===')
# pick a method we KNOW is referenced many times, e.g. RouletteModel.AddBet
for label, rva in (('RouletteModel.AddBet', 0x48E4BB0),
                   ('RouletteModel.get_WinningNumber', 0x7BB030)):
    pat = struct.pack('<Q', PREF + rva)
    n = data.count(pat)
    pat4 = struct.pack('<I', rva)
    n4 = data.count(pat4)
    print('%-34s VA-form %d, RVA-form %d' % (label, n, n4))
