# verification — rerun of the Krinkin catalogue's own `verify_all.py` with the two closed values

- **Date:** 2026-07-11 · **Motivation:** REV-0007 (Codex) finding 4 — the numbers 987→995 cited in
  the technote and in the issue needed an archived artefact, not just a claim in prose.
- **Procedure:** downloaded `krinkin/bounds` @ HEAD (`1443063`); applied a two-line binary patch to
  the CSV (`improved_ub` → `exact` on classes 0x1669/0x166b, line endings preserved); ran the
  author's OWN `scripts/verify_all.py`, unmodified, over the patched CSV plus the original
  `mutation_graph.json`.
- **Command:** `python3 scripts/verify_all.py` (Python 3.14.3, stdlib only — as the author's README
  specifies).
- **Files in this directory:**
  - `csv_update.diff` — the two-line patch.
  - `verify_all_updated.out` — the full output of the rerun: **222 exact / 0 ub; 995 exact-exact
    edges; max |diff_opt| = 4; distribution |0|=301 |1|=421 |2|=221 |3|=45 |4|=7; 7 tight edges;
    PASS.**
  - `HASHES.txt` — SHA-256 of: the original CSV (`5328e44f…`, identical to the one used in the
    experiments), the patched CSV, the author's script, and `mutation_graph.json`.
  - *(`verify_all.py.snapshot` was removed on 2026-07-27 — see the note below.)*
- **Baseline (original CSV, same script):** 220 exact / 2 ub; 987 edges; max 4; distribution
  |0|=300 |1|=414 |2|=221 |3|=45 |4|=7; PASS — reproduces the "Expected output" of the author's
  README exactly.
- **Conclusion this supports:** with the two exact values in place, the set of exact-exact edges in
  the author's OWN mutation graph grows 987→995 (+8) and the bound |Δopt| ≤ 4 holds on all of them;
  the distribution shifts in |0| (+1) and |1| (+7). Edge definition and canonicalization are the
  author's script's — we redefined nothing.
- **Conclusion this does NOT support:** anything about exhaustiveness beyond what the author's
  script computes.

---

## Note on what is not here (2026-07-27)

**This rerun is checkable but not self-contained, and that is deliberate.** Neither its two
inputs — `npn4.csv` and `mutation_graph.json` — nor the checker itself, `scripts/verify_all.py`,
is redistributed here. All three belong to the source paper's companion catalogue, and
[`krinkin/bounds`](https://github.com/krinkin/bounds) carries no licence, so they are not ours
to pass on. A snapshot of the script was originally kept in this directory; it was removed once
that was noticed.

To reproduce the run, take all three from that repository at commit `1443063`, apply
`csv_update.diff` to the CSV, and run the author's script unmodified.

`HASHES.txt` carries the SHA-256 of the original CSV, the patched CSV, the script and
`mutation_graph.json` — which is what makes the rerun checkable without our redistributing
anything: you can confirm you are working from exactly the bytes we did.
