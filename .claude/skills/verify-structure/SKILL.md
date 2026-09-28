---
name: verify-structure
description: Verify RP2's structural integrity against a sailing/weather condition (point of sail, wind speed, wave impact, design category, crew/loading) using the ISO-12215-traceable checks in src/structural/, and suggest a single-parameter design fix on failure. Use when asked to check if the boat "survives", "holds up", "is strong enough for", or "passes" a given wind/wave/loading/offshore-category scenario, or to suggest a structural fix.
---

# Verify structural integrity against a sailing condition

This skill drives the existing ISO-12215-traceable structural validation in
`src/structural/` against a chosen sailing/weather condition, and - on
failure - suggests a concrete single-parameter design change.

It **verifies and suggests against an existing design**. It does not
generate a new boat from conditions alone - that's a documented future
phase these same condition levers (wind, waves, direction, design category,
loading) are meant to feed into.

## 1. Resolve the boat and configuration

- `BOAT` defaults to `rp2` unless the user names another boat in
  `constant/boat/`.
- Base `CONFIGURATION` is one of `closehaul`, `beamreach`, `broadreach`,
  `goosewing`, `closehaulreefed`, `beaching` (see `constant/configuration/`).
  Pick the closest point of sail to what the user describes, or ask if it's
  genuinely ambiguous.

## 2. Resolve condition overrides

Only override what the user actually stated - leave everything else at the
configuration preset's own values (already merged into the parameter
artifact) or today's code defaults:

- **Wind speed**: knots, from the user's own words. Maps to `--wind-speed`.
- **Wave/sea state**: this is a runtime-only input - `constant/configuration/*.json`
  deliberately has no wave-height field (there's no reviewed formula linking
  a wave-height guess to impact velocity/dynamic factor). If the user gives
  wave height in a form like "1.5m waves", **ask them directly** for an
  impact velocity (m/s) and dynamic amplification factor instead of
  inventing a conversion, or use the code defaults (3.0 m/s, 2.5x) if they
  have no strong opinion. Maps to `--impact-velocity` / `--dynamic-factor`.
- **Design category** (A/B/C/D): if the user mentions offshore vs. coastal
  vs. sheltered/inshore use. Maps to `--design-category`. Defaults to `B`,
  itself an unconfirmed placeholder in this codebase
  (`beam_mechanics.ASSUMED_DESIGN_CATEGORY`) - say so when it matters to the
  result.
- **Crew mass on the aka**: if the user mentions crew standing/working on
  the aka specifically (boarding, sail handling). Maps to `--crew-mass`.
  Default 150 kg (2 people).
- **Wind side for the capsize/ama-lift check**: this check is now a hard
  pass/fail (safety_factor = max_righting_moment / heeling_moment_at_wind_speed
  must meet `--min-safety-factor`, same convention as every other check) and
  always assumes wind from the ama side (the proa's less stable direction) -
  there is currently no flag to check the other side; `--wind-from-vaka-side`
  below is aspirational, not implemented. Note in your summary that none of
  the configuration presets encode which side the ama is on relative to
  `wind_direction` either, so this side-assumption is fixed, not derived from
  the condition.
- **Reefing**: `--reefing-percentage` (0-100) now actually reduces sail area
  for both the mast test and the capsize check (it previously only affected
  the FreeCAD render geometry). If the user wants "how much do I need to reef
  to be safe at this wind speed" rather than "is this specific reefing
  level safe", use `python -m src.structural.operating_envelope` instead
  (see its `--help`, or `constant/conditions/` for example condition files) -
  it solves for the minimum reefing percentage directly rather than requiring
  you to guess-and-check a value.
- **Vessel loading condition** (more/less crew and gear aboard generally,
  not just standing on the aka): `constant/boat/*.json` has
  `deck_load_in_kg`, `sole_load_in_kg`, `ama_load_in_kg` fields that likely
  drive this via the external `shipshape.design`/`shipshape.mass` pipeline,
  but this has **not been empirically verified** in this repo (that
  toolchain wasn't available when this skill was built). If the user asks
  about a different loading condition:
  1. Write a scratch boat JSON (e.g. `constant/boat/rp2-scratch.json`) with
     those three fields adjusted.
  2. Run `make design mass gz BOAT=rp2-scratch CONFIGURATION=<config>` to
     regenerate the design/mass/gz artifacts.
  3. Diff the resulting `mass_data`/`gz_data` against the baseline - if the
     load fields didn't move the numbers, say so plainly and fall back to
     just noting the loading condition as a caveat rather than silently
     treating it as applied.
  4. If it worked, proceed to step 4 below using the scratch artifacts.

## 3. Refresh artifacts

Run `make validate-structure BOAT=<boat> CONFIGURATION=<config>` to (re)build
`PARAMETER_ARTIFACT` / `MASS_ARTIFACT` / `GZ_ARTIFACT` in `artifact/`. Skip
this if step 2's loading-condition path already produced a fresh scratch set.

## 4. Run the validator directly for the actual condition

Bypass `make` for the condition-specific run, since its pattern rule doesn't
expose ad hoc flags:

```
PYTHONPATH=<repo root> python -m src.structural \
  --parameters artifact/<boat>.<config>.parameter.json \
  --mass artifact/<boat>.<config>.mass.json \
  --gz artifact/<boat>.<config>.gz.json \
  --output <scratch>.json \
  [--wind-speed N] [--reefing-percentage N] [--min-safety-factor N]
```

`--wind-speed` only needs to be passed if overriding the configuration's own
`wind_speed_kt` - it's picked up automatically otherwise.

**Only `--parameters`, `--mass`, `--gz`, `--output`, `--wind-speed`,
`--reefing-percentage`, `--min-safety-factor` and `--quiet` actually exist on
this CLI today.** `--suggest`, `--impact-velocity`, `--dynamic-factor`,
`--design-category`, `--crew-mass`, and `--wind-from-vaka-side` (referenced
below and earlier in this file) were never implemented - they describe a
planned CLI surface, not the current one. Don't pass them; argparse will
reject unknown flags. If the user needs one of those specifically (crew mass,
design category, wave impact velocity/dynamic factor as CLI overrides rather
than editing the JSON inputs directly), say so plainly rather than
pretending the flag works.

On Windows, set `PYTHONIOENCODING=utf-8` alongside `PYTHONPATH` - the
CLI prints a checkmark character that native Windows Python can't encode
in the default console codepage otherwise.

## 5. Summarize the result

- Overall pass/fail, and each test's safety factor.
- For the four ISO-traceability tests (`iso_material_traceability`,
  `iso_aka_joint_traceability`, `iso_global_loads`,
  `iso_design_pressure_cross_check`), cite the relevant clause from
  `constant/standards/iso12215.json`.
- Call out the design category used and the capsize check's wind-side
  assumption, since both are judgement calls baked into the run, not
  measured facts.
- If reefing was applied, mention the resulting sail area reduction (mast
  test's `geometry.reefing_percentage` / `sail_area_m2` vs.
  `sail_area_m2_before_reefing`).

## 6. Present suggestions on failure

Read `results['suggestions']` (only present if `--suggest` was passed and
the run failed). Each entry is either:
- A convergent fix: `param_key`, `current_value` -> `suggested_value`,
  `achieved_safety_factor`.
- A non-convergent or informational note explaining why no single-parameter
  fix was suggested (e.g. the governing component shifted to a different
  member once the tried dimension got stiff enough - a sign the real fix
  needs two dimensions changed together, not one).

Present these in plain terms. Never apply a suggestion silently.

## 7. Applying a suggestion

If the user asks to apply a suggested fix: confirm the specific parameter
change with them, then edit the relevant `constant/boat/*.json` field
directly. Tell them that downstream artifacts (mass, CAD, renders) need
regenerating (`make design mass gz` at minimum, plus `make validate-structure`
again to confirm the fix actually holds against the full pipeline, not just
the isolated function used during suggestion search).

## Reference: what each condition flag actually changes

Flags marked **(not implemented)** appear elsewhere in this file describing
a planned CLI surface - passing them will error. Use the JSON inputs
directly (edit `constant/boat/*.json`, or - for wind/wave conditions -
`constant/conditions/*.json` with `operating_envelope.py`) until they exist.

| Flag | Affects | Source |
|---|---|---|
| `--wind-speed` | mast bending/shear/buckling test, and now the ama-lift/capsize hard cutoff too | `mast_analysis.py`, `capsize_analysis.py` |
| `--reefing-percentage` | mast test's effective sail area AND the capsize check's sail area/CE height - a single scalar applied uniformly to both masts, distinct from the per-mast `reefing_percentage_biru`/`_kuning` fields in the configuration file (which still only drive the FreeCAD render geometry, not this CLI) | `mast_analysis.py`, `capsize_analysis.py` |
| `--impact-velocity`, `--dynamic-factor` **(not implemented)** | would affect all 3 wave-slam tests + ISO pressure cross-check | `wave_slam.py`, `iso_design_pressure.py` |
| `--design-category` **(not implemented)** | would affect ISO global-loads (GLC1) + ISO pressure cross-check | `iso_global_loads.py`, `iso_design_pressure.py` |
| `--crew-mass` **(not implemented)** | would affect the aka point-load (crew standing) test | `aka_point_load.py` |
| `--wind-from-vaka-side` **(not implemented)** | would flip the ama-lift/capsize check to the other side - it's a hard pass/fail now, not informational, always checks the ama side | `capsize_analysis.py` |
| `boat_speed_kt` (from configuration) | reported alongside wave-slam results for context only - does not change the slam physics (no reviewed formula linking speed to impact velocity yet) | `validate.py` |
