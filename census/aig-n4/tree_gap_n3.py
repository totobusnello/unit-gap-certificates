"""Unit Gap check at n=3, v2: opt via encoder+kissat (enumeration blows up at k=8); tree via the correct Bellman."""
import subprocess, sys, tempfile, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "encoders"))
from aig_exact import AIGEncoder, trivial_opt
from collections import Counter

N, ROWS = 3, 8
MASK = (1 << ROWS) - 1

def opt_kissat(tt, kmax=12):
    if trivial_opt(N, tt):
        return 0
    for k in range(1, kmax + 1):
        enc = AIGEncoder(N, k, tt).build()
        if any(len(c) == 0 for c in enc.clauses):
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
            path = f.name
            f.write(f"p cnf {enc.nvars} {len(enc.clauses)}\n")
            for cl in enc.clauses:
                f.write(" ".join(map(str, cl)) + " 0\n")
        rc = subprocess.run(["kissat", "-q", path], capture_output=True).returncode
        os.unlink(path)
        if rc == 10:
            return k
        assert rc == 20, f"rc={rc}"
    return None

t0 = time.time()
opts = {f: opt_kissat(f) for f in range(256)}
print(f"opt via kissat: 256 functions in {time.time()-t0:.0f}s, max opt = {max(opts.values())}", flush=True)

INF = 10**9
tree = {f: INF for f in range(256)}
lits = [sum(((t >> j) & 1) << t for t in range(ROWS)) for j in range(N)]
for f in [0, MASK] + lits + [l ^ MASK for l in lits]:
    tree[f] = 0
changed, rounds = True, 0
while changed:
    changed = False; rounds += 1
    for a in range(256):
        va = tree[a]
        if va >= INF: continue
        for b in range(a, 256):
            vb = tree[b]
            if vb >= INF: continue
            g = a & b; c = 1 + va + vb
            for h in (g, g ^ MASK):
                if c < tree[h]:
                    tree[h] = c; changed = True
print(f"tree (correct Bellman, children = trees): {rounds} rounds", flush=True)
gaps = {f: tree[f] - opts[f] for f in range(256)}
print("gap distribution (n=3, 256 functions):", dict(sorted(Counter(gaps.values()).items())))
print(f"paridade_3 (tt=150): opt={opts[150]}, tree={tree[150]}, gap={gaps[150]}")
w = max(gaps, key=gaps.get)
print(f"pior gap: tt={w:#04x}: opt={opts[w]}, tree={tree[w]}, gap={gaps[w]}")
