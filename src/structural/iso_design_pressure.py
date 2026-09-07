"""
ISO 12215-5/12215-7 local design pressure cross-check.

Computes an ISO-anchored bottom design pressure for the ama, for comparison
against the ad hoc slam-pressure model in wave_slam.py (P = 0.5*rho*V^2*Cp
with an assumed 3 m/s impact velocity and a hand-picked Cp=1.5 and 2.5x
dynamic factor - none of those three numbers are ISO-derived).

MONOHULL-APPLICABILITY NOTE: ISO 12215-5 Section 9 design pressures are
written for monohulls. This module does NOT apply them directly to the ama.
Instead it uses ISO 12215-7 Clause 9.4 ("Design pressure for trimaran
floats"), which explicitly states the float bottom/side pressure uses the
SAME base formula as ISO 12215-5's sailing-craft bottom pressure (Table 13 /
Part 7 Table 6), but with the float's own length substituted for LWL in the
k_L (longitudinal distribution) factor. This is the ISO-sanctioned way to get
a float/outrigger pressure without misapplying a monohull formula - treating
the single ama as the "trimaran float" analogue, same adaptation used in
iso_global_loads.py for GLC5.

Every formula below is explicitly marked with its governing clause. Where an
input this codebase's parametric model doesn't provide (design category,
panel design area, longitudinal position of the loaded panel) is assumed,
that assumption is stated inline and in the caveats list - not silently
resolved.

See constant/standards/iso12215.json for citation details.
"""

from typing import Dict, Any

from .lifting_sling import get_total_boat_mass

ASSUMED_DESIGN_CATEGORY = 'B'  # see iso_global_loads.py - same unconfirmed placeholder
K_DC_BY_CATEGORY = {'A': 1.0, 'B': 0.8, 'C': 0.6, 'D': 0.4}

# ISO 12215-5 8.3: sailing/displacement craft use k_DYN=3 for k_L purposes
# (k_DYN itself is not used directly in the bottom pressure formula for
# non-planing craft, only inside k_L below).
K_DYN_SAILING = 3.0

# Assumed longitudinal position of the wave-slam patch on the ama, as a
# fraction of float length aft of the transom (x/L_FLOAT). Mid-length is
# used as a representative value for a slam check - the actual worst-case
# position depends on real wave-impact geometry not modeled here.
ASSUMED_X_OVER_L = 0.5


def calculate_k_dc() -> float:
    """ISO 12215-5 8.2, Table 6: design category factor k_DC."""
    return K_DC_BY_CATEGORY[ASSUMED_DESIGN_CATEGORY]


def calculate_k_l(x_over_l: float = ASSUMED_X_OVER_L, k_dyn: float = K_DYN_SAILING) -> float:
    """
    ISO 12215-5 8.4, Table 8: longitudinal pressure distribution factor k_L.

    k_L = (1.667 - 0.222*k_DYN) * (x/LWL) + 0.133*k_DYN, capped at 1.0

    For the ama, x/LWL is replaced by x/L_FLOAT per ISO 12215-7 9.4.1.
    """
    k_l = (1.667 - 0.222 * k_dyn) * x_over_l + 0.133 * k_dyn
    return min(k_l, 1.0)


def calculate_k_ar(m_ldc_kg: float, design_area_m2: float, is_stiffener: bool = False) -> float:
    """
    ISO 12215-5 8.5, Table 9: area pressure reduction factor k_AR.

    k_AR = k_R * 0.1 * m_LDC^0.15 / A_D^0.3, clamped to [0, 1]

    k_R for sailing craft bottom/side stiffeners = 1 - 2e-4 * l_u (l_u =
    unsupported span, mm) - the ama has no documented internal frame/former
    spacing in this codebase's parametric model, so k_R is conservatively
    taken as 1.0 here (i.e. no additional reduction from stiffener spacing) -
    flagged as an approximation, not a real span-based k_R.
    """
    k_r = 1.0  # approximation - see docstring
    if design_area_m2 <= 0:
        return 1.0
    k_ar = k_r * 0.1 * (m_ldc_kg ** 0.15) / (design_area_m2 ** 0.3)
    return max(0.0, min(k_ar, 1.0))


def calculate_ama_bottom_pressure(params: Dict[str, Any],
                                   mass_data: Dict[str, Any],
                                   design_area_m2: float) -> Dict[str, Any]:
    """
    ISO 12215-7 9.4 + ISO 12215-5 9.2, Table 13: sailing-craft bottom design
    pressure, applied to the ama as a "trimaran float" analogue.

    P_BS_BASE = (2*m_LDC^0.3 + 18) * k_SLS   [k_SLS=1, RP2 is not a "light
    and stable" sailing craft per 8.7 - not modeled, assumed 1]
    P_BS = max(P_BS_BASE * k_AR * k_DC * k_L, P_BS_MIN)
    """
    mass_breakdown = get_total_boat_mass(mass_data)
    m_ldc_kg = mass_breakdown['total_mass_kg']  # whole-craft mass, per ISO - not just the ama

    ama_length_mm = params.get('ama_length', 9300)
    ama_length_m = ama_length_mm / 1000

    k_dc = calculate_k_dc()
    k_l = calculate_k_l()
    k_ar = calculate_k_ar(m_ldc_kg, design_area_m2)
    k_sls = 1.0  # ISO 12215-5 8.7 not evaluated - assumed neutral

    p_bs_base_kpa = (2 * (m_ldc_kg ** 0.3) + 18) * k_sls
    p_bs_kpa = p_bs_base_kpa * k_ar * k_dc * k_l

    # ISO minimum floor (ISO 12215-5 Table 13, plating): not evaluated in
    # full (needs LWL, T_C draught) - the unreduced base*kDC*kL is reported
    # alongside as a sanity bound instead of computing the exact MIN term.

    return {
        'clause': 'ISO 12215-7 9.4 (float pressure) + ISO 12215-5 9.2 Table 13 (base formula)',
        'proa_adaptation': 'Ama treated as "trimaran float" per ISO 12215-7 9.4.1 (float length substituted for LWL in k_L).',
        'inputs': {
            'm_ldc_kg_whole_craft': round(m_ldc_kg, 1),
            'ama_length_m': round(ama_length_m, 2),
            'design_area_m2': round(design_area_m2, 3),
            'design_category_assumed': ASSUMED_DESIGN_CATEGORY,
            'k_dc': k_dc,
            'k_l': round(k_l, 3),
            'k_ar': round(k_ar, 3),
            'k_sls_assumed': k_sls,
        },
        'p_bs_base_kpa': round(p_bs_base_kpa, 2),
        'p_bs_design_kpa': round(p_bs_kpa, 2),
        'caveats': [
            'm_LDC is this codebase\'s modeled structural mass, not the full ISO loaded displacement (crew/payload/fuel excluded) - likely understates the true design pressure.',
            'Design category B is an unconfirmed placeholder.',
            'k_AR uses k_R=1.0 (no stiffener-span reduction) because the ama has no documented internal frame/former spacing in the parametric model - a real k_R would likely reduce this pressure further.',
            'k_L assumes the slam patch is at mid-ama-length (x/L=0.5) - the true worst-case position is not modeled.',
            'ISO Table 13\'s MIN pressure floor is not evaluated here - only the base*k_AR*k_DC*k_L term.',
        ],
    }


def compare_to_wave_slam_model(params: Dict[str, Any], mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cross-check: compute the ISO-anchored ama bottom pressure at the same
    effective area wave_slam.py uses, and compare directly to wave_slam.py's
    ad hoc pressure assumption (Cp=1.5, V=3 m/s, no ISO basis for either
    number).
    """
    from .wave_slam import estimate_wave_slam_force

    slam_data = estimate_wave_slam_force(params, impact_velocity_ms=3.0, dynamic_factor=2.5)
    effective_area_m2 = slam_data['effective_area_m2']

    iso_pressure = calculate_ama_bottom_pressure(params, mass_data, effective_area_m2)

    ad_hoc_static_kpa = slam_data['slam_pressure_kpa']  # before the 2.5x dynamic factor
    ad_hoc_dynamic_kpa = ad_hoc_static_kpa * slam_data['dynamic_factor']

    iso_kpa = iso_pressure['p_bs_design_kpa']

    return {
        'test_name': 'iso_design_pressure_cross_check',
        'description': 'ISO 12215-7 float bottom pressure vs. wave_slam.py ad hoc slam pressure model',
        'passed': True,  # Always passes - informational cross-check, not a pass/fail against a load case
        'wave_slam_py_model': {
            'static_pressure_kpa': ad_hoc_static_kpa,
            'dynamic_pressure_kpa (after 2.5x factor)': ad_hoc_dynamic_kpa,
            'basis': 'P = 0.5*rho_seawater*V^2*Cp, V=3 m/s, Cp=1.5 (hand-picked for "rounded shape"), then x2.5 dynamic factor - none of V, Cp, or the 2.5x factor are ISO-derived.',
        },
        'iso_anchored_model': iso_pressure,
        'comparison': {
            'iso_vs_ad_hoc_dynamic_ratio': round(iso_kpa / ad_hoc_dynamic_kpa, 2) if ad_hoc_dynamic_kpa > 0 else None,
            'note': (
                'If this ratio is well below 1.0, the existing ad hoc model '
                'is more conservative than this ISO-anchored estimate (a '
                'reasonable outcome, since wave_slam.py\'s 3 m/s + 2.5x '
                'factors were chosen to be deliberately conservative). If it '
                'is above 1.0, the ad hoc model may be under-predicting '
                'slam pressure relative to what ISO 12215-7 would estimate.'
            ),
        },
        'summary': {
            'result': 'INFO',
            'iso_bottom_pressure_kpa': iso_kpa,
            'ad_hoc_dynamic_pressure_kpa': ad_hoc_dynamic_kpa,
            'iso_vs_ad_hoc_ratio': round(iso_kpa / ad_hoc_dynamic_kpa, 2) if ad_hoc_dynamic_kpa > 0 else None,
        },
    }
