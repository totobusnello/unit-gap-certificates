"""Gap at n=4: tree(f) for all 65536 functions by a layered DP (numpy),
with opt(f) from the npn4_opt_aig.csv catalogue (complete, claims 0022/0023).

Model identical to n=3 (tree_gap_n3.py): AIG, free negations on the edges and on
the output => cost(f) == cost(~f); cost 0 = constants and literals; tree = formula
(fan-out 1): f = (+-a) AND (+-b) with a,b trees => layers closed under
complemento absorvem as polaridades.

tree and opt are NPN-invariant (input permutation/negation and output negation are
free in the AIG model), so it suffices to read tree(rep) on the catalogue's 222
representatives.

Output: npn4_gap.csv (class, opt, tree, gap) + the distribution on stdout.
"""
import csv
import time
from collections import Counter
from pathlib import Path

import numpy as np

N, ROWS = 4, 16
MASK = (1 << ROWS) - 1
HERE = Path(__file__).resolve().parent
CAT = HERE.parent.parent / "encoders" / "npn4_opt_aig.csv"

t0 = time.time()

# --- cost 0: constants and literals (+ complements) ---
cost = np.full(1 << ROWS, -1, dtype=np.int16)
layer0 = {0, MASK}
for j in range(N):
    v = 0
    for t in range(ROWS):
        if (t >> j) & 1:
            v |= 1 << t
    layer0.add(v)
    layer0.add(v ^ MASK)
for f in layer0:
    cost[f] = 0
layers = [np.array(sorted(layer0), dtype=np.int64)]

# --- layers k=1..: f = a AND b, a in D[i], b in D[j], i+j = k-1 ---
CHUNK = 512
k = 0
while (cost < 0).any():
    k += 1
    new = set()
    for i in range((k - 1) // 2 + 1):
        j = k - 1 - i
        if j >= len(layers):
            continue
        Di, Dj = layers[i], layers[j]
        for s in range(0, len(Di), CHUNK):
            block = np.bitwise_and.outer(Di[s:s + CHUNK], Dj).ravel()
            cand = block[cost[block] < 0]
            if len(cand):
                new.update(np.unique(cand).tolist())
    if not new:
        # no new function in this layer; continue (there may be one at k+1)
        layers.append(np.array([], dtype=np.int64))
        if k > 40:
            raise RuntimeError("no progress up to k=40 — bug")
        continue
    both = set()
    for f in new:
        both.add(f)
        both.add(f ^ MASK)
    arr = np.array(sorted(both), dtype=np.int64)
    arr = arr[cost[arr] < 0]  # could the complement already be cheaper? no — cost(f)==cost(~f); kept anyway
    cost[arr] = k
    layers.append(arr)
    done = int((cost >= 0).sum())
    print(f"k={k}: +{len(arr)} novas (total {done}/{1 << ROWS}) [{time.time() - t0:.1f}s]", flush=True)

print(f"tree completo: max tree = {k} [{time.time() - t0:.1f}s]", flush=True)

# sanity: tree(f) == tree(~f)
alltt = np.arange(1 << ROWS, dtype=np.int64)
assert (cost[alltt] == cost[alltt ^ MASK]).all(), "tree did not close under complement"

# --- join with the opt catalogue ---
rows = list(csv.DictReader(open(CAT)))
# REV-0013 (Codex): the join must require a 100% exact catalogue, not consume
# improved_ub silently (0x1669/0x166b carried stale metadata in the CSV, since
# corrected — the k=9 DRAT proofs of claims 0022/0023 establish opt=10 exactly)
nonexact = [r["npn_rep_hex"] for r in rows if r["status"] != "exact"]
assert not nonexact, f"catalogue has non-exact rows: {nonexact}"
out_rows = []
dist = Counter()
viol = []
for r in rows:
    rep = int(r["npn_rep_dec"])
    opt = int(r["opt_aig"])
    tree = int(cost[rep])
    gap = tree - opt
    if gap < 0:
        viol.append((r["npn_rep_hex"], opt, tree))
    out_rows.append({"npn_rep_hex": r["npn_rep_hex"], "npn_rep_dec": rep,
                     "opt_aig": opt, "tree_aig": tree, "gap": gap})
    dist[gap] += 1

assert not viol, f"tree < opt at {viol[:5]} — a bug in one of the two"

with open(HERE / "npn4_gap.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["npn_rep_hex", "npn_rep_dec", "opt_aig", "tree_aig", "gap"])
    w.writeheader()
    w.writerows(out_rows)

print(f"\nGap distribution over the {len(out_rows)} NPN-4 classes:")
for g in sorted(dist):
    print(f"  gap={g}: {dist[g]} classes")
print("\nClasses attaining the maximum gap:")
gmax = max(dist)
for r in out_rows:
    if r["gap"] == gmax:
        print(f"  {r['npn_rep_hex']}: opt={r['opt_aig']} tree={r['tree_aig']} gap={r['gap']}")
print(f"\ntree(0x6996 = paridade-4) = {int(cost[0x6996])}")
print(f"[{time.time() - t0:.1f}s total]")
