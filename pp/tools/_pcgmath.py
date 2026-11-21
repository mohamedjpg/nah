"""Decode the PCG32 math from the bytes to state it precisely."""
import struct

MULT = 0x5851F42D4C957F2D
INC_DEFAULT = 0x14057B7EF767814F
GEN_ADD = 0x1A08EE1184BA6D32

print('PCG32 multiplier        = 0x%016X' % MULT)
print('PCG32 default increment = 0x%016X  (odd: %s)' % (INC_DEFAULT, INC_DEFAULT & 1))
print('GenerateState addend    = 0x%016X  (odd: %s)' % (GEN_ADD, GEN_ADD & 1))
print()
print('GenerateState(seed) = seed * MULT + 0x%016X' % GEN_ADD)
print()
print('Next(state):')
print('  nextState = state * MULT + 0x%016X      <- default PCG increment' % INC_DEFAULT)
print('  xorshifted = (state >> 45) ^ (state >> 27)')
print('  rot = state >> 59')
print('  return ror32(xorshifted, rot)')
print()
print('=> textbook PCG32 XSH-RR. Deterministic, stateless, caller threads state.')

# demonstrate determinism
def next_pcg(state):
    ns = (state * MULT + INC_DEFAULT) & 0xFFFFFFFFFFFFFFFF
    xorshifted = (((state >> 45) ^ (state >> 27)) & 0xFFFFFFFF)
    rot = state >> 59
    return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF, ns

s = 0x1234567890ABCDEF
print()
print('sample stream from seed 0x%X:' % s)
for i in range(6):
    v, s = next_pcg(s)
    print('   %10u   -> pocket %d' % (v, v % 37))
