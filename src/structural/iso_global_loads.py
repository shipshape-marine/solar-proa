"""
ISO 12215-7 multihull global load cross-check for the aka/crossbeam system.

ISO 12215-7:2020 ("Determination of loads for multihulls") is the correct
governing standard for global crossbeam loads - NOT ISO 12215-5, which is
written for monohulls and is used elsewhere in this package only for the
vaka's own local hull-panel pressures (see iso_design_pressure.py).

APPLICABILITY CAVEAT (read before trusting any number here): ISO 12215-7's
worked formulas and Figure 9 structural-arrangement categories assume
SYMMETRIC catamarans (two equal hulls) or trimarans (one main hull + two
equal floats). RP2 is a Pacific-proa layout: ONE main hull (vaka) + ONE
asymmetric outrigger float (ama). There is no literal fit:

- GLC5 (longitudinal force on one hull/float, Table 15) maps reasonably
  cleanly: the single ama is treated as the closest analogue to a "trimaran
  float", and the resulting force is distributed to the akas by relative
  stiffness exactly as Part 7 prescribes. This is implemented below.
- GLC1 (diagonal torsional moment in quartering sea, Table 13 + Annex D) does
  NOT map cleanly: Annex D's differential-bending distribution method assumes
  the torsional moment is reacted by TWO OR MORE crossbeams connecting the
  SAME TWO hulls twisting against each other. RP2 has only one outrigger, so
  there is no second hull for the akas to differentially react against in the
  way Annex D models. This module computes the order-of-magnitude torsional
  moment from Table 13 as a bound, but deliberately does NOT force it through
  Annex D's per-beam distribution - ISO 12215-7 12.3.3 itself says a
  non-typical arrangement needs the "enhanced method" (FEM), not the
  simplified method, and a single-outrigger proa is exactly that case.

See constant/standards/iso12215.json for citation details.
"""

import math
from typing import Dict, Any

from .beam_mechanics import (
    ISO_AL_DESIGN_STRESS_WELDED_MPA, GRAVITY,
    calculate_rhs_section_properties,
)
from .lifting_sling import get_total_boat_mass


# Design category factor k_DC (ISO 12215-5 8.2, reused by Part 7 Table 13).
# RP2's design category has not been formally declared yet; Category B
# (coastal, day-tourism in Singapore/Indonesia waters) is assumed as a
# placeholder and MUST be confirmed by the designer per ISO 12217 before
# this number is used for certification.
ASSUMED_DESIGN_CATEGORY = 'B'
K_DC_BY_CATEGORY = {'A': 1.0, 'B': 0.8, 'C': 0.6, 'D': 0.4}

# k_DYNM (dynamic load factor for GLC1, ISO 12215-7 Table 13) is referenced
# in the Table 13 formula but its own definition table was not captured in
# this extraction pass (only the formula that consumes it). As a documented
# placeholder, this reuses ISO 12215-5 8.3's k_DYN=3 for sailing/displacement
# craft - VERIFY against the Part 7 source PDF before relying on this number.
ASSUMED_K_DYNM = 3.0


def calculate_glc1_torsional_moment(params: Dict[str, Any],
                                     mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ISO 12215-7 12.5, Table 13 - GLC1 diagonal torsional moment in quartering
    sea. Order-of-magnitude bound only - see module docstring for why this is
    NOT distributed to individual akas via Annex D on this hull form.

    M_TD = 0.5 * k_DC * m_LDC * 9.81 * k_DYNM * 0.076 * L_DIAG / 1000 (kNm)
    L_DIAG = sqrt(LWL^2 + BCB^2)
    """
    mass_breakdown = get_total_boat_mass(mass_data)
    m_ldc_kg = mass_breakdown['total_mass_kg']  # structural mass only - see caveat below

    lwl_mm = params['vaka_length']  # approximation: no separate LWL param exists
    bcb_mm = params['aka_length']   # approximation: vaka/ama centreline spacing

    lwl_m = lwl_mm / 1000
    bcb_m = bcb_mm / 1000
    l_diag_m = math.sqrt(lwl_m ** 2 + bcb_m ** 2)

    k_dc = K_DC_BY_CATEGORY[ASSUMED_DESIGN_CATEGORY]

    m_td_kNm = 0.5 * k_dc * m_ldc_kg * GRAVITY * ASSUMED_K_DYNM * 0.076 * l_diag_m / 1000

    return {
        'clause': 'ISO 12215-7 12.5, Table 13 (GLC1)',
        'inputs': {
            'm_ldc_kg': round(m_ldc_kg, 1),
            'design_category_assumed': ASSUMED_DESIGN_CATEGORY,
            'k_dc': k_dc,
            'k_dynm_assumed': ASSUMED_K_DYNM,
            'lwl_m_approx': round(lwl_m, 2),
            'bcb_m_approx': round(bcb_m, 2),
            'l_diag_m': round(l_diag_m, 2),
        },
        'torsional_moment_kNm': round(m_td_kNm, 2),
        'torsional_moment_Nm': round(m_td_kNm * 1000, 0),
        'caveats': [
            'm_LDC uses this codebase\'s modeled structural mass, not full ISO loaded displacement (crew/payload/fuel not included) - likely understates the true design moment.',
            'Design category B is an unconfirmed placeholder - must be set by the designer per ISO 12217.',
            'k_DYNM is assumed equal to ISO 12215-5 k_DYN=3 (sailing/displacement) - the Part 7-specific k_DYNM definition table was not captured in this extraction pass; verify against source before relying on this number.',
            'This is an ORDER-OF-MAGNITUDE bound only. It is deliberately NOT distributed to individual akas via ISO 12215-7 Annex D, because that method assumes the torsional moment is reacted by crossbeams twisting between TWO hulls of the same type - RP2 has only one outrigger, so there is no second hull for the akas to react against in the way Annex D models. Per ISO 12215-7 12.3.3, a non-typical arrangement like this needs the "enhanced method" (FEM), not the simplified method used here.',
        ],
    }


def calculate_glc5_longitudinal_force(params: Dict[str, Any],
                                       mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ISO 12215-7 12.10, Table 15 - GLC5 longitudinal force on one hull/float
    (e.g. hitting a floating object or a steep wave), distributed to the akas
    by relative stiffness. The single ama is treated as the closest available
    analogue to a "trimaran float" (F_LT = min(5*m_LDC, 5*m_FLOAT) kN) - this
    maps onto the proa's single-outrigger geometry more directly than GLC1
    does, since it is a force on ONE float/hull reacted by the crossbeams
    connecting it to the rest of the structure, which is exactly RP2's aka
    arrangement.
    """
    from .aka_analysis import extract_outrigger_mass

    mass_breakdown = get_total_boat_mass(mass_data)
    m_ldc_kg = mass_breakdown['total_mass_kg']

    tip_mass_kg, distributed_mass_kg, _ = extract_outrigger_mass(mass_data)
    m_float_kg = tip_mass_kg + distributed_mass_kg

    # ISO 12215-7 Table 15 item 1: F_LT = min(5*m_LDC, 5*m_FLOAT), result in
    # kN with mass in tonnes (Note 1: this corresponds to ~0.5g deceleration,
    # i.e. 5 ~= 0.5*9.81/1000*1000 already calibrated to kN from mass in kg).
    f_lt_kN = min(5 * m_ldc_kg / 1000, 5 * m_float_kg / 1000)
    f_lt_n = f_lt_kN * 1000

    aka_width = params['aka_width']
    aka_height = params['aka_height']
    aka_thickness = params['aka_thickness']
    aka_length_mm = params['aka_length']
    vaka_width_mm = params['vaka_width']

    panels_per_half = params['panels_longitudinal'] // 2
    akas_per_panel = params.get('akas_per_panel', 1)
    num_akas = 2 * panels_per_half * akas_per_panel

    # Equal-stiffness akas (same section) -> force splits evenly per Table 15
    # item 2 (F_Li = F_L * EI_i/L^3 / sum(EI_i/L^3), which reduces to 1/n when
    # all akas share the same section and effective length)
    f_li_per_aka_n = f_lt_n / num_akas

    cantilever_length_mm = aka_length_mm - vaka_width_mm
    m_li_nmm = f_li_per_aka_n * cantilever_length_mm  # Table 15 item 2: M_Li = F_Li * B_i

    section = calculate_rhs_section_properties(aka_width, aka_height, aka_thickness)
    # Longitudinal (fore-aft) force bends the aka about its WEAK axis
    sy_mm3 = section['Sy_mm3']
    sigma_mpa = m_li_nmm / sy_mm3

    safety_factor = ISO_AL_DESIGN_STRESS_WELDED_MPA / sigma_mpa if sigma_mpa > 0 else float('inf')

    return {
        'clause': 'ISO 12215-7 12.10, Table 15 (GLC5)',
        'proa_adaptation': 'Single ama treated as the "trimaran float" analogue (closest fit in Part 7).',
        'inputs': {
            'm_ldc_kg': round(m_ldc_kg, 1),
            'm_float_kg': round(m_float_kg, 1),
            'num_akas': num_akas,
            'cantilever_length_mm': round(cantilever_length_mm, 0),
        },
        'force_lt_kN': round(f_lt_kN, 2),
        'force_per_aka_n': round(f_li_per_aka_n, 1),
        'moment_per_aka_nm': round(m_li_nmm / 1000, 1),
        'weak_axis_stress_mpa': round(sigma_mpa, 2),
        'iso_design_stress_welded_mpa': round(ISO_AL_DESIGN_STRESS_WELDED_MPA, 1),
        'safety_factor_vs_iso_design_stress': round(safety_factor, 2),
        'note': (
            'This safety factor is computed against ISO\'s own allowable '
            'design stress (already includes ISO\'s knockdown from yield), '
            'so SF>=1.0 here means ISO-compliant - it is NOT directly '
            'comparable to the >=2.0 convention used against raw yield '
            'strength elsewhere in this package (see aka_analysis.py).'
        ),
    }


def validate_global_loads(params: Dict[str, Any], mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ISO 12215-7 global load cross-check for the aka/crossbeam system.

    This supplements (does not replace) the existing static suspended_ama
    and diagonal_braces checks - it adds the ISO-specific dynamic global
    load cases (GLC1, GLC5) that those static checks do not model at all.
    """
    glc1 = calculate_glc1_torsional_moment(params, mass_data)
    glc5 = calculate_glc5_longitudinal_force(params, mass_data)

    passed = glc5['safety_factor_vs_iso_design_stress'] >= 1.0

    return {
        'test_name': 'iso_global_loads',
        'description': 'ISO 12215-7 multihull global load cross-check (GLC1 torsion, GLC5 longitudinal force)',
        'passed': passed,
        'applicability_caveat': (
            'ISO 12215-7 assumes symmetric catamarans/trimarans. RP2 is a '
            'single-outrigger proa. GLC5 is adapted with reasonable '
            'confidence (single ama as trimaran-float analogue); GLC1 is '
            'reported as an order-of-magnitude bound only and is NOT run '
            'through Annex D\'s per-beam distribution - see module docstring.'
        ),
        'glc1_torsional': glc1,
        'glc5_longitudinal': glc5,
        'summary': {
            'result': 'PASS' if passed else 'FAIL',
            'governing_check': 'GLC5 longitudinal force (GLC1 not quantified per-aka - see caveat)',
        },
    }
