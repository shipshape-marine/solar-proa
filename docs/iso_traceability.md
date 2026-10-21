---
layout: default
title: Roti Proa II - ISO 12215 Traceability
---

[← Back to Structural Safety Report]({{ '/validation_rp2.html' | relative_url }})

---

## Purpose

This page maps RP2's existing structural safety factors (computed by the analytical
beam-theory suite in `src/structural/`) against the BS EN ISO 12215 small-craft
standard series, and the ISO 12217-2 stability standard that sets the design
category (§7), and reports where new ISO-anchored checks agree, disagree, or
cannot yet be computed for this vessel's asymmetric proa layout.

Full clause/table citations are recorded in
[`constant/standards/iso12215.json`](https://github.com/shipshape-marine/solar-proa/blob/main/constant/standards/iso12215.json)
in the repository. Per copyright terms, the ISO/BSI source PDFs themselves are held
locally by the design team and are not redistributed through this repository or site
— only bibliographic citations (standard, edition, clause/table number) are recorded.

Numbers on this page were computed by running `make validate-structure BOAT=rp2
CONFIGURATION=beaching`, which uses RP2's real modeled mass/geometry — they are
reproducible from the repository, not illustrative placeholders.

---

## The multihull gap is largely resolved

RP2's design team previously flagged that ISO 12215-5 (design pressures) is written
for **monohulls**, while RP2 is an asymmetric proa (one main hull + one outrigger
float) — a mismatch with no obvious governing standard on hand.

**ISO 12215-7:2020** ("Determination of loads for multihulls and of their local
scantlings using ISO 12215-5") is, in fact, on file with the design team. It gives
global load cases (crossbeam torsion, longitudinal shock, rig-load combination) and
float-specific local pressures that ISO 12215-5 alone does not cover.

It is still not a perfect fit: **ISO 12215-7's worked formulas assume a symmetric
catamaran or trimaran** (two equal hulls, or one hull + two equal floats). RP2 has
only one, asymmetric outrigger. Where a Part 7 formula is applied below, the
adaptation used and its confidence level is stated explicitly — nothing is silently
forced onto the proa geometry.

---

## Cross-check summary

| # | Load case | Existing SF (vs. raw yield, required ≥2.0) | ISO-anchored cross-check | Status |
|---|---|---|---|---|
| 1 | Suspended ama (aka bending) | **3.27** | GLC5 (ISO 12215-7 §12.10) dynamic longitudinal-shock case on the same aka: **SF = 1.35** vs. ISO's own design stress | ⚠️ See below — different load case, much tighter margin |
| 2 | Aka point load (crew standing) | 5.74 | Not separately re-derived (static, non-ISO-specific load case) | — |
| 3 | One end supported (spine bending) | 16.50 | Not separately re-derived | — |
| 4 | **Mast wind loading (25 kn, full sail)** | ~~6.18~~ ~~3.09~~ ~~2.06~~ **1.60** | ISO 12215-10:2020 Table 5 formula itself; CE height re-derived from CAD rig geometry, now including sail tilt | ⚠️ Fails 2.0, but the load case is deliberately harsher than the boat can carry — see below |
| 5 | Diagonal braces (lateral) | 33.60 | Reviewed against ISO 12215-7 Table 12 aluminium design stress convention | ✅ Confirmed genuine margin, not a modeling artifact — see below |
| 6–8 | Wave slam (vertical/frontal/sideways) | 4.46 / 5.23 / 4.46 | ISO 12215-7 §9.4 float bottom pressure: **0.33×** the ad hoc model's dynamic pressure | ℹ️ Ad hoc model is more conservative — see below |
| 9 | Lifting sling | 6.16 | Not an ISO-covered load case (crane/rigging, not a small-craft design load) | — |
| 10 | Gunwale loads | 12.24 | Not separately re-derived | — |
| 11 | Ama lift wind speed | ~~22 kn~~ ~~17.9 kn~~ 16.0 kn | CE height re-derived from CAD rig geometry, now including sail tilt (see §1 follow-up); ISO 12217-2 Annex G gives a lower figure — see §7 | ⚠️ See §7 |
| — | **Aka-to-vaka joint** | *(not previously checked at all)* | ISO 12215-6 good practice + first-pass weld sizing: passes a web-area rule of thumb | ⚠️ Real gap confirmed — see below |
| — | **Aluminium alloy spec** | *(not finalized)* | ISO 12215-3 §4.7: extruded-profile family (6000-series) is the correct choice | ⚠️ Documentation gap confirmed — see below |

---

## 1. Mast wind loading: a real formula bug, now fixed (6.18 → 3.09)

`mast_analysis.py` computed wind force as `F = 0.72 × V² × A / 2`, citing ISO
12215-10 Clause 7.2, Table 5. Checking the ISO 12215-10:2020 source directly (Table
5, Note 3):

> *"the wind force is F_A = N × 0.5 × ρ × A × V² (N) where N=1.2 ... ρ=1.2 kg/m³
> ... hence F_A = 0.720 × A × V² (N)"*

The 0.72 coefficient **already includes** the ½ dynamic-pressure term (1.2 × 0.5 ×
1.2 = 0.72). The code's extra `/2` halved the applied wind force, which
approximately doubled the reported safety factor. This has been corrected —
`mast_analysis.py` now computes `F = 0.72 × V² × A` with no extra division.

**Result on the real design**: mast wind-loading safety factor moves from **6.18 →
3.09**. The mast still comfortably passes the required minimum of 2.0 — this is a
correction to the reported number, not a design deficiency.

**Follow-up (2026-10): center-of-effort height.** The mast and capsize checks
assumed the boom sits at the mast partner (`aka_base_level`, 1406 mm), putting the
CE 2200 mm above the partner. The CAD rig (`src/design/rotating.py`) instead hangs
the sail from the yard pivot (`yard_spar_height + yard_spar_thickness/2`, 8005 mm),
which puts the boom at 2505 mm and the CE 3299 mm above the partner at full sail.
Reefing also raises the boom toward the pivot rather than lowering the CE, so the
lever arm grows as sail is reefed. Both checks now share
`mast_analysis.calculate_sail_levels`. At 25 kn and full sail, the mast
wind-loading safety factor moves from **3.09 → 2.06**, which still passes the 2.0
minimum but only just. The capsize safety factor moves from 0.72 → 0.51, and the
ama-lift wind speed from 22 kn → 17.9 kn.

Those figures still treated the sail as hanging straight down. The CAD also turns
each sail in its own plane by the configuration's `sail_angle` about the yard pivot,
which raises the CE to 0.6 × sail height × cos(sail_angle) below the pivot.
`calculate_sail_levels` now takes that angle. For RP2 at full sail the CE rises from
3.80 m above the heeling axis to 4.24 m at −30° and 4.77 m at −45°.

The design check (`python -m src.structural`) runs on the beaching artifacts, whose
−90° is the stowed rig, so it doesn't use the configuration's angle. It applies
`validate.DESIGN_SAIL_ANGLE_DEG` = −45°, the most-tilted sailing preset (close haul,
goosewing), overridable with `--sail-angle`. The operating envelope still uses the
configuration's own angle. At 25 kn and full sail, the mast safety factor drops
**2.06 → 1.60, now failing the 2.0 minimum**, the capsize safety factor drops
0.51 → 0.41, and the ama-lift wind speed drops 17.9 kn → 16.0 kn.

**The 25 kn full-sail mast case is deliberately harsh.** It is a project design
case, not an ISO-prescribed wind speed, and it is kept as a simple, conservative
strength check. It is not a load the boat can actually carry: full sail overpowers
RP2's maximum righting moment at about 16 kn with the wind from the ama side (14.0
kN·m) and about 19.5 kn from the vaka side (20.8 kN·m), so the sails are reefed or
eased, or the boat capsizes, before the mast sees the 25 kn load. Because the
partner bending moment is capped at roughly the maximum righting moment, the mast
keeps a safety factor of about 2.6 or more (static) under any load RP2 can stand up
to; it is 3.89 at the 16 kn ama-lift point. 25 kn does sit within Design Category
C's steady wind (Beaufort 6, ISO 12217-2 §9.2.3), where it applies to a reefed
sail: at an 88% reef the mast safety factor is 8.97. ISO 12217-2 §7.5 b) treats rig
strength as one limit on the safe full-sail wind speed, alongside stability (see §7).

---

## 2. Diagonal braces (33.60): confirmed genuine margin, not a boundary-condition artifact

The design team's original concern was that the diagonal braces' very high safety
factor (33.60) might be a "fixed-support artifact" — i.e. that `brace_analysis.py`'s
Euler buckling calculation assumed unrealistically rigid end conditions.

Checking the actual computation: the code uses **K = 1.0 (pinned-pinned)**, which is
the *most conservative* standard idealization for buckling (it gives the *lowest*
buckling capacity among common end-fixity assumptions — any real end fixity, K <
1.0, would only *increase* the buckling load and therefore *increase* the reported
safety factor further). So K=1.0 is not an overly-rigid assumption; if anything it
already understates the brace's true capacity.

The real driver of the 33.60 figure: the brace's actual compressive load under the
"boat on its side" load case (698.5 N) is simply small relative to its Euler
buckling capacity (23,468 N) for this slenderness (88.3). Checked against ISO
12215-7 Table 12's aluminium buckling design-stress convention as well, nothing in
the governing standard changes this conclusion. **The 33.60 figure is genuine
margin, not a modeling artifact.**

---

## 3. Aka bending: existing 3.27 covers a different (lighter) load case than ISO's own dynamic global load

`aka_analysis.py`'s 3.27 safety factor is for the **suspended ama** case: static
weight of the outrigger (1g), no dynamic amplification, compared against raw
aluminium yield strength (240 MPa) with a required SF of 2.0.

ISO 12215-7 §12.10 (GLC5 — longitudinal shock, e.g. hitting a floating object or a
steep wave) is a genuinely different, **dynamic** load case that the existing suite
does not check at all. Adapting it to RP2 (treating the single ama as the closest
available "trimaran float" analogue, the most defensible fit in Part 7 for this
geometry):

- Longitudinal shock force: **F_LT = min(5×m_LDC, 5×m_ama) = 2.01 kN** (≈0.5g
  deceleration per ISO's own note)
- Distributed evenly across the 4 akas: **503.5 N per aka**
- Resulting weak-axis bending stress at the vaka connection: **59.75 MPa**
- Compared to ISO's own allowable design stress for a welded 6061 closed-profile
  extrusion (σ_d = 0.7×σ_yw = **80.5 MPa**, per ISO 12215-5 Table 17/Annex B):
  **SF = 1.35**

An SF of 1.35 against ISO's *own* design stress (which already includes ISO's
built-in knockdown from yield) means this case is ISO-compliant but with far less
margin than the 3.27 figure suggests for a different loading direction. **This is
the most actionable finding on this page**: the aka has comfortable margin against
the static suspended-weight case, but only modest margin against a dynamic
longitudinal-shock case that nothing in the existing suite previously checked.

*(GLC1 — the diagonal torsional-moment case in a quartering sea — was deliberately
**not** carried through to a per-aka number. ISO 12215-7 Annex D's distribution
method assumes the torsional moment is reacted by crossbeams twisting between two
hulls of the same type; RP2 has only one outrigger, so there is no second hull for
the akas to react against in the way Annex D models. Per ISO 12215-7 §12.3.3, a
non-typical arrangement like this needs the "enhanced method" (FEM), not the
simplified method — this is flagged as an open item requiring dedicated engineering
analysis, not force-fit into a formula that doesn't apply.)*

---

## 4. Aka-to-vaka joint: confirmed real gap, but for a different reason than assumed

The original assumption was that ISO 12215-6 §6.3/7.2 would give bonding-width /
k_j-style coefficients for this joint, similar to FRP tabbing calculations.

**Checking the source directly: ISO 12215-6 Clause 7.2 "Bonding" is specific to
FRP/composite construction.** It does not apply to the aluminium aka-to-vaka
connection at all. For metal construction, ISO 12215-6 gives only qualitative
good-practice principles:

- §6.3.1/6.3.2: loads transmitted via stiff brackets, not landed on unsupported
  material
- §8.2: end connections must provide "adequate end fixity and effective
  transmission of the bending moment and shear force" — no formula given
- §8.7/8.8: welding per Annex C good practice, or riveting with concrete geometric
  rules (rivet diameter, spacing, edge distance) — but still no joint-capacity
  formula

**There is no closed-form ISO 12215-6 formula for a metal end-connection's load
capacity.** This module derives a first-pass minimum by engineering analogy to
Clause 6.3.4 (which addresses a different connection type — floating frames — but
states "weld or glue area shall generally not be less than the stiffener web
area"): the aka's web area (833 mm²) exceeds the area required to carry the
suspended-ama case's moment and shear at ISO's welded design stress (governing
requirement: 391.5 mm²) — so this rule-of-thumb passes, but **it is not a
certified joint design**, because no joint design exists yet. This remains the
right place to focus engineering effort once a real bracket/weld geometry is
proposed.

---

## 5. Wave slam pressure: ad hoc model is more conservative than the ISO estimate

`wave_slam.py` estimates ama slam pressure from an assumed 3 m/s impact velocity, a
hand-picked slam coefficient (Cp=1.5), and a 2.5× dynamic factor — none of the three
numbers are ISO-derived.

Using ISO 12215-7 §9.4 ("Design pressure for trimaran floats" — again treating the
single ama as the closest available float analogue) and ISO 12215-5 §8/§9 for the
base formula and k_DC/k_L/k_AR/k_SLS factors (Design Category C: k_DC = 0.6, and
k_SLS = 1 per ISO 12215-5 §8.7 Table 11):

- ISO-anchored design pressure at the ama's slam-affected area: **5.7 kPa**
- Existing ad hoc dynamic pressure: **17.3 kPa**
- Ratio: **0.33×** — the existing model is roughly 3× more conservative

k_SLS is a slamming correction for light, stable sailing craft. It only applies in
Categories A and B. RP2 does count as "light" by Table 11's test (modelled mass
2,350 kg, below 5 × L_WL³ ≈ 3,650 kg), so if the category were ever raised to B,
k_SLS would come from the table's righting-lever formula instead, at roughly 1.2–1.4,
and this pressure would rise by that factor. `iso_design_pressure.py` refuses to run
for Category A or B until that formula is implemented.

This is a reasonable outcome (the ad hoc model was deliberately chosen to be
conservative) and gives the design team a real ISO-anchored floor to compare future
tuning of the ad hoc model against, rather than an unmoored guess.

*Caveats on the ISO-anchored number: it uses this codebase's modeled structural
mass rather than full ISO loaded displacement (crew/payload/fuel excluded, so it
likely understates the true design pressure); Design Category C as a target not
yet demonstrated by an ISO 12217-2 assessment; k_AR without a documented stiffener-span reduction for the ama
shell; and an assumed mid-length slam location. See
`iso_design_pressure.py` for the full list.*

---

## 6. Aluminium alloy: family choice confirmed correct, documentation still open

ISO 12215-3 §4.7 classifies aluminium into non-heat-treatable (Mg-based, typically
rolled sheet/plate) and heat-treatable (Si-based, typically extruded
sections/tubes/closed profiles) families. The aka, braces, mast and gunwale are all
extruded closed-profile sections — **the heat-treatable (6000-series) family is the
correct choice per §4.7.3**, consistent with the 6061-T6 placeholder already used in
`beam_mechanics.py`.

What is still genuinely open (per the design team, no alloy/temper has been
finalized yet): ISO 12215-3 §7.3 requires a material data sheet stating chemical
composition, grade, temper, minimum mechanical properties, and — critically —
**minimum/expected mechanical properties after welding**. This does not exist yet.
It is a documentation gap to close before certification, not evidence the current
design is undersized: ISO's own tabulated values for a representative alloy
(EN AW-6061 T5/T6 closed profile) are already used throughout this page's
cross-checks as a stand-in.

One consequence worth flagging: **whether the aka-to-vaka joint ends up welded or
mechanically fastened changes the applicable ISO design stress by ~1.8×** (81 MPa
welded vs. 147 MPa unwelded/riveted, per ISO 12215-5 Table 17). This is undetermined
today because no joint design exists yet (see §4 above) — it is one more reason
that joint design is the highest-value open item.

---

## 7. Design category and safe wind speed (ISO 12217-2)

ISO 12217-2 (stability and buoyancy, sailing boats ≥ 6 m) assigns the design
category. §3.1.3 states that proas are asymmetric catamarans, so RP2 is assessed
under **Clause 7** (catamarans and trimarans), not the monohull rules.

**Target: Design Category C** (§9.2.3: steady winds up to Beaufort 6, significant
waves up to 2 m). Category B is not a realistic target. It requires a fully enclosed
boat (§7.1.2), and a maximum transverse righting lever of at least 1.3 m / BPF
(§7.8, Table 8). BPF is the bare-poles factor from §7.7, at most 1. RP2's maximum
righting lever from the GZ curve is 0.90 m heeling toward the vaka and 0.61 m toward
the ama. Category C needs 0.7 m / BPF, which RP2 meets only on the vaka side and only
if BPF is at least about 0.78; a rough estimate puts BPF near 0.8. **The Clause 7
assessment itself (Tables 8 and 9, §7.10, §7.11) has not been carried out yet.** It
needs GZ curves in the minimum operating condition (§3.5.3: light craft plus 150 kg
crew), which this repository doesn't compute. The standard doesn't say which side
governs for an asymmetric hull.

**Safe wind speed.** §7.5 b) requires a "reef sails at N knots apparent wind" figure
on a sign at the helm (Figure 9) and in the owner's manual. Annex G is the method
for calculating it, and it is the standard's counterpart to
`capsize_analysis.py`. It differs in several ways:
- it uses each sail's centroid height, not 40% up from the boom;
- heights are measured from the centre of the underwater hull profile, not the
  waterline;
- it includes hull, mast and spar windage;
- its force coefficient is about 1.10 × V² × A rather than 0.72 × V² × A, which
  includes a gust margin;
- it uses the minimum operating condition mass.

A rough sails-only estimate gives about **12 kn** (ama side, −45° tilt), against the
capsize check's 16 kn. That estimate assumes the underwater profile centre sits
0.3 m below the waterline; including windage and the lighter mass would lower it
further. Below 16 kn, §7.11.2 c) classes a catamaran as susceptible to inversion in
every category. That requires the capsize warning sign (Figure 10) and, if the boat
is habitable (§3.1.9), buoyancy when inverted (§7.12) and a means of escape (§7.13).

**Rig strength.** §7.5 b) also says the safe full-sail wind speed may be limited by
the strength of the rig, and that owner information shall use the lower of the
stability and strength limits. This is how the mast check is meant to be used:
alongside the reefing table, not as a stand-alone 25 kn pass/fail (see §1).

---

## Summary of open items

1. **Aka global dynamic loading (GLC5)** — SF 1.35 against ISO's own design
   stress. Worth a closer look; the static suspended-ama check (3.27) does not
   cover this load direction.
2. **Aka-to-vaka joint** — no design exists; a first-pass ISO-anchored rule of
   thumb passes, but this needs a real bracket/weld design once the joint geometry
   is decided.
3. **Aluminium alloy/temper** — needs to be finalized and documented per ISO
   12215-3 §7.3 (including post-weld properties), since it affects both the
   material design stress and the joint design above.
4. **GLC1 (quartering-sea torsion)** — order-of-magnitude bound computed (16.7 kNm
   at Category C), but not distributed to individual akas; ISO 12215-7 itself says
   this asymmetric arrangement needs FEM ("enhanced method"), not the simplified
   formula.
5. **Design Category** — Category C is the target (see §7) and is used throughout
   this page's ISO-anchored calculations. It still has to be demonstrated by the
   ISO 12217-2 Clause 7 assessment, which needs GZ curves in the minimum operating
   condition.
6. **Safe wind speed (ISO 12217-2 Annex G)** — not yet calculated. A rough estimate
   (about 12 kn at full sail) is below the 16 kn in-house capsize figure and would
   make RP2 susceptible to inversion in every category (§7.11.2 c)).
7. **Other local loads (ISO 12215-6 §10)** — docking, grounding, towing, anchoring,
   berthing/mooring and road transport loads "shall be considered". Only lifting is
   checked today; grounding and docking matter most for a boat that is routinely
   beached.
