"""
EXP-GATE-0001 / G3 — INDEPENDENT exhaustive enumeration of AIG circuits.

Purpose (rule REV-0004): validate the SEMANTICS of the SAT encoder by a route
that shares nothing with it — direct brute-force search over circuits.
opt(f) = the smallest number of AND gates such that some sequence of gates
g_1..g_d (each = AND of two earlier nodes with free polarities)
produces f (up to output inversion) at the LAST gate added.

Justification for "last gate": if f appears at gate j of a circuit with
d > j gates, the prefix up to j is a j-gate circuit for f — so it suffices
to record each function at the first depth where it appears as a freshly
created gate along the recursion.
"""

import sys
from functools import lru_cache


def enumerate_opts(n, max_gates):
    """Returns a dict f_tt -> opt (0..max_gates) for every reachable function."""
    rows = 1 << n
    mask = (1 << rows) - 1
    inputs = tuple(sum(((t >> j) & 1) << t for t in range(rows)) for j in range(n))

    opt = {}

    def note(tt, d):
        for g in (tt, tt ^ mask):  # output inversion is free
            if g not in opt or opt[g] > d:
                opt[g] = d

    # opt = 0: constants and literals
    note(0, 0)
    for x in inputs:
        note(x, 0)

    seen_states = set()

    def rec(nodes, depth):
        state = (depth, tuple(sorted(nodes)))
        if state in seen_states:
            return
        seen_states.add(state)
        if depth == max_gates:
            return
        m = len(nodes)
        for i in range(m):
            for j in range(i + 1, m):
                for a in (nodes[i], nodes[i] ^ mask):
                    for b in (nodes[j], nodes[j] ^ mask):
                        g = a & b
                        note(g, depth + 1)
                        rec(nodes + (g,), depth + 1)

    rec(inputs, 0)
    return opt


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    opts = enumerate_opts(n, k)
    rows = 1 << n
    total = 1 << rows
    from collections import Counter
    dist = Counter(opts.values())
    print(f"n={n}, up to {k} gates: {len(opts)}/{total} functions reached")
    print("distribution of opt:", dict(sorted(dist.items())))
