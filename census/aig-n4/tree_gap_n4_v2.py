"""Second INDEPENDENT implementation of tree(f) at n=4 (for claim 0026):
global Bellman fixed point — relaxes cost[f] = min(cost[f], 1 + cost[a] + cost[b])
over ALL pairs (a,b) with f = a AND b, sweeping to a fixed point, WITHOUT layers.

Structural differences from tree_gap_n4.py (layered BFS):
- different discovery order (global relaxation, not a frontier);
- polarities handled EXPLICITLY: for each pair (a,b) it relaxes all 4 combinations
  (a&b, a&~b, ~a&b, ~a&~b) and the output complement — NO "layer closed under
  complement" step (if that absorption were wrong, this version would diverge);
- initial cost INF (int32) instead of a -1 sentinel.

Compares all 65,536 cells against v1, recomputed on the spot.
"""
import time

import numpy as np

N, ROWS = 4, 16
MASK = (1 << ROWS) - 1
INF = np.int32(10 ** 6)

t0 = time.time()

cost = np.full(1 << ROWS, INF, dtype=np.int32)
cost[0] = cost[MASK] = 0
for j in range(N):
    v = sum(1 << t for t in range(ROWS) if (t >> j) & 1)
    cost[v] = cost[v ^ MASK] = 0

CHUNK = 256
sweep = 0
while True:
    sweep += 1
    changed = 0
    known = np.nonzero(cost < INF)[0]
    kc = cost[known]
    # sort by cost to relax cheapest-first (speeds convergence, does not move the fixed point)
    order = np.argsort(kc, kind="stable")
    known, kc = known[order], kc[order]
    for s in range(0, len(known), CHUNK):
        A = known[s:s + CHUNK]
        cA = kc[s:s + CHUNK]
        for a, ca in zip(A.tolist(), cA.tolist()):
            newc = 1 + ca + kc  # cost of the AND with each known b
            for aa in (a, a ^ MASK):
                for bvec in (known, known ^ MASK):
                    f = np.bitwise_and(aa, bvec)
                    # relax f and ~f (output negation is free)
                    for g in (f, f ^ MASK):
                        upd = newc < cost[g]
                        if upd.any():
                            np.minimum.at(cost, g[upd], newc[upd])
                            changed += int(upd.sum())
    print(f"sweep {sweep}: {changed} relaxations [{time.time() - t0:.0f}s]", flush=True)
    if changed == 0:
        break

assert (cost < INF).all(), "unreachable functions — bug"
print(f"fixed point in {sweep} sweeps; max tree = {int(cost.max())} [{time.time() - t0:.0f}s]")

# --- recompute v1 (layered BFS) and compare cell by cell ---
c1 = np.full(1 << ROWS, -1, dtype=np.int16)
layer0 = {0, MASK}
for j in range(N):
    v = sum(1 << t for t in range(ROWS) if (t >> j) & 1)
    layer0 |= {v, v ^ MASK}
for f in layer0:
    c1[f] = 0
layers = [np.array(sorted(layer0), dtype=np.int64)]
k = 0
while (c1 < 0).any():
    k += 1
    new = set()
    for i in range((k - 1) // 2 + 1):
        j = k - 1 - i
        if j >= len(layers):
            continue
        Di, Dj = layers[i], layers[j]
        for s in range(0, len(Di), 512):
            block = np.bitwise_and.outer(Di[s:s + 512], Dj).ravel()
            cand = block[c1[block] < 0]
            if len(cand):
                new.update(np.unique(cand).tolist())
    both = set()
    for f in new:
        both |= {f, f ^ MASK}
    arr = np.array(sorted(both), dtype=np.int64)
    arr = arr[c1[arr] < 0]
    c1[arr] = k
    layers.append(arr)

diff = np.nonzero(cost.astype(np.int64) != c1.astype(np.int64))[0]
if len(diff):
    for f in diff[:10]:
        print(f"DIVERGENCE {f:#06x}: v2={int(cost[f])} v1={int(c1[f])}")
    raise SystemExit(f"FAILED: {len(diff)} cells diverge")
print(f"v2 (Bellman) == v1 (layers) on ALL 65,536 cells ✓")
print(f"tree(0x6996) = {int(cost[0x6996])} | [{time.time() - t0:.0f}s total]")
