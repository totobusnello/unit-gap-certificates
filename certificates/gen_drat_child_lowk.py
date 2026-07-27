"""Completes the DRAT chain for the child h=(x1⊕x2)∧¬x3 (opt=4): generates UNSAT DRAT at k=1,2
(k=3 already exists as h_child_k3). Closes finding REV-0017-r2/Codex I2: in the
exact-size, opt(h)≥4 requires UNSAT at k=1,2,3, not only k=3.
"""
import sys, subprocess, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "encoders"))
from aig_exact import AIGEncoder

N, ROWS = 3, 8
# h = (x1 xor x2) and (not x3)
H = sum(((((t & 1) ^ ((t >> 1) & 1)) & (1 - ((t >> 2) & 1)))) << t for t in range(ROWS))
CERTS = HERE  # in this layout the certificates sit alongside the generators
print(f"h child tt = {H:#04x}")

for k in [1, 2]:
    enc = AIGEncoder(N, k, H).build()
    empty = any(len(c) == 0 for c in enc.clauses)
    cnf_path = os.path.join(CERTS, f"h_child_k{k}.cnf")
    with open(cnf_path, "w") as f:
        f.write(f"p cnf {enc.nvars} {len(enc.clauses)}\n")
        for cl in enc.clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")
    if empty:
        ch = hashlib.sha256(open(cnf_path, "rb").read()).hexdigest()[:16]
        print(f"k={k}: UNSAT SINTATICO (clausula vazia). cnf sha[:16]={ch}")
        continue
    drat_path = os.path.join(CERTS, f"h_child_k{k}.drat")
    p = subprocess.run(["kissat", "-q", cnf_path, drat_path], capture_output=True, text=True)
    res = {10: "SAT", 20: "UNSAT"}.get(p.returncode, f"RC{p.returncode}")
    dh = hashlib.sha256(open(drat_path, "rb").read()).hexdigest()[:16]
    print(f"k={k}: {res}, drat {os.path.getsize(drat_path)} bytes, drat_sha[:16]={dh}")
