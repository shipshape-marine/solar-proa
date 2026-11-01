"""
Two-sail trim: with the foresail's rig rotation locked (e.g. at the best
angle trim.py found for it alone), which rig rotation of the aft sail gives
the boat the most total driving force at one apparent wind angle (AWA).

Both sails are placed on the boat with geometry.rig_surface: vaka along y,
the bow (the end the wind comes from) at +y, foresail mast at
y = +mast_distance_from_center and aft mast at -mast_distance_from_center.
The wind comes from the -x side, AWA off the bow, so it blows along
(sin AWA, -cos AWA, 0) and each sail meets it at alpha = AWA - rotation,
as in trim.py. Masts, spars and hull are not modelled.

Each aft rotation is its own geometry, so it gets its own mesh and one
flow case. A 'fore_alone' config - the foresail alone in the same domain -
checks the boat-frame setup against the trim sweep and is the baseline for
how much the aft sail changes the foresail's drive.

The aft sail changes the flow the foresail sees, so once the best aft
rotation is known, extend_pair_sweep can add configs with the foresail at
other rotations (aft locked) to re-check the foresail's best angle.

Per-sail coefficients use that sail's own area, in the boat frame:
C_drive = F_y / (q A) toward the bow, C_heel = F_x / (q A) toward leeward.
Both sails have the same area, so the boat's total is their mean.

Layout written under the run directory:

    sweep.json            what was generated - read by build_pair_report
    Allrun                meshes and runs every config, skipping finished ones
    fore_alone/mesh/      foresail only
    fore_alone/case/
    aft_r<RR>/mesh/       both sails, aft sail at rig rotation RR
    aft_r<RR>/case/
    fore_r<FF>_aft_r<RR>/ both sails, foresail at FF instead of the sweep's locked rotation
"""

import json
import math
import os
from typing import Any, Dict, List, Optional

from .case import (AIR_DENSITY, BASE_CELL_M, MESH_PRESETS, REFERENCE_SPEED, _domain, _script,
                   angle_tag, write_flow_case, write_multi_mesh_case)
from .geometry import min_gap_m, rig_surface
from .postprocess import CONVERGENCE_WARNING, mean_force_moment
from .trim import _parabola_peak

# Skip aft rotations whose sail comes closer than this to the foresail.
# min_gap_m reads about one grid cell (~0.1 m) for surfaces that cross,
# and a slot needs a few coarse-mesh cells (31 mm at sail level 6) across it.
MIN_GAP_M = 0.15

SAILS = ('fore', 'aft')


def wind_directions(awa_deg: float) -> Dict[str, List[float]]:
    """Unit drag (along the wind) and lift (toward leeward +x) directions, AWA off the bow (+y)."""
    a = math.radians(awa_deg)
    return {
        'drag_dir': [math.sin(a), -math.cos(a), 0.0],
        'lift_dir': [math.cos(a), math.sin(a), 0.0],
    }


def _surface(sweep: Dict[str, Any], params: Dict[str, Any], sail: str,
             rotation: float) -> Dict[str, Any]:
    mast_y = params['mast_distance_from_center'] * (1 if sail == 'fore' else -1)
    return rig_surface(params, 0, params['sail_camber_biru'], sweep['sail_angle_deg'], rotation,
                       mast_y, chord_camber_pct=sweep['chord_camber_pct'])


def _add_config(run_dir: str, sweep: Dict[str, Any], params: Dict[str, Any],
                fore_rotation: float, aft_rotation: Optional[float], n_procs: int) -> Dict[str, Any]:
    """Write one config's mesh and flow case and return its sweep.json entry."""
    surfaces = {'sail_fore': _surface(sweep, params, 'fore', fore_rotation)}
    if aft_rotation is None:
        name, gap = 'fore_alone', None
    else:
        name = f"aft_r{angle_tag(aft_rotation)}"
        if fore_rotation != sweep['fore_rotation_deg']:
            name = f"fore_r{angle_tag(fore_rotation)}_{name}"
        surfaces['sail_aft'] = _surface(sweep, params, 'aft', aft_rotation)
        gap = round(min_gap_m(surfaces['sail_fore']['triangles'],
                              surfaces['sail_aft']['triangles']), 3)
        if gap < sweep['min_gap_threshold_m']:
            raise ValueError(f"fore {fore_rotation} / aft {aft_rotation} deg puts the sails {gap} m "
                             f"apart (< {sweep['min_gap_threshold_m']} m) - too close to mesh")

    dom = sweep['domain']
    for s in surfaces.values():
        if any(abs(v) > dom['max'][0] - 2 * sweep['chord_m']
               for v in s['bounds_m']['min'][:2] + s['bounds_m']['max'][:2]):
            raise ValueError(f"{name}: sail too close to the domain edge")

    preset = MESH_PRESETS[sweep['mesh']]
    write_multi_mesh_case(os.path.join(run_dir, name, 'mesh'), surfaces, preset['sail_level'],
                          n_procs, dom, wake_center=(0.0, 0.0), wake_radius=2.0 * sweep['chord_m'])
    # Per-sail moments about the sea surface below that sail, so
    # postprocess.py's centre of pressure height formula holds
    groups = {f"forces_{n[len('sail_'):]}": (f"{n}.*", [s['centroid_m'][0], s['centroid_m'][1], 0.0])
              for n, s in surfaces.items()}
    write_flow_case(os.path.join(run_dir, name, 'case'),
                    wind_directions(sweep['apparent_wind_angle_deg'])['drag_dir'],
                    n_procs, preset['end_time'], groups)

    rotations = {'fore': fore_rotation, 'aft': aft_rotation}
    return {
        'name': name,
        'aft_rotation_deg': aft_rotation,
        'min_gap_m': gap,
        'sails': {n[len('sail_'):]: {'function': f"forces_{n[len('sail_'):]}",
                                     'rig_rotation_deg': rotations[n[len('sail_'):]],
                                     'reference_area_m2': s['reference_area_m2'],
                                     'geometric_ce_height_m': s['geometric_ce_height_m']}
                  for n, s in surfaces.items()},
    }


def _write_allrun(run_dir: str, sweep: Dict[str, Any]) -> None:
    lines = ['#!/bin/sh', 'cd "${0%/*}" || exit', 'set -e', '',
             '# Skips meshes with a finished checkMesh and cases whose solver log ended,',
             '# so rerunning picks up where an interrupted run stopped', '']
    for c in sweep['configs']:
        mesh, case = f"{c['name']}/mesh", f"{c['name']}/case"
        # Invoked via sh: execute bits don't survive writing from Windows
        lines.append(f'if ! grep -qs "^End" ./{mesh}/log.checkMesh; then '
                     f'echo "== {c["name"]}: mesh"; rm -rf ./{mesh}/processor* ./{mesh}/log.*; '
                     f'sh ./{mesh}/Allrun; fi')
        lines.append(f'if ! grep -qs "^End" ./{case}/log.simpleFoam; then '
                     f'echo "== {c["name"]}: case"; rm -rf ./{case}/processor* ./{case}/log.* '
                     f'./{case}/postProcessing; sh ./{case}/Allrun; fi')
    _script(os.path.join(run_dir, 'Allrun'), '\n'.join(lines) + '\n')


def _check_rotations(awa_deg: float, rotations: List[float]) -> None:
    for r in rotations:
        if not awa_deg - 90 <= r <= awa_deg:
            raise ValueError(f"rig rotation {r} deg gives angle of attack {awa_deg - r} deg "
                             f"at AWA {awa_deg} - must be 0-90")
    if len(set(rotations)) != len(rotations):
        raise ValueError(f"duplicate rig rotations: {sorted(rotations)}")


def generate_pair_sweep(run_dir: str, params: Dict[str, Any], parameters_path: str,
                        awa_deg: float, fore_rotation_deg: float, aft_rotations: List[float],
                        sail_angle_deg: float, chord_camber_pct: Optional[float],
                        mesh: str, n_procs: int, min_gap: float = MIN_GAP_M) -> Dict[str, Any]:
    """Write the fore_alone config and one two-sail config per aft rotation, plus sweep.json and Allrun."""
    if mesh not in MESH_PRESETS:
        raise ValueError(f"mesh must be one of {list(MESH_PRESETS)}, got {mesh!r}")
    _check_rotations(awa_deg, [fore_rotation_deg])
    _check_rotations(awa_deg, aft_rotations)
    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise FileExistsError(f"{run_dir} already exists and is not empty - pick a new run "
                              "directory so earlier results aren't overwritten")

    preset = MESH_PRESETS[mesh]
    chord = params['yard_length'] / 1000
    sweep = {
        'type': 'pair',
        'parameters': parameters_path,
        'apparent_wind_angle_deg': awa_deg,
        'fore_rotation_deg': fore_rotation_deg,
        'sail_angle_deg': sail_angle_deg,
        'chord_camber_pct': chord_camber_pct,
        'mast_distance_from_center_mm': params['mast_distance_from_center'],
        'mesh': mesh,
        'sail_level': preset['sail_level'],
        'base_cell_m': BASE_CELL_M,
        'end_time': preset['end_time'],
        'reference_speed_ms': REFERENCE_SPEED,
        'air_density': AIR_DENSITY,
        'min_gap_threshold_m': min_gap,
        'chord_m': chord,
        'configs': [],
    }
    # One domain for every config - the single-sail sweep's, centred on the
    # boat - so configs differ only in the sails. Sized for the tallest sail.
    top = _surface(sweep, params, 'fore', fore_rotation_deg)['bounds_m']['max'][2]
    sweep['domain'] = _domain(chord, top)

    os.makedirs(run_dir, exist_ok=True)
    for aft in [None] + sorted(aft_rotations):
        sweep['configs'].append(_add_config(run_dir, sweep, params, fore_rotation_deg, aft, n_procs))

    _write_allrun(run_dir, sweep)
    with open(os.path.join(run_dir, 'sweep.json'), 'w') as f:
        json.dump(sweep, f, indent=2)
    return sweep


def extend_pair_sweep(run_dir: str, params: Dict[str, Any], aft_rotations: List[float],
                      n_procs: int, fore_rotations: Optional[List[float]] = None) -> List[str]:
    """
    Add configs to an existing pair sweep: every combination of the given
    foresail rotations (default: the sweep's locked one) and aft rotations -
    e.g. to refine around the best aft rotation, or to re-check the
    foresail with the aft sail locked. Rewrites Allrun, which skips finished
    configs, so rerunning it runs only the new ones. Returns their names.
    """
    with open(os.path.join(run_dir, 'sweep.json'), 'r') as f:
        sweep = json.load(f)
    if sweep.get('type') != 'pair':
        raise ValueError(f"{run_dir}/sweep.json is not a pair sweep (use pair-setup)")
    fore_rotations = fore_rotations or [sweep['fore_rotation_deg']]
    _check_rotations(sweep['apparent_wind_angle_deg'], fore_rotations)
    _check_rotations(sweep['apparent_wind_angle_deg'], aft_rotations)
    pairs = [(f, a) for f in sorted(fore_rotations) for a in sorted(aft_rotations)]
    clash = sorted(set(pairs) & {(c['sails']['fore']['rig_rotation_deg'], c['aft_rotation_deg'])
                                 for c in sweep['configs']})
    if clash:
        raise ValueError(f"(fore, aft) rotations {clash} are already in the sweep")

    added = [_add_config(run_dir, sweep, params, f, a, n_procs) for f, a in pairs]
    sweep['configs'].extend(added)
    _write_allrun(run_dir, sweep)
    with open(os.path.join(run_dir, 'sweep.json'), 'w') as f:
        json.dump(sweep, f, indent=2)
    return [c['name'] for c in added]


def _sail_result(case_dir: str, entry: Dict[str, Any], q: float) -> Dict[str, Any]:
    m = mean_force_moment(case_dir, entry['function'])
    f, qa = m.pop('force'), q * entry['reference_area_m2']
    return {'c_drive': round(f[1] / qa, 4), 'c_heel': round(f[0] / qa, 4), **m}


def build_pair_report(run_dir: str) -> Dict[str, Any]:
    """Per-sail and total drive for every aft rotation, and the best one."""
    with open(os.path.join(run_dir, 'sweep.json'), 'r') as f:
        sweep = json.load(f)
    if sweep.get('type') != 'pair':
        raise ValueError(f"{run_dir}/sweep.json is not a pair sweep (use pair-setup)")
    q = 0.5 * sweep['air_density'] * sweep['reference_speed_ms']**2

    warnings: List[str] = []
    fore_alone, rows = None, []
    for c in sweep['configs']:
        case_dir = os.path.join(run_dir, c['name'], 'case')
        sails = {}
        for sail, entry in c['sails'].items():
            r = _sail_result(case_dir, entry, q)
            if r['force_relative_std'] > CONVERGENCE_WARNING:
                warnings.append(f"{c['name']} ({sail}): force fluctuates "
                                f"{r['force_relative_std']:.1%} over the averaging window")
            sails[sail] = r
        if c['aft_rotation_deg'] is None:
            fore_alone = sails['fore']
            continue
        fore_rotation = c['sails']['fore']['rig_rotation_deg']
        rows.append({
            'fore_rotation_deg': fore_rotation,
            'fore_angle_of_attack_deg': sweep['apparent_wind_angle_deg'] - fore_rotation,
            'aft_rotation_deg': c['aft_rotation_deg'],
            'aft_angle_of_attack_deg': sweep['apparent_wind_angle_deg'] - c['aft_rotation_deg'],
            'min_gap_m': c['min_gap_m'],
            'fore': sails['fore'],
            'aft': sails['aft'],
            'c_drive_total': round((sails['fore']['c_drive'] + sails['aft']['c_drive']) / 2, 4),
            'c_heel_total': round((sails['fore']['c_heel'] + sails['aft']['c_heel']) / 2, 4),
        })
    rows.sort(key=lambda r: (r['fore_rotation_deg'], r['aft_rotation_deg']))

    best = None
    if rows:
        top = max(rows, key=lambda r: r['c_drive_total'])
        best = {'fore_rotation_deg': top['fore_rotation_deg'],
                'aft_rotation_deg': top['aft_rotation_deg'],
                'c_drive_total': top['c_drive_total']}
        # Along each sail's rotation, through the best config with the other sail held
        for sail, other in (('aft', 'fore'), ('fore', 'aft')):
            key = f'{sail}_rotation_deg'
            line = sorted((r for r in rows
                           if r[f'{other}_rotation_deg'] == top[f'{other}_rotation_deg']),
                          key=lambda r: r[key])
            if len(line) < 2:
                continue
            i = line.index(top)
            if 0 < i < len(line) - 1:
                peak = _parabola_peak([[r[key], r['c_drive_total']] for r in line[i - 1:i + 2]])
                if peak is not None:
                    best[f'interpolated_{key}'] = round(peak, 1)
            else:
                warnings.append(f"best total drive is at the edge of the {sail} sweep ({sail} "
                                f"rotation {top[key]} deg) - the optimum may lie beyond it")

    return {
        'apparent_wind_angle_deg': sweep['apparent_wind_angle_deg'],
        'fore_rotation_deg': sweep['fore_rotation_deg'],
        'sail_angle_deg': sweep['sail_angle_deg'],
        'chord_camber_pct': sweep['chord_camber_pct'],
        'mesh': sweep['mesh'],
        'parameters': sweep['parameters'],
        'run_dir': run_dir,
        'coefficient_note': ("Per-sail coefficients use that sail's area, boat frame: drive toward "
                             "the bow, heel toward leeward. Totals are the mean of the two sails "
                             "(equal areas), i.e. normalised by the combined area."),
        'fore_alone': fore_alone,
        'best': best,
        'convergence_warnings': warnings,
        'rows': rows,
    }
