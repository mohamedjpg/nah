"""Analyse the recorded round: is the payload encrypted, or just binary?"""
import struct, math, os, glob

cands = []
for pat in ('**/*.pcapng', '**/*.pcap', '**/*.etl'):
    cands += glob.glob(pat, recursive=True)
cands = [c for c in cands if os.path.getsize(c) > 10000]
print('captures found:')
for c in cands:
    print('   %-60s %d bytes' % (c, os.path.getsize(c)))
if not cands:
    raise SystemExit('no capture found')

path = max(cands, key=os.path.getsize)
print('\nanalysing', path)

data = open(path, 'rb').read()

# --- minimal pcapng walker -------------------------------------------------
packets = []
linktype = None
off = 0
n = len(data)
while off + 12 <= n:
    btype, blen = struct.unpack_from('<II', data, off)
    if blen < 12 or off + blen > n:
        break
    body = data[off+8:off+blen-4]
    if btype == 0x0A0D0D0A:            # Section Header
        pass
    elif btype == 0x00000001:          # Interface Description
        if len(body) >= 8:
            linktype = struct.unpack_from('<H', body, 0)[0]
    elif btype == 0x00000006:          # Enhanced Packet
        if len(body) >= 20:
            cap = struct.unpack_from('<I', body, 12)[0]
            packets.append(body[20:20+cap])
    elif btype == 0x00000003:          # Simple Packet
        if len(body) >= 4:
            orig = struct.unpack_from('<I', body, 0)[0]
            packets.append(body[4:4+orig])
    off += blen

print('linktype:', linktype, ' packets:', len(packets))

def entropy(b):
    if not b:
        return 0.0
    freq = [0]*256
    for x in b:
        freq[x] += 1
    e = 0.0
    for f in freq:
        if f:
            p = f/len(b)
            e -= p*math.log2(p)
    return e

print()
print('%-6s %-6s %-8s %-8s' % ('idx', 'len', 'entropy', 'verdict'))
sizes = {}
for i, p in enumerate(packets[:400]):
    sizes[len(p)] = sizes.get(len(p), 0) + 1
    if i < 25:
        e = entropy(p)
        print('%-6d %-6d %-8.3f %s' % (i, len(p), e,
              'ENCRYPTED/compressed' if e > 7.5 else ('structured' if e > 4 else 'plaintext-ish')))

print()
print('packet size histogram (top 12):')
for sz, cnt in sorted(sizes.items(), key=lambda kv: -kv[1])[:12]:
    print('   %6d bytes x %d' % (sz, cnt))

# entropy across all payload bytes
allb = b''.join(packets)
print()
print('overall payload bytes: %d   entropy: %.4f bits/byte' % (len(allb), entropy(allb)))
print('=> ~8.0 means ciphertext or compressed; ~4-6 means structured binary.')
