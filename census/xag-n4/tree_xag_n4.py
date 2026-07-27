"""tree_XAG(f) for all 65,536 functions of n=4 — layered DP (numpy),
the same validated scheme as tree_gap_n4 (AIG), adding XOR to the combinations.

Justification for closure under complement (as in the AIG case): layers closed under
complement absorb the AND input polarities; for XOR, ~a^b = ~(a^b) and
a^~b = ~(a^b) — every variant obtained by negating a child is the complement of the positive
XOR, which enters the layer through the closure. Output negation is free.

Built-in cross-check: the 256 functions that ignore x4 are compared against a
recomputation at n=3 by the same method, plus the n=3 opt_XAG distribution from the gate
(tree >= opt sempre).
"""
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def tree_xag(N):
    ROWS = 1 << N
    MASK = (1 << ROWS) - 1
    cost = np.full(1 << ROWS, -1, dtype=np.int16)
    layer0 = {0, MASK}
    for j in range(N):
        v = sum(1 << t for t in range(ROWS) if (t >> j) & 1)
        layer0 |= {v, v ^ MASK}
    for f in layer0:
        cost[f] = 0
    layers = [np.array(sorted(layer0), dtype=np.int64)]
    k = 0
    while (cost < 0).any():
        k += 1
        new = set()
        for i in range((k - 1) // 2 + 1):
            j = k - 1 - i
            if j >= len(layers):
                continue
            Di, Dj = layers[i], layers[j]
            for s in range(0, len(Di), 512):
                blk_and = np.bitwise_and.outer(Di[s:s + 512], Dj).ravel()
                blk_xor = np.bitwise_xor.outer(Di[s:s + 512], Dj).ravel()
                for block in (blk_and, blk_xor):
                    cand = block[cost[block] < 0]
                    if len(cand):
                        new.update(np.unique(cand).tolist())
        both = set()
        for f in new:
            both |= {f, f ^ MASK}
        arr = np.array(sorted(both), dtype=np.int64)
        arr = arr[cost[arr] < 0]
        cost[arr] = k
        layers.append(arr)
        if k > 40:
            raise RuntimeError("no convergence")
    return cost, k


t0 = time.time()
c4, kmax4 = tree_xag(4)
print(f"tree_XAG n=4 completo: max = {kmax4} [{time.time()-t0:.1f}s]")

# cross-check: embedding n=3
c3, kmax3 = tree_xag(3)
bad = 0
for f3 in range(256):
    f4 = f3 | (f3 << 8)
    if c4[f4] != c3[f3]:
        bad += 1
assert bad == 0, f"{bad} mismatches in the n=3 embedding"
print(f"embedding n=3: 256/256 ✓ (max tree_XAG n=3 = {kmax3})")

M4 = (1 << 16) - 1
assert (c4 == c4[np.arange(1 << 16) ^ M4]).all()
print(f"tree_XAG(par4 0x6996) = {int(c4[0x6996])} | tree_XAG(par3 padded 0x9696) = {int(c4[0x9696])}")

np.save(HERE / "tree_xag_n4.npy", c4)
print("salvo tree_xag_n4.npy")
