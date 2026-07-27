"""
EXP-GATE-0001 — Run of the pre-registered qualification gate (proposal v5).

G3: semantic validation of the encoder — cross-check against independent enumeration
    (n=2 complete; n=3 complete up to k=3, in both directions).
G1: an already-solved NPN-4 class — SAT at k=opt, circuit decoded and
    verified by SIMULATION against the truth table.
G2: same class — UNSAT at k=opt−1 with kissat + a DRAT proof verified
    by drat-trim (an independent checker).

Pre-registered budget: 4h wall-clock per instance; overrun = gate FAILURE.
"""

import csv
import os
import subprocess
import sys
import time
from pathlib import Path

from aig_exact import opt_via_sat, solve_k, trivial_opt, AIGEncoder, verify_circuit
from enumerate_aig import enumerate_opts

HERE = Path(__file__).parent
BUDGET_S = 4 * 3600
KISSAT = os.environ.get("KISSAT", "kissat")
DRAT_TRIM = os.environ.get("DRAT_TRIM", "drat-trim")


def g3():
    print("=== G3 — semantic validation of the encoder vs independent enumeration ===")
    t0 = time.time()
    # n=2 complete (all 16 functions, exact opt by enumeration up to 3 gates)
    enum2 = enumerate_opts(2, 4)
    assert len(enum2) == 16, f"n=2 enumeration incomplete: {len(enum2)}"
    for tt, opt_enum in sorted(enum2.items()):
        opt_enc = opt_via_sat(2, tt, kmax=5)
        assert opt_enc == opt_enum, f"n=2 tt={tt:#06x}: encoder={opt_enc} enum={opt_enum}"
    print(f"  n=2: 16/16 functions — encoder == enumeration (max opt = {max(enum2.values())})")

    # n=3 up to k=3, in BOTH directions
    enum3 = enumerate_opts(3, 3)
    checked_le3 = 0
    for tt, opt_enum in sorted(enum3.items()):
        opt_enc = opt_via_sat(3, tt, kmax=3)
        assert opt_enc == opt_enum, f"n=3 tt={tt:#06x}: encoder={opt_enc} enum={opt_enum}"
        checked_le3 += 1
    # reverse direction: functions NOT reachable with <=3 gates => encoder UNSAT for k<=3
    unreachable = [tt for tt in range(256) if tt not in enum3]
    for tt in unreachable:
        assert not trivial_opt(3, tt)
        for k in (1, 2, 3):
            sat, _ = solve_k(3, tt, k)
            assert not sat, f"n=3 tt={tt:#06x}: encoder SAT at k={k}, enumeration says unreachable"
    print(f"  n=3: {checked_le3} functions with opt<=3 checked + {len(unreachable)} unreachable ones confirmed UNSAT (k=1..3)")
    print(f"  G3: PASSED ({time.time()-t0:.1f}s)")


def pick_class(target_opt=7):
    rows = list(csv.DictReader(open(HERE / "npn4_opt_aig.csv")))
    for r in rows:
        if r["status"] == "exact" and int(r["opt_aig"]) == target_opt:
            return r["npn_rep_hex"], int(r["npn_rep_dec"]), int(r["opt_aig"])
    raise SystemExit("no exact class with that opt")


def g1(tt, opt, hexname):
    print(f"=== G1 — SAT at k={opt} for class {hexname} (catalogue: opt={opt}) ===")
    t0 = time.time()
    sat, circ = solve_k(4, tt, opt, return_circuit=True)
    dt = time.time() - t0
    assert dt < BUDGET_S, f"budget overrun: {dt:.0f}s"
    assert sat, f"G1 FAILURE: UNSAT at k={opt} — contradicts the catalogue OR the encoder is wrong"
    gates, op = circ
    assert verify_circuit(4, tt, gates, op), "G1 FAILURE: circuit does not verify by simulation"
    print(f"  SAT at k={opt}; {len(gates)}-gate circuit VERIFIED BY SIMULATION ({dt:.1f}s)")
    print(f"  circuit: {gates} out_inv={op}")
    return dt


def g2(tt, opt, hexname):
    k = opt - 1
    print(f"=== G2 — UNSAT at k={k} with kissat + DRAT + drat-trim ===")
    enc = AIGEncoder(4, k, tt).build()
    cnf = HERE / f"g2_{hexname}_k{k}.cnf"
    proof = HERE / f"g2_{hexname}_k{k}.drat"
    enc.to_dimacs(cnf)
    print(f"  CNF: {enc.nvars} vars, {len(enc.clauses)} clauses")
    t0 = time.time()
    r = subprocess.run([KISSAT, str(cnf), str(proof)], capture_output=True, text=True,
                       timeout=BUDGET_S)
    dt = time.time() - t0
    # kissat: exit 10 = SAT, 20 = UNSAT
    assert r.returncode == 20, f"G2 FAILURE: kissat returned {r.returncode} (expected UNSAT=20)"
    print(f"  kissat: UNSAT in {dt:.1f}s; DRAT proof: {proof.stat().st_size} bytes")
    t1 = time.time()
    v = subprocess.run([DRAT_TRIM, str(cnf), str(proof)], capture_output=True, text=True,
                       timeout=BUDGET_S)
    ok = "s VERIFIED" in v.stdout
    assert ok, f"G2 FAILURE: drat-trim did not verify:\n{v.stdout[-500:]}"
    print(f"  drat-trim: s VERIFIED ({time.time()-t1:.1f}s) — independent checker")
    return dt


if __name__ == "__main__":
    g3()
    hexname, dec, opt = pick_class(target_opt=7)
    # truth table of the representative: the decimal integer in the CSV IS the 16-bit truth table
    tt = dec
    print(f"\nClass chosen for G1/G2: {hexname} (tt={tt:#06x}, catalogue opt={opt})")
    t_g1 = g1(tt, opt, hexname)
    t_g2 = g2(tt, opt, hexname)
    print(f"\n*** GATE: G1 PASSED ({t_g1:.1f}s) · G2 PASSED ({t_g2:.1f}s) · G3 PASSED ***")
