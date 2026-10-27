# Sail CFD: OpenFOAM lift/drag polar

Generates the sail polar (C_L, C_D vs. angle of attack, per reefing level)
that `src/structural/operating_envelope.py` uses in place of
`constant/sail_polar/placeholder.json`.

## Install OpenFOAM (WSL Ubuntu, once)

The cases target **OpenFOAM v2412 from openfoam.com**. The openfoam.org
releases use different dictionary names and won't run these cases as-is.

```sh
curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt-get install openfoam2412-default
openfoam2412          # opens a shell with the OpenFOAM environment loaded
```

## Run

From the repo root on Windows (or in WSL):

```sh
# 1. Generate cases. Start small: one reef level on the coarse mesh.
python -m src.sail_cfd setup --parameters artifact/rp2.closehaul.parameter.json \
    --run-dir cfd_runs/rp2_coarse_r0 --reef 0 --mesh coarse --procs 12

# 2. Run inside the OpenFOAM shell (WSL sees the repo under /mnt/c/...)
openfoam2412 -c "sh ./cfd_runs/rp2_coarse_r0/Allrun"

# 3. Build the polar
python -m src.sail_cfd postprocess --run-dir cfd_runs/rp2_coarse_r0 \
    --output constant/sail_polar/rp2_openfoam.json

# 4. Use it
python -m src.structural.operating_envelope ... --sail-polar constant/sail_polar/rp2_openfoam.json
```

### Trim study: best rig rotation for one sail

`trim-setup` simulates one unreefed sail on its own (the other rig is not in
the model) at a single apparent wind angle, one case per rig rotation
(sail chord vs. hull centerline, so alpha = AWA - rotation). `trim` then
ranks the rotations by driving coefficient C_L sin(AWA) - C_D cos(AWA),
also listing the heeling coefficient and drive/heel ratio, and fits a
parabola through the best three for an in-between optimum.

```sh
python -m src.sail_cfd trim-setup --parameters artifact/rp2.closehaul.parameter.json \
    --run-dir cfd_runs/rp2_trim_c45 --awa 45 --chord-camber 10
openfoam2412 -c "sh ./cfd_runs/rp2_trim_c45/Allrun"
python -m src.sail_cfd trim --run-dir cfd_runs/rp2_trim_c45
```

By default the yard and boom are horizontal (`--sail-angle 0`). At that
tilt the CAD sail has no chordwise camber at all, since its
`sail_camber_*` curve (a cylinder radius) runs only from yard to boom. So
`--chord-camber` swaps in a doubly curved sail: flat along the yard, boom,
luff and leech, deepest at the centre, with mid-height camber of that % of
chord. The deepest point is at mid-chord, so the sail is the same from
either end, as a shunting proa's sail must be.

Run directories are big, so `cfd_runs/` is gitignored. Commit only the
polar JSON. Running WSL cases on `/mnt/c` is slow. For long sweeps, generate
the cases into the WSL filesystem (e.g. `~/cfd_runs/...`) and copy
`sweep.json` and `postProcessing/` back for the postprocess step.

## What is modelled

- **Geometry:** the CAD sail surface (`geometry.py` mirrors
  `src/design/rotating.py`), meshed as a zero-thickness baffle. The camber
  and tilt come from one rig's `sail_camber_*` and `sail_angle_*`.
- **Flow:** steady RANS (`simpleFoam`, k-ω SST, wall functions) with
  uniform wind. The sea surface and domain top are slip walls. The four
  sides are freestream, so one mesh per reef level serves every angle of
  attack.
- **Output:** C_L and C_D normalised by the same sail area the structural
  checks use, plus the centre-of-pressure height above the waterline.

## Limits: read before trusting the numbers

- **The CAD sail shape is not a real sail shape.** It is curved vertically
  (between yard and boom) and flat along the chord. A real sail also has
  chordwise camber, which raises peak C_L. The CFD is only as good as this
  geometry. The trim study's `--chord-camber` shape is an idealised
  parabola, not a measured flying shape either.
- **Single sail only.** There is no mast, spars, hull or second rig, and
  no interaction between the two sails.
- **Rigid sail.** A real sail changes shape under load (no
  fluid-structure coupling), and there are no gusts and no boat motion.
- **Steady RANS is weakest past stall (alpha ≳ 25°) and broadside.** Those
  cases oscillate. The post-processor averages the last 20% of iterations
  and flags any case whose force still varies by more than 2%.
- **No atmospheric wind gradient.** The wind speed is the same at every
  height, as in ISO 12215-10.

## Verification (the CFD solving its own model correctly)

1. **Mesh independence:** run the same reef/alpha set (e.g. alpha 20 and 90)
   on `coarse`, `medium` and `fine`. Use the finest mesh whose C_L and C_D
   stay within about 3% of the next one up.
2. **Convergence:** check `postprocess` warnings and the residuals in each
   case's `log.simpleFoam`.
3. **y+:** run `simpleFoam -postProcess -func yPlus -latestTime` in a case.
   Wall functions want 30 < y+ < 300 on most of the sail.
4. **Centre of pressure:** compare each point's `center_of_pressure_height_m`
   with the polar's `geometric_ce_height_m`, which is the CE height the
   capsize check assumes.

## Validation (the model matching reality)

CFD agreeing with itself doesn't prove it matches real sails. Compare against:

- **Flat plate broadside:** C_D ≈ 1.1–1.2 for aspect ratio ≈ 1 (Hoerner,
  *Fluid-Dynamic Drag*). The alpha = 90 point should land close.
- **Published sail and crab-claw wind-tunnel data** (e.g. Marchaj, *Sail
  Performance*). Compare the shape and peak of the polar, not exact values.
- **On-water measurements** are the real test: a load cell at the mast
  partner, a heel-angle logger and a masthead anemometer, compared with
  `operating_envelope`'s predicted force at the measured apparent wind.
