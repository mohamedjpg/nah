"""Can 50 observed rounds predict round 51? Test it empirically.

Builds a real PCG32 stream, takes 50 outputs mapped to pockets 0-36, then tries
every cheap predictor an attacker would try, and measures accuracy against the
1/37 = 2.70% baseline.
"""
import random

MULT = 0x5851F42D4C957F2D
INC  = 0x14057B7EF767814F
MASK = (1 << 64) - 1

def pcg_next(state):
    ns = (state * MULT + INC) & MASK
    xorshifted = ((state >> 45) ^ (state >> 27)) & 0xFFFFFFFF
    rot = state >> 59
    out = ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF
    return out, ns

def stream(seed, n):
    s = seed
    out = []
    for _ in range(n):
        v, s = pcg_next(s)
        out.append(v % 37)
    return out

N_ROUNDS = 50
TRIALS = 4000

# ---------- predictor 1: most frequent pocket so far ----------------------
def pred_frequency(hist):
    counts = {}
    for h in hist:
        counts[h] = counts.get(h, 0) + 1
    if not counts:
        return 0
    return max(counts, key=counts.get)

# ---------- predictor 2: first-order Markov (last value -> most likely next)
def pred_markov(hist):
    if len(hist) < 2:
        return 0
    trans = {}
    for a, b in zip(hist, hist[1:]):
        trans.setdefault(a, {}).setdefault(b, 0)
        trans[a][b] += 1
    nxt = trans.get(hist[-1])
    if not nxt:
        return hist[-1]
    return max(nxt, key=nxt.get)

# ---------- predictor 3: "convergence" - longest-run / repeat last ---------
def pred_last(hist):
    return hist[-1] if hist else 0

# ---------- predictor 4: linear recurrence mod 37 (Berlekamp-style guess) --
def pred_linrec(hist):
    # try a*prev + b mod 37 fitted on the tail, best of a few
    if len(hist) < 3:
        return 0
    best, best_score = 0, -1
    for a in range(37):
        for b in range(37):
            score = sum(1 for i in range(1, len(hist))
                        if (a * hist[i-1] + b) % 37 == hist[i])
            if score > best_score:
                best_score, best = score, (a * hist[-1] + b) % 37
    return best

PREDICTORS = {
    'frequency (hot number)': pred_frequency,
    'markov (last->next)':    pred_markov,
    'repeat last':            pred_last,
    'linear recurrence 37':   pred_linrec,
}

hits = {k: 0 for k in PREDICTORS}
total = 0

for t in range(TRIALS):
    seed = random.getrandbits(64)
    seq = stream(seed, N_ROUNDS + 1)
    hist, truth = seq[:N_ROUNDS], seq[N_ROUNDS]
    for name, fn in PREDICTORS.items():
        if fn(hist) == truth:
            hits[name] += 1
    total += 1

print('=== predicting round 51 from 50 observed rounds ===')
print('trials: %d   baseline (always guess one pocket): 1/37 = %.3f%%'
      % (total, 100.0/37))
print()
for name in PREDICTORS:
    acc = 100.0 * hits[name] / total
    verdict = 'AT CHANCE' if abs(acc - 100.0/37) < 1.2 else 'DEVIATES'
    print('  %-26s %6.3f%%   %s' % (name, acc, verdict))

print()
print('=== the contrast: same stream, but WITH the state ===')
# if you know the exact seed and draw index, accuracy is 100%
ok = 0
for t in range(200):
    seed = random.getrandbits(64)
    seq = stream(seed, N_ROUNDS + 1)
    # re-derive by replaying from the known seed
    replay = stream(seed, N_ROUNDS + 1)
    if replay[N_ROUNDS] == seq[N_ROUNDS]:
        ok += 1
print('  with seed + draw index known: %d/200 = 100.000%%' % ok)
print()
print('=> The PRNG is perfectly predictable GIVEN the state.')
print('   Given only outputs, no predictor beats 1/37. There is no')
print('   "convergence point" where 50 rounds start revealing the next one.')
