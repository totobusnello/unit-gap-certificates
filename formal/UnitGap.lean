/-
UnitGap.lean — Formalization of the counterexample to the "Unit Gap Theorem"
(K. Krinkin, arXiv:2603.08033v2, Theorem 2: gap(f) = tree(f) − opt(f) ∈ {0,1}
for every Boolean function in the AIG basis with free inversions).

RESULT (theorems at the end): for f = ⊕₃ (parity of 3 variables):
  (a) `circuit_upper`   — an AIG circuit (straight-line, sharing allowed)
                          with 6 gates computes f;
  (b) `tree_lower`      — every AIG FORMULA (tree: fan-out 1 at the gates,
                          leaves may repeat, inversions free) that computes f
                          has ≥ 9 gates;
  (c) `tree_upper`      — a formula with exactly 9 gates computes f;
  (d) `unit_gap_refuted` — package (a)+(b): gap(⊕₃) ≥ 3 > 1.

MODEL: functions of 3 variables = 8-bit truth tables as `Nat < 256`
(bit t = f on row t; x_j = bit j of t ⟹ x1 ↦ 0xAA, x2 ↦ 0xCC, x3 ↦ 0xF0).
AND of functions = bitwise AND. Complement of v < 256 = 255 − v (equal to
v XOR 255 in that range). Parity = 0x96.

TRUST: structural lemmas by induction (kernel); finite facts by
`decide`/`native_decide` (the latter trusts the Lean compiler).

7_PROBLEMS programme · claims 7P-PNP-CLM-0024/0025 · 2026-07-11.
-/

namespace UnitGap

/-- Complement of an 8-bit truth table (v < 256 ⟹ equal to v XOR 255). -/
def cmpl (v : Nat) : Nat := 255 - v

/-- Apply an edge polarity: `true` inverts. -/
def ap (pol : Bool) (v : Nat) : Nat := if pol then cmpl v else v

def x1 : Nat := 0xAA
def x2 : Nat := 0xCC
def x3 : Nat := 0xF0

def par3 : Nat := 0x96

/-! ## AIG formulas (trees)

Internal nodes = 2-input AND gates with free complementation on each
edge; leaves = variables or the constant 1. Fan-out 1 at every gate is
automatic from the tree structure; leaves may repeat freely — exactly the
paper's own verbal definition ("a circuit in which every gate has fan-out one — a
tree"). Free OUTPUT inversion is handled in `Computes`. -/
inductive F where
  | var : Fin 3 → F
  | one : F
  | and : Bool → F → Bool → F → F

def eval : F → Nat
  | .var ⟨0, _⟩ => x1
  | .var ⟨1, _⟩ => x2
  | .var ⟨_ + 2, _⟩ => x3
  | .one => 255
  | .and pl l pr r => (ap pl (eval l)) &&& (ap pr (eval r))

def gates : F → Nat
  | .var _ => 0
  | .one => 0
  | .and _ l _ r => 1 + gates l + gates r

/-- `φ` computes `f` (free output inversion in the AIG basis). -/
def Computes (φ : F) (f : Nat) : Prop := eval φ = f ∨ eval φ = cmpl f

/-! ### Invariante: eval < 256 -/

theorem cmpl_lt {v : Nat} : cmpl v < 256 := by unfold cmpl; omega

theorem ap_lt {p : Bool} {v : Nat} (h : v < 256) : ap p v < 256 := by
  unfold ap; split
  · exact cmpl_lt
  · exact h

theorem and_lt {a b : Nat} (ha : a < 256) : a &&& b < 256 :=
  Nat.lt_of_le_of_lt Nat.and_le_left ha

theorem eval_lt (φ : F) : eval φ < 256 := by
  induction φ with
  | var i =>
    match i with
    | ⟨0, _⟩ => exact (by decide : x1 < 256)
    | ⟨1, _⟩ => exact (by decide : x2 < 256)
    | ⟨2, _⟩ => exact (by decide : x3 < 256)
  | one => decide
  | and pl l pr r ihl ihr => exact and_lt (ap_lt ihl)

/-! ## DP by cost levels

`lvls c = [D c, D (c−1), …, D 0]` (mais novo primeiro). COMPLETUDE (provada):
every function computable by a formula with ≤ i gates lies in `D i`. The converse
direction is not needed for the lower bound. The 4 edge-polarity combinations
are handled in the step (no closure under complement is required). -/

/-- Level 0: truth tables of the leaves. -/
def base : List Nat := [255, x1, x2, x3]

/-- g = (±a) ∧ (±b) with a in the first set and b in the second? -/
def combOk (s t : List Nat) (g : Nat) : Bool :=
  s.any fun a => t.any fun b =>
    g == a &&& b || g == a &&& cmpl b || g == cmpl a &&& b ||
      g == cmpl a &&& cmpl b

/-- Next level from the history `ls = [D (c−1), …, D 0]`:
keeps the previous level and combines pairs of levels whose costs sum to c−1
(paired by zipping the history with its reverse). -/
def nextLevel (ls : List (List Nat)) : List Nat :=
  (List.range 256).filter fun g =>
    List.elem g (ls.headD []) ||
    (ls.zip ls.reverse).any fun st => combOk st.1 st.2 g

def lvls : Nat → List (List Nat)
  | 0 => [base]
  | c + 1 => nextLevel (lvls c) :: lvls c

/-- `D i` read off the history `lvls c` (for i ≤ c). -/
def dpAt (c i : Nat) : List Nat := ((lvls c)[c - i]?).getD []

theorem lvls_length (c : Nat) : (lvls c).length = c + 1 := by
  induction c with
  | zero => rfl
  | succ c ih => simp [lvls, ih]

/-- Stability: old levels do not change as the history grows. -/
theorem dpAt_succ_of_le {c i : Nat} (h : i ≤ c) :
    dpAt (c + 1) i = dpAt c i := by
  unfold dpAt
  rw [show c + 1 - i = (c - i) + 1 from by omega]
  show (((nextLevel (lvls c) :: lvls c))[(c - i) + 1]?).getD [] = _
  rw [List.getElem?_cons_succ]

theorem dpAt_stable {c c' i : Nat} (hic : i ≤ c) (hcc : c ≤ c') :
    dpAt c' i = dpAt c i := by
  induction c' with
  | zero =>
    have : c = 0 := Nat.le_zero.mp hcc
    subst this; rfl
  | succ c' ih =>
    rcases Nat.lt_or_ge c (c' + 1) with hlt | hge
    · have hle : c ≤ c' := Nat.lt_succ_iff.mp hlt
      rw [dpAt_succ_of_le (Nat.le_trans hic hle), ih hle]
    · have : c = c' + 1 := Nat.le_antisymm hcc hge
      subst this; rfl

/-- D_{c+1} read directly off the history. -/
theorem dpAt_top (c : Nat) : dpAt (c + 1) (c + 1) = nextLevel (lvls c) := by
  unfold dpAt
  rw [Nat.sub_self]
  show (((nextLevel (lvls c) :: lvls c))[0]?).getD [] = _
  rfl

/-- head of the history = diagonal level. -/
theorem headD_lvls (c : Nat) : (lvls c).headD [] = dpAt c c := by
  unfold dpAt
  rw [Nat.sub_self]
  cases hc : lvls c with
  | nil =>
    have := lvls_length c
    rw [hc] at this
    simp at this
  | cons h t => rfl

/-- O par (D_{c−i}, D_i) aparece em `(lvls c).zip (lvls c).reverse`. -/
theorem pair_mem_zip (c i : Nat) (hi : i ≤ c) :
    (dpAt c (c - i), dpAt c i) ∈ ((lvls c).zip (lvls c).reverse) := by
  have hlen : (lvls c).length = c + 1 := lvls_length c
  have hi' : i < (lvls c).length := by omega
  have hci : c - i < (lvls c).length := by omega
  have h1 : (lvls c)[i]? = some ((lvls c)[i]'hi') := List.getElem?_eq_getElem hi'
  have h2 : (lvls c).reverse[i]? = (lvls c)[c - i]? := by
    apply List.getElem?_reverse'
    omega
  have h3 : (lvls c)[c - i]? = some ((lvls c)[c - i]'hci) :=
    List.getElem?_eq_getElem hci
  have hA : dpAt c (c - i) = (lvls c)[i]'hi' := by
    unfold dpAt
    rw [show c - (c - i) = i from by omega, h1]
    rfl
  have hB : dpAt c i = (lvls c)[c - i]'hci := by
    unfold dpAt
    rw [h3]
    rfl
  apply List.mem_of_getElem? (i := i)
  show ((lvls c).zip (lvls c).reverse)[i]? = _
  simp only [List.zip]
  rw [List.getElem?_zipWith, h1, h2, h3, hA, hB]

/-- Step: a ∈ D_{c−i}, b ∈ D_i (in history c) ⟹ (±a)∧(±b) ∈ D_{c+1}. -/
theorem step_mem {c i : Nat} (hi : i ≤ c) {a b : Nat} {p q : Bool}
    (ha : a ∈ dpAt c (c - i)) (hb : b ∈ dpAt c i)
    (hlt : ap p a &&& ap q b < 256) :
    (ap p a &&& ap q b) ∈ dpAt (c + 1) (c + 1) := by
  have hcomb : combOk (dpAt c (c - i)) (dpAt c i) (ap p a &&& ap q b) = true := by
    unfold combOk
    rw [List.any_eq_true]
    refine ⟨a, ha, ?_⟩
    rw [List.any_eq_true]
    refine ⟨b, hb, ?_⟩
    cases p <;> cases q <;> simp [ap]
  rw [dpAt_top]
  unfold nextLevel
  rw [List.mem_filter]
  refine ⟨List.mem_range.mpr hlt, ?_⟩
  simp only [Bool.or_eq_true]
  right
  rw [List.any_eq_true]
  exact ⟨(dpAt c (c - i), dpAt c i), pair_mem_zip c i hi, hcomb⟩

/-- Monotonia diagonal: g ∈ D_i ⟹ g ∈ D_c (i ≤ c, g < 256). -/
theorem dpAt_mono {c i : Nat} (hi : i ≤ c) {g : Nat}
    (hg : g ∈ dpAt c i) (hg256 : g < 256) : g ∈ dpAt c c := by
  induction c with
  | zero =>
    have : i = 0 := Nat.le_zero.mp hi
    subst this; exact hg
  | succ c ih =>
    rcases Nat.lt_or_ge i (c + 1) with hlt | hge
    · have hic : i ≤ c := Nat.lt_succ_iff.mp hlt
      have hg' : g ∈ dpAt c i := by rw [← dpAt_succ_of_le hic]; exact hg
      have hgc : g ∈ dpAt c c := ih hic hg'
      rw [dpAt_top]
      unfold nextLevel
      rw [List.mem_filter]
      refine ⟨List.mem_range.mpr hg256, ?_⟩
      simp only [Bool.or_eq_true]
      left
      rw [headD_lvls]
      exact List.elem_eq_true_of_mem hgc
    · have : i = c + 1 := Nat.le_antisymm hi hge
      subst this; exact hg

/-- COMPLETENESS: a formula with ≤ c gates ⟹ its truth table lies in D_c. -/
theorem complete (φ : F) : ∀ c, gates φ ≤ c → eval φ ∈ dpAt c c := by
  induction φ with
  | var i =>
    intro c _
    have h0 : eval (F.var i) ∈ dpAt 0 0 := by
      match i with
      | ⟨0, _⟩ => exact (by decide : x1 ∈ dpAt 0 0)
      | ⟨1, _⟩ => exact (by decide : x2 ∈ dpAt 0 0)
      | ⟨2, _⟩ => exact (by decide : x3 ∈ dpAt 0 0)
    have hst := dpAt_stable (Nat.le_refl 0) (Nat.zero_le c)
    exact dpAt_mono (Nat.zero_le c) (hst ▸ h0) (eval_lt _)
  | one =>
    intro c _
    have h0 : eval F.one ∈ dpAt 0 0 := by decide
    have hst := dpAt_stable (Nat.le_refl 0) (Nat.zero_le c)
    exact dpAt_mono (Nat.zero_le c) (hst ▸ h0) (eval_lt _)
  | and pl l pr r ihl ihr =>
    intro c hc
    have hglr : 1 + gates l + gates r ≤ c := hc
    have ha : eval l ∈ dpAt (gates l + gates r) ((gates l + gates r) - gates r) := by
      rw [show (gates l + gates r) - gates r = gates l from by omega,
        dpAt_stable (Nat.le_refl (gates l)) (Nat.le_add_right _ _)]
      exact ihl (gates l) (Nat.le_refl _)
    have hb : eval r ∈ dpAt (gates l + gates r) (gates r) := by
      rw [dpAt_stable (Nat.le_refl (gates r)) (Nat.le_add_left _ _)]
      exact ihr (gates r) (Nat.le_refl _)
    have hstep := step_mem (c := gates l + gates r) (i := gates r)
      (Nat.le_add_left _ _) (p := pl) (q := pr) ha hb
      (and_lt (ap_lt (eval_lt _)))
    have hle : gates l + gates r + 1 ≤ c := by omega
    have h2 : eval (F.and pl l pr r) ∈ dpAt c (gates l + gates r + 1) := by
      rw [dpAt_stable (Nat.le_refl _) hle]
      exact hstep
    exact dpAt_mono hle h2 (eval_lt _)

/-! ## Finite computational fact: ⊕₃ (and its complement) lie outside D 8. -/

theorem par3_not_in_D8 : par3 ∉ dpAt 8 8 ∧ cmpl par3 ∉ dpAt 8 8 := by
  native_decide

/-! ## (b) Formula lower bound. -/

theorem tree_lower (φ : F) (h : Computes φ par3) : 9 ≤ gates φ := by
  rcases Nat.lt_or_ge (gates φ) 9 with hlt | hge
  · exfalso
    have h8 : gates φ ≤ 8 := by omega
    have hmem : eval φ ∈ dpAt 8 8 := complete φ 8 h8
    rcases h with heq | heq
    · exact par3_not_in_D8.1 (heq ▸ hmem)
    · exact par3_not_in_D8.2 (heq ▸ hmem)
  · exact hge

/-! ## (c) Nine-gate witness formula. -/

/-- u ∧ ¬v. -/
def andn (u v : F) : F := .and false u true v

/-- ¬(u⊕v) as a 3-gate tree: ¬(u∧¬v) ∧ ¬(¬u∧v). -/
def nxor (u v : F) : F := .and true (andn u v) true (andn v u)

/-- ¬⊕₃ with 9 gates (two copies of the ⊕₂ subtree; `Computes` covers the
output inversion): ¬( (⊕₂ ∧ ¬x3) ∨ (¬⊕₂ ∧ x3) ). -/
def w9 : F :=
  .and true (.and true (nxor (.var 0) (.var 1)) true (.var 2))
       true (.and false (nxor (.var 0) (.var 1)) false (.var 2))

theorem tree_upper : gates w9 = 9 ∧ Computes w9 par3 :=
  ⟨rfl, Or.inr (by decide)⟩

/-! ## (a) Six-gate circuit (straight-line program).

AIG circuit = list of gates; the gate at position p refers to nodes 0..2 (inputs)
and 3..(2+p) (earlier gates) — ANY node may be referred to more than once
(sharing, which a formula forbids). Output = last gate, with free output
inversion. -/

structure Gate where
  na : Bool
  ia : Nat
  nb : Bool
  ib : Nat

def inputTT (i : Nat) : Nat :=
  if i == 0 then x1 else if i == 1 then x2 else x3

def nodeVal (nodes : Array Nat) (i : Nat) : Nat :=
  if i < 3 then inputTT i else nodes.getD (i - 3) 0

def runProg (p : List Gate) : Array Nat :=
  p.foldl
    (fun nodes g =>
      nodes.push ((ap g.na (nodeVal nodes g.ia)) &&& (ap g.nb (nodeVal nodes g.ib))))
    #[]

def outProg (p : List Gate) : Nat := (runProg p).getD (p.length - 1) 0

/-- Well-formedness: each gate refers only to earlier nodes. -/
def wf (p : List Gate) : Bool :=
  p.zipIdx.all fun gi => gi.1.ia < 3 + gi.2 && gi.1.ib < 3 + gi.2

def ProgComputes (p : List Gate) (f : Nat) : Prop :=
  outProg p = f ∨ outProg p = cmpl f

/-- 6 gates: node 5 = ¬(x1⊕x2) is SHARED (fan-out 2, nodes 6 and 7). -/
def c6 : List Gate :=
  [ ⟨false, 0, true, 1⟩,   -- node 3:  x1 ∧ ¬x2
    ⟨true, 0, false, 1⟩,   -- node 4:  ¬x1 ∧ x2
    ⟨true, 3, true, 4⟩,    -- node 5:  ¬n3 ∧ ¬n4 = ¬(x1⊕x2)
    ⟨true, 5, true, 2⟩,    -- node 6:  (x1⊕x2) ∧ ¬x3
    ⟨false, 5, false, 2⟩,  -- node 7:  ¬(x1⊕x2) ∧ x3
    ⟨true, 6, true, 7⟩ ]   -- node 8:  ¬n6 ∧ ¬n7 = ¬⊕₃

theorem circuit_upper : wf c6 = true ∧ c6.length = 6 ∧ ProgComputes c6 par3 :=
  ⟨by decide, rfl, Or.inr (by decide)⟩

/-! ## Final package -/

/-- **Refutation of the Unit Gap Theorem** (Thm 2 of arXiv:2603.08033) under the
definition of formula stated in that paper itself: the parity of 3 variables has a
6-gate circuit, but every formula computing it has ≥ 9 gates —
gap ≥ 3 ∉ {0,1}. (`tree_upper` pins the value: gap = 3.) -/
theorem unit_gap_refuted :
    (∃ p : List Gate, wf p = true ∧ p.length = 6 ∧ ProgComputes p par3) ∧
    (∀ φ : F, Computes φ par3 → 9 ≤ gates φ) :=
  ⟨⟨c6, circuit_upper⟩, tree_lower⟩

/-! ## Axiom audit (trust documentation) -/
#print axioms complete
#print axioms tree_lower
#print axioms tree_upper
#print axioms circuit_upper
#print axioms unit_gap_refuted

end UnitGap
