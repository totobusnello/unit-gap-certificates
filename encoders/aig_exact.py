"""
EXP-GATE-0001 — AIG exact-synthesis encoder via SAT (PHASE 5 qualification gate).

Question encoded: "is there an AIG circuit with exactly k AND gates that computes f?"
AIG model (catalogue convention SRC-0019/0027): 2-input AND gates,
free inversions on any edge and on the output; size = number of AND gates.

Encoding semantics (validated in G3 against independent enumeration):
- Nodes: inputs 1..n (values fixed per truth-table row), gates n+1..n+k.
- Each gate i selects (one-hot) an option (a, pa, b, pb): operands a < b
  among earlier nodes, with polarities pa, pb.
- v[i][t] = value of gate i on row t; conditional clauses impose
  v[i][t] <-> (val(a,t) xor pa) AND (val(b,t) xor pb).
- Output = gate k with free polarity op: v[k][t] <-> (f(t) xor op).
- Symmetry breaking (sound): every gate i < k must be used by some
  later gate.
- k=0 is handled outside SAT (f constant or a literal).

RULE REV-0004: a DRAT proof certifies the CNF, not the encoding — hence G3
(cross-enumeration) and the simulation check of every SAT circuit.
"""

from itertools import combinations


def tt_bit(tt, t):
    return (tt >> t) & 1


class AIGEncoder:
    def __init__(self, n, k, tt):
        """n inputs, k AND gates, tt = truth table as a 2^n-bit integer."""
        self.n, self.k, self.tt = n, k, tt
        self.rows = 1 << n
        self.nvars = 0
        self.clauses = []
        # v[i][t] for gates i=1..k
        self.v = {(i, t): self._new() for i in range(1, k + 1) for t in range(self.rows)}
        # options per gate: (a, pa, b, pb); nodes 1..n are inputs, n+j is gate j
        self.options = {}
        for i in range(1, k + 1):
            opts = []
            nodes = list(range(1, self.n + i))  # available nodes (< n+i)
            for a, b in combinations(nodes, 2):
                for pa in (0, 1):
                    for pb in (0, 1):
                        opts.append((a, pa, b, pb, self._new()))
            self.options[i] = opts
        self.out_pol = self._new()

    def _new(self):
        self.nvars += 1
        return self.nvars

    def _node_val(self, node, t):
        """Node value on row t: (const, None) for inputs; (None, var) for gates."""
        if node <= self.n:
            return ((t >> (node - 1)) & 1, None)
        return (None, self.v[(node - self.n, t)])

    def build(self):
        c = self.clauses
        for i in range(1, self.k + 1):
            svars = [o[4] for o in self.options[i]]
            c.append(svars)  # at-least-one
            c.extend([-x, -y] for x, y in combinations(svars, 2))  # at-most-one
            for a, pa, b, pb, s in self.options[i]:
                for t in range(self.rows):
                    x = self.v[(i, t)]
                    # BUGFIX (caught by G1-verify on the first run): constants 0/1
                    # collided with DIMACS literals ±1 — now separate types.
                    ka, la = self._lit(a, pa, t)  # ('const', 0|1) ou ('lit', ±var)
                    kb, lb = self._lit(b, pb, t)
                    # x <-> la AND lb, condicionado a s
                    if (ka == "const" and la == 0) or (kb == "const" and lb == 0):
                        c.append([-s, -x])           # AND with false => x false
                    elif ka == "const" and kb == "const":  # ambos true
                        c.append([-s, x])
                    elif ka == "const":              # la=true: x <-> lb
                        c.append([-s, -x, lb]); c.append([-s, x, -lb])
                    elif kb == "const":              # lb=true: x <-> la
                        c.append([-s, -x, la]); c.append([-s, x, -la])
                    else:
                        c.append([-s, -x, la]); c.append([-s, -x, lb])
                        c.append([-s, x, -la, -lb])
        # SYMMETRY BREAKING (sound for the question "opt = k?"): two gates never
        # select the SAME option (a,pa,b,pb) — a MINIMAL circuit never has
        # duplicate gates (dropping the duplicate would give a smaller circuit).
        # Since the probe asks k=9 with opt in {9,10} (catalogue), every relevant
        # solution is minimal, hence duplicate-free. [EXP-PROBE-0001 v2]
        by_tuple = {}
        for i in range(1, self.k + 1):
            for a, pa, b, pb, s in self.options[i]:
                by_tuple.setdefault((a, pa, b, pb), []).append(s)
        for svars in by_tuple.values():
            if len(svars) > 1:
                c.extend([-x, -y] for x, y in combinations(svars, 2))
        # every gate i < k is used by some later gate
        for i in range(1, self.k):
            users = [o[4] for j in range(i + 1, self.k + 1)
                     for o in self.options[j] if o[0] == self.n + i or o[2] == self.n + i]
            if users:
                self.clauses.append(users)
            else:  # no possible consumers => k infeasible in this shape
                self.clauses.append([])
        # output: v[k][t] <-> (f(t) xor op)
        op = self.out_pol
        for t in range(self.rows):
            x = self.v[(self.k, t)]
            if tt_bit(self.tt, t):   # op=0 -> x=1 ; op=1 -> x=0
                self.clauses.append([op, x]); self.clauses.append([-op, -x])
            else:
                self.clauses.append([op, -x]); self.clauses.append([-op, x])
        return self

    def _lit(self, node, pol, t):
        """Returns ('const', 0|1) for inputs, ('lit', ±var) for gates."""
        const, var = self._node_val(node, t)
        if var is None:
            return ("const", const ^ pol)
        return ("lit", -var if pol else var)

    def to_dimacs(self, path):
        with open(path, "w") as f:
            f.write(f"p cnf {self.nvars} {len(self.clauses)}\n")
            for cl in self.clauses:
                f.write(" ".join(map(str, cl)) + " 0\n")

    def decode(self, model):
        """model = list of ints (pysat) or set of true literals. Returns the circuit."""
        pos = {abs(l) for l in model if l > 0}
        gates = []
        for i in range(1, self.k + 1):
            sel = [o for o in self.options[i] if o[4] in pos]
            assert len(sel) == 1, f"gate {i}: selection not unique ({len(sel)})"
            a, pa, b, pb, _ = sel[0]
            gates.append((a, pa, b, pb))
        return gates, (self.out_pol in pos)


def simulate(n, gates, out_pol, t):
    """Independent simulation of the decoded circuit, row t."""
    vals = {j: (t >> (j - 1)) & 1 for j in range(1, n + 1)}
    for idx, (a, pa, b, pb) in enumerate(gates, start=1):
        vals[n + idx] = (vals[a] ^ pa) & (vals[b] ^ pb)
    return vals[n + len(gates)] ^ (1 if out_pol else 0)


def verify_circuit(n, tt, gates, out_pol):
    """SEMANTIC CHECK (rule REV-0004): does the circuit match the whole truth table?"""
    return all(simulate(n, gates, out_pol, t) == tt_bit(tt, t) for t in range(1 << n))


def trivial_opt(n, tt):
    """opt=0: constants and literals (with polarity)."""
    rows = 1 << n
    if tt in (0, (1 << rows) - 1):
        return True
    for j in range(1, n + 1):
        lit = sum(((t >> (j - 1)) & 1) << t for t in range(rows))
        if tt == lit or tt == ((1 << rows) - 1) ^ lit:
            return True
    return False


def solve_k(n, tt, k, return_circuit=False):
    """SAT check with pysat/Glucose4. Returns (bool, circuit|None)."""
    from pysat.solvers import Glucose4
    enc = AIGEncoder(n, k, tt).build()
    if any(len(cl) == 0 for cl in enc.clauses):
        return False, None
    with Glucose4(bootstrap_with=enc.clauses) as s:
        if not s.solve():
            return False, None
        model = s.get_model()
    gates, op = enc.decode(model)
    assert verify_circuit(n, tt, gates, op), "FAILED: circuit does not match truth table"
    return True, (gates, op) if return_circuit else None


def opt_via_sat(n, tt, kmax=12):
    """Smallest k with a solution (0 = trivial)."""
    if trivial_opt(n, tt):
        return 0
    for k in range(1, kmax + 1):
        sat, _ = solve_k(n, tt, k)
        if sat:
            return k
    return None
