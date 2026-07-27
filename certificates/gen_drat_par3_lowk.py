"""Generates UNSAT DRAT proofs for parity-3 in the AIG encoder at k=1,2,3,4, completing the
chain opt(par3) >= 6 (the par3_k5 certificate already exists). Closes finding C1/REV-0017 (Codex):
the encoder is normalized exact-size (not "at most k"), so opt>=6 requires UNSAT
at EVERY k=1..5, not only k=5.

Verificacao drat-trim: rodar separadamente (drat-trim par3_k{k}.cnf par3_k{k}.drat).
"""
import sys, subprocess, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "encoders"))
from aig_exact import AIGEncoder

N, ROWS = 3, 8
PAR3 = sum((bin(t).count("1") & 1) << t for t in range(ROWS))
CERTS = HERE  # in this layout the certificates sit alongside the generators
print(f"par3 tt = {PAR3:#04x}")

for k in [1, 2, 3, 4]:
    enc = AIGEncoder(N, k, PAR3).build()
    empty = any(len(c) == 0 for c in enc.clauses)
    cnf_path = os.path.join(CERTS, f"par3_k{k}.cnf")
    with open(cnf_path, "w") as f:
        f.write(f"p cnf {enc.nvars} {len(enc.clauses)}\n")
        for cl in enc.clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")
    if empty:
        # Syntactic UNSAT: the CNF contains an empty clause -> unsatisfiable by inspection,
        # with no solver or DRAT needed.
        ncnf = hashlib.sha256(open(cnf_path, "rb").read()).hexdigest()[:16]
        print(f"k={k}: SYNTACTIC UNSAT (empty clause in the CNF; no solver/DRAT). cnf sha[:16]={ncnf}")
        continue
    drat_path = os.path.join(CERTS, f"par3_k{k}.drat")
    p = subprocess.run(["kissat", "-q", cnf_path, drat_path], capture_output=True, text=True)
    res = {10: "SAT", 20: "UNSAT"}.get(p.returncode, f"RC{p.returncode}")
    if res != "UNSAT":
        print(f"k={k}: {res} (!!! esperava UNSAT)")
        continue
    dh = hashlib.sha256(open(drat_path, "rb").read()).hexdigest()[:16]
    ch = hashlib.sha256(open(cnf_path, "rb").read()).hexdigest()[:16]
    print(f"k={k}: UNSAT, drat {os.path.getsize(drat_path)} bytes, drat_sha[:16]={dh}, cnf_sha[:16]={ch}")
