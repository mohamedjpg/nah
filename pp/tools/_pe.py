"""Map RVAs in GameAssembly.dll and look for textbook PCG32 constants."""
import struct, sys

PATH = r'D:\tools2\dumpss\robrun\newasmbly\GameAssembly.dll'
data = open(PATH, 'rb').read()
print('size', len(data))

e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
assert data[e_lfanew:e_lfanew+4] == b'PE\0\0'
nsec = struct.unpack_from('<H', data, e_lfanew+6)[0]
optsz = struct.unpack_from('<H', data, e_lfanew+0x14)[0]
sec = e_lfanew + 24 + optsz

sections = []
for i in range(nsec):
    o = sec + i*40
    name = data[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o+8)
    sections.append((name, vaddr, vsize, raddr, rsize))
    print('%-10s va=0x%08X vsz=0x%08X raw=0x%08X rsz=0x%08X' % (name, vaddr, vsize, raddr, rsize))

def rva_to_off(rva):
    for name, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None

def off_to_rva(off):
    for name, vaddr, vsize, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return None

MULT = 6364136223846793005
INC  = 1442695040888963407
print()
print('PCG32 default multiplier 0x%016X' % MULT)
print('PCG32 default increment  0x%016X' % INC)

for label, val in (('multiplier', MULT), ('increment', INC)):
    pat = struct.pack('<Q', val)
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    print()
    print('%s: %d little-endian hits' % (label, len(hits)))
    for h in hits[:20]:
        r = off_to_rva(h)
        print('   file 0x%08X  rva %s' % (h, hex(r) if r else 'n/a'))
