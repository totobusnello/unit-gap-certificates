# unit-gap-certificates: machine-checkable artefacts for a refutation of Theorem 2 of arXiv:2603.08033

Machine-checkable artefacts for a refutation of Theorem 2 of Krinkin, *The Unit Gap: How
Sharing Works in Boolean Circuits* ([arXiv:2603.08033v2]). The refutation itself rests on a
single counterexample at `n = 3`; the exhaustive `n = 4` census included here is what shows
the failure is structural rather than a lucky function.

**What this is not:** progress on P vs NP. Nothing here claims a separation, a collapse, or a
step toward either. It is a correction to one published claim, plus the data behind it.

[arXiv:2603.08033v2]: https://arxiv.org/abs/2603.08033

---

## The refutation

Theorem 2 asserts that for every Boolean function the minimum formula size exceeds the minimum
circuit size by at most one gate — `gap ∈ {0, 1}` in the And-Inverter Graph cost model — with
Corollary 6 bounding a shared-gate term `s ∈ {0, 1}`.

Both are false. Under the paper's own definition of a formula (fan-out one at every gate), the
parity of three variables is a counterexample:

|  |  |
|---|---|
| `opt(⊕₃)` | **6** — UNSAT for every gate count `k = 1..5`, each certified by a DRAT proof |
| `tree(⊕₃)` | **9** — two independent dynamic programs, and the Lean development |
| gap | **3** — against a claimed maximum of 1 |
| Krinkin's own `s = \|Dₐ ∩ D_b\|` | **3** — against a claimed maximum of 1 |

Two things are worth separating here, because they have different standing.

**What refutes Theorem 2 is classical, and no certificate in this repository is needed for it.**
The AIG basis with free inversions is exactly `U₂` — the full binary basis minus XOR and XNOR — so
Schnorr (1976) gives `opt(⊕₃) = 6`, and Khrapchenko's bound forces `tree(⊕₃) ≥ 9` leaves, hence
`≥ 8` gates. **That already gives `gap ≥ 2 > 1`**, from two published results and one
identification, with no computation of ours in the chain. The identification is elementary, but it
is a step, and it is supplied by the accompanying note rather than by Schnorr or Khrapchenko.

**What this repository certifies is the exact value.** `gap = 3` needs `tree(⊕₃) = 9`, which is not
in the refereed literature — the obvious citation does not survive, since Lee's rank technique
(STACS 2007) was announced as determining the formula size of parity for every `n` and Lee has
since [publicly retracted](http://www.cs.columbia.edu/~tl2383/correction.html) that claim. So
`tree(⊕₃) = 9` is certified here, by two independent dynamic programs and the Lean development,
and `opt(⊕₃) = 6` by a DRAT chain a reader can re-check with `drat-trim` alone.

The number is not new. An exhaustive enumeration by
[Russ Cox and Alex Healy](https://research.swtch.com/boolean), computed in 2010 and published in
2011, gives parity 9 AND/OR operators at `n = 3` and 15 at `n = 4` — their measure is gates, so
it matches without conversion. We claim nothing for the number; we say where it comes from.

The failure is structural, not a lucky single function. An exhaustive census over the 222 NPN
classes of `n = 4` finds **72 classes (32.4%) with gap ≥ 2**, the maximum gap being 6, attained
by three distinct classes — and that maximum is exactly what Schnorr and Tarui (2010) give for
parity-4, since `4 = 2²` is where Khrapchenko's bound is attained. That is an external spot
check: it confirms one row of the census against published values, not the other 221, and not
the NPN-class join.

The error is locatable in the source paper: §2 displays `tree(f) = min(1 + opt(a) + opt(b))`,
with the DAG measure `opt` in the children, while §3's Bellman operator is
`(Tv)(f) = min(1 + v(a) + v(b))`, the recursive measure. These are incompatible
characterizations of formula size — the first makes Theorem 2 a one-line tautology, the second
makes it false.

The counterexample is formalized in Lean 4.

---

## Re-checking the certificates yourself

Re-checking that the archived CNFs are unsatisfiable needs `drat-trim` and nothing else — not
the encoder, not the solver, nothing else here.

What a DRAT proof does **not** certify is that a CNF faithfully encodes the question asked of
it. That is a separate obligation, and it is discharged separately: `encoders/enumerate_aig.py`
computes the same optima by brute-force enumeration, sharing no code with the SAT encoder, and
`encoders/run_gate.py` cross-checks the two in both directions. Trust the solver less; audit
the encoding.

```sh
cd certificates
for f in par3_k1 par3_k2 par3_k3 par3_k4 par3_k5 h_child_k1 h_child_k2 h_child_k3; do
  drat-trim "$f.cnf" "$f.drat"
done
```

Each run should report `s VERIFIED`. The recorded transcript in `verify_lowk.log` carries the
SHA-256 of every CNF and DRAT file, so you can confirm you are checking the same bytes.

**Tool versions:** kissat 4.0.4 · `drat-trim` ([marijnheule], commit `2e3b2dc`) · Lean 4.31.0.

[marijnheule]: https://github.com/marijnheule/drat-trim

---

## Where the artefacts are

| Claim in the paper | File |
|---|---|
| `opt(⊕₃) ≥ 6`, `k = 1..5` | `certificates/par3_k{1..5}.{cnf,drat}` |
| `opt(child) ≥ 4`, `k = 1..3` | `certificates/h_child_k{1..3}.{cnf,drat}` |
| Checker transcript, 8/8 `s VERIFIED` + SHA-256 | `certificates/verify_lowk.log` |
| CNF generators | `certificates/gen_drat_*.py` |
| AIG census, `n = 4` (222 classes) | `census/aig-n4/npn4_gap.csv` |
| The layered dynamic program that produced it | `census/aig-n4/tree_gap_n4.py` |
| Its independent re-implementation as a global Bellman fixed point | `census/aig-n4/tree_gap_n4_v2.py` |
| The two implementations agreeing on all 65,536 cells | `census/aig-n4/tree_gap_n4_v2_out.txt` |
| `n = 3` gap distribution | `census/aig-n4/tree_gap_n3.py`, `tree_gap_n3.log` |
| XAG census, per-class `opt`/`tree`/`gap` | `census/xag-n4/npn4_xag_gap.csv` |
| MIG census | `census/mig-n4/` |
| `n = 5` directed search, per worker + deduplicated | `census/xag-n4/search_n5_*.csv` |
| 494/494 re-verification of the `n = 5` sample, by simulation | `census/xag-n4/verify_n5_recheck.log` |
| Rerun of the source paper's own catalogue checker | `verification/` |
| Lean 4 formalization | `formal/UnitGap.lean` |
| Exact-synthesis encoders | `encoders/` |
| The `n = 4` exact-opt catalogue, re-derived 222/222 | `encoders/npn4_opt_aig.csv` |
| Qualification gate: UNSAT at `k = opt − 1`, with its DRAT proof | `encoders/g2_0x0016_k6.{cnf,drat}` |
| Paper source and PDF | `paper/` |

---

## Method and provenance

The analysis, code and certificates were produced with AI assistance, under the direction of
**Luiz Antonio Busnello**, who chose the targets, set the verification standard, and is
responsible for the claims.

The working method is adversarial: results are attacked by independent language-model families
before being accepted. That review is provenance, not evidence — the evidence is the DRAT
certificates and the two classical results, both of which stand without it.

Source files carry internal review identifiers (`REV-00NN`) referring to this programme's own
audit log. Comments and docstrings were translated from Portuguese to English on 2026-07-27 so
that the code can be read by the people it is addressed to; no logic was touched, and the Lean
development compiles to byte-identical `#print axioms` output before and after.

The five `.log` files and the `*_out.txt` transcripts are left exactly as the tools printed
them; editing a transcript would falsify the record. For the same reason the scripts' own
`print` strings were left in Portuguese where the archived transcripts contain them — a
re-run has to stay comparable, line for line, with what is recorded here.

## Relation to the working repository

This repository is the frozen artefact set, and it is the one to cite. The programme's working
repository — the lab notebook, which also holds correspondence with the author of the refuted
paper — is private, because that correspondence is not ours to publish. Everything the note
relies on is here.

If something you need to check is missing, say so and it will be added: the point of an
artefact set is that a reader can get to the bottom of it without asking, and any gap in that
is a defect.

## Citation

See `CITATION.cff`. Archived on Zenodo with a permanent DOI; cite the DOI rather than a
repository URL.

## License

MIT — see `LICENSE`. The point of a certificate is that anyone may re-check it and say so.
