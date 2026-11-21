"""Dump raw bytes of the RNG functions so the algorithm can be verified."""
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

def rva_to_off(rva):
    for name, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None

FUNCS = [
    ('PCG32.GenerateState', 0x394d650, 96),
    ('PCG32.Step',          0x394d870, 96),
    ('PCG32.Next',          0x394d790, 96),
    ('RandomUtils..cctor',  0x4a3e470, 80),
    ('RandomUtils.GenerateSeed', 0x4a3e3c0, 80),
]

for name, rva, n in FUNCS:
    off = rva_to_off(rva)
    blob = data[off:off+n]
    print('=== %s  rva 0x%X' % (name, rva))
    for i in range(0, len(blob), 16):
        chunk = blob[i:i+16]
        hx = ' '.join('%02X' % b for b in chunk)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print('  +%-3X %-47s %s' % (i, hx, asc))
    print()
