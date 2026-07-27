"""Re-verification by SIMULATION of the n=5 instances (closes B1/REV-0015..0017): the search
ran with verify=False (SAT models were not decoded). Here we re-decode and
simulate both the optimal circuit (opt gates) AND the formula (tree gates) of every gap1 + a sample
of gap0, confirming that they compute the tt. solve_k(return_circuit=True) performs the
simulacao internamente.
"""
import sys, os, csv, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xag_exact import solve_k

N = 5
dedup = os.path.join(HERE, "search_n5_dedup.csv")
rows = list(csv.DictReader(open(dedup)))
gap1 = [r for r in rows if r["verdict"] == "gap1"]
gap0 = [r for r in rows if r["verdict"] == "gap0"][:200]  # deterministic sample
targets = gap1 + gap0
print(f"targets: {len(gap1)} gap1 + {len(gap0)} gap0 (sample) = {len(targets)}")

ok = 0
bad = []
for i, r in enumerate(targets):
    tt, opt, tree = int(r["tt"]), int(r["opt"]), int(r["tree"])
    try:
        s_opt, _ = solve_k(N, tt, opt, return_circuit=True, timeout=30)
        s_tree, _ = solve_k(N, tt, tree, return_circuit=True, formula=True, timeout=30)
    except (subprocess.TimeoutExpired, AssertionError) as e:
        bad.append((f"{tt:#010x}", opt, tree, f"ERR:{type(e).__name__}"))
        continue
    if s_opt and s_tree:
        ok += 1
    else:
        bad.append((f"{tt:#010x}", opt, tree, f"sat_opt={s_opt} sat_tree={s_tree}"))
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(targets)} (ok {ok}, bad {len(bad)})", flush=True)

print(f"\nVERIFIED BY SIMULATION: {ok}/{len(targets)}")
if bad:
    print(f"DIVERGENCIAS ({len(bad)}): {bad[:15]}")
else:
    print("every re-decoded instance simulates the tt (opt circuit + tree formula)")
