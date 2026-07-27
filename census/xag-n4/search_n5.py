"""n=5 search for a unit-gap SEPARATOR in XAG: a 5-variable function f with
gap_XAG(f) = tree_XAG(f) - opt_XAG(f) >= 2 (open question #1 of the technote).

At n<=4, gap_XAG is in {0,1} (empirically). In XAG there is NO trivial decomposition f=1&f
forcing gap<=1 as in AIG, so gap>=2 is possible a priori. A separator refines the basis-
dependence; its absence over a large sample is evidence for the conjecture.

Strategy: generate LOW-opt candidates (where SAT is feasible) from random XAG circuits
with sharing/reconvergence; for each tt on 5 essential variables:
  opt = opt_XAG(f) by SAT in ASCENDING search (k=1,2,...; timeout; opt>kmax => discard);
  tree = tree_XAG(f) by ASCENDING search in k starting from opt (formula=True, timeout); the
    PRIMEIRO k SAT e tree. gap = tree - opt.
  gap >= 2 => SEPARATOR; gap in {0,1} => gap0/gap1; a timeout on opt or on tree => inconclusive.

IMPORTANT (correction of 2026-07-12; see Appendix B of the paper): an earlier version tested the
formula at opt+1 IN ISOLATION and declared UNSAT a separator. That is WRONG for the
normalized exact-size encoder — UNSAT at EXACTLY opt+1 means "there is no formula
of opt+1 gates", NOT tree>=opt+2 (a formula of some other size may exist). The bug produced a
falso positivo em parity-5 (0x69969669, linear, gap 0). A busca ASCENDENTE de opt corrige.

Uso: python3 search_n5.py <worker_id> <n_workers>
Output: search_n5_w<id>.csv (all f) + sep_n5_w<id>.jsonl (separators). Resumes by tt.
"""
import sys, os, csv, json, time, random, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xag_exact import opt_via_sat, solve_k, simulate, tt_bit

N = 5
ROWS = 1 << N
MASK = (1 << ROWS) - 1
TIMEOUT = 20  # s per SAT call


def circuit_tt(gates, out_pol):
    """32-bit tt of the XAG circuit (n=5)."""
    tt = 0
    for t in range(ROWS):
        if simulate(N, gates, out_pol, t):
            tt |= 1 << t
    return tt


def essential_all5(tt):
    """Does f depend on all 5 variables? (cofactor xj=0 != cofactor xj=1 on each axis)"""
    for j in range(N):
        diff = False
        for t in range(ROWS):
            if not ((t >> j) & 1) and ((tt >> t) & 1) != ((tt >> (t | (1 << j))) & 1):
                diff = True
                break
        if not diff:
            return False
    return True


def random_candidate(rng, kmin=4, kmax=8):
    """Random XAG circuit biased towards reconvergence (gate reuse)."""
    k = rng.randint(kmin, kmax)
    gates = []
    for i in range(1, k + 1):
        node = N + i
        prev = list(range(1, node))
        # bias: with prob 0.6 pick at least one predecessor among already-created gates
        gate_nodes = [p for p in prev if p > N]
        if gate_nodes and rng.random() < 0.6:
            a = rng.choice(gate_nodes)
            b = rng.choice([p for p in prev if p != a])
        else:
            a, b = rng.sample(prev, 2)
        if a > b:
            a, b = b, a
        typ = rng.choice(["and", "xor", "xor"])  # XOR bias (non-linear structure)
        pa, pb = (rng.randint(0, 1), rng.randint(0, 1)) if typ == "and" else (0, 0)
        gates.append((typ, a, pa, b, pb))
    return circuit_tt(gates, rng.randint(0, 1))


def main():
    wid, nw = int(sys.argv[1]), int(sys.argv[2])
    out_csv = os.path.join(HERE, f"search_n5_w{wid:02d}.csv")
    out_sep = os.path.join(HERE, f"sep_n5_w{wid:02d}.jsonl")
    seen = set()
    if os.path.exists(out_csv):
        for r in csv.DictReader(open(out_csv)):
            seen.add(int(r["tt"]))
    rng = random.Random(90210 + wid)
    t0 = time.time()
    mode = "a" if seen else "w"
    n_done = n_sep = n_gap1 = n_gap0 = n_inc = 0
    with open(out_csv, mode, newline="") as fc, open(out_sep, "a") as fs:
        w = csv.DictWriter(fc, fieldnames=["tt", "opt", "tree", "gap", "verdict", "t_sec"])
        if not seen:
            w.writeheader()
        # loop up to 1e9 candidates (backstop); in practice it runs until we kill it
        for _ in range(10**9):
            tt = random_candidate(rng)
            if tt in seen or tt in (0, MASK):
                continue
            if not essential_all5(tt):
                continue
            seen.add(tt)
            t1 = time.time()
            try:
                opt = opt_via_sat(N, tt, kmax=12, timeout=TIMEOUT, verify=False)
            except subprocess.TimeoutExpired:
                continue  # opt needs an expensive k (kissat > TIMEOUT) — out of reach
            if opt is None:
                continue  # opt > kmax — out of reach
            # tree_XAG by ASCENDING search from opt (solve_k in formula mode,
            # validated by gate G-T3). The first SAT k = tree. gap = tree - opt.
            # (parity and linear functions are SAT already at k=opt => gap 0, no false positive.)
            tree = None; timed_out = False
            for kk in range(opt, opt + 6):
                try:
                    sat, _ = solve_k(N, tt, kk, timeout=TIMEOUT, formula=True)
                except subprocess.TimeoutExpired:
                    timed_out = True; break
                if sat:
                    tree = kk; break
            if tree is not None:
                gap = tree - opt
                verdict = "SEPARATOR" if gap >= 2 else ("gap1" if gap == 1 else "gap0")
            elif timed_out:
                verdict, gap = "inconclusive", -1
            else:
                verdict, gap, tree = "SEPARATOR", 6, opt + 6  # tree>opt+5 (gap>=6, forte)
            n_done += 1
            if verdict == "SEPARATOR":
                n_sep += 1
                fs.write(json.dumps({"tt": tt, "tt_hex": f"{tt:#010x}", "opt": opt,
                                     "tree": tree, "gap": gap}) + "\n")
                fs.flush()
                print(f"[w{wid}] *** SEPARATOR *** tt={tt:#010x} opt={opt} tree={tree} gap={gap}", flush=True)
            elif verdict == "gap1":
                n_gap1 += 1
            elif verdict == "gap0":
                n_gap0 += 1
            else:
                n_inc += 1
            w.writerow({"tt": tt, "opt": opt, "tree": tree if tree is not None else "",
                        "gap": gap, "verdict": verdict, "t_sec": f"{time.time()-t1:.2f}"})
            fc.flush()
            if n_done % 100 == 0:
                print(f"[w{wid}] {n_done} f (sep {n_sep}, gap1 {n_gap1}, gap0 {n_gap0}, "
                      f"inc {n_inc}) [{time.time()-t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
