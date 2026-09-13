"""
Aka-to-vaka joint check per ISO 12215-6.

IMPORTANT SCOPE NOTE: ISO 12215-6 Clause 7.2 "Bonding" (tabbing width, k_j-style
coefficients) is specific to FRP/composite construction. It does NOT apply to
the aluminium aka-to-vaka connection on RP2. For metal construction, ISO
12215-6 gives only qualitative good-practice principles (Clause 6.3 "Load
transfer", Clause 8.1 "Design details", Clause 8.2 "End connections") - there
is no closed-form joint-capacity formula for a metal connection anywhere in
Part 6. This is itself a real gap, just a different one than originally
assumed (not "the tabbing-width formula doesn't apply to a proa", but "the
tabbing-width formula doesn't apply to metal construction at all").

No aka-to-vaka joint/bracket design exists yet in this codebase (only the aka
beam itself is checked, in aka_analysis.py). This module:
1. Reports the qualitative good-practice checklist from ISO 12215-6 Clause
   6.3/8.1/8.2 that any joint design will need to satisfy.
2. Derives an ISO-minimum weld/fastener capacity for the joint by engineering
   analogy to ISO 12215-6 Clause 6.3.4 ("weld or glue area shall generally not
   be less than the stiffener web area"), using the aka's own peak moment/
   shear (from aka_analysis.py) and the ISO 12215-5 Table 17 aluminium design
   stresses - NOT a literal ISO 12215-6 formula, since none exists for this
   case, but a first-pass sizing check flagged explicitly as such.

See constant/standards/iso12215.json for citation details.
"""

from typing import Dict, Any

from .beam_mechanics import (
    ISO_AL_DESIGN_STRESS_WELDED_MPA, ISO_AL_SHEAR_DESIGN_STRESS_WELDED_MPA,
    calculate_rhs_section_properties,
)
from .aka_analysis import extract_outrigger_mass, analyze_aka_cantilever
from .iso_global_loads import calculate_glc5_longitudinal_force


GOOD_PRACTICE_CHECKLIST = [
    {
        'clause': '6.3.1/6.3.2',
        'requirement': 'Concentrated loads transmitted via stiff supporting members/brackets, not landed on unsupported plating; smooth, non-abrupt load transfer.',
    },
    {
        'clause': '6.3.5',
        'requirement': 'Avoid knife-edge load crossing (two load-carrying members meeting at a right angle with no bracket) - at least one member must be reinforced at the joint.',
    },
    {
        'clause': '8.1',
        'requirement': 'No abrupt change of section/shape; where width/depth changes, taper >= 33%.',
    },
    {
        'clause': '8.2',
        'requirement': 'End connection must provide "adequate end fixity and effective transmission of the bending moment and shear force into the supporting member" (qualitative requirement, no formula given).',
    },
    {
        'clause': '8.7/8.8',
        'requirement': (
            'If welded: follow Annex C good-practice welding procedure. '
            'If riveted: rivet diameter >= thickest connected plate thickness '
            'or 25% of total connected thickness (whichever greater); edge '
            'distance >= 1.5x plate thickness; rivet spacing >= 2.5x diameter.'
        ),
    },
]


def get_aka_peak_load(params: Dict[str, Any], mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the aka's governing moment/shear at the vaka connection, for use as
    the joint design demand. Compares two load cases and takes the governing
    (larger) of each component, since the joint has to survive whichever
    demand is actually higher rather than only the one this module happened
    to check first:

    - Static suspended-ama case (aka_analysis.py, strong axis).
    - ISO 12215-7 GLC5 dynamic longitudinal case (iso_global_loads.py, weak
      axis) - generally the higher demand, per that module's own docstring.

    Neither load case is distributed per-axis here; the weld/fastener sizing
    in check_weld_capacity_by_analogy() is a scalar area check (not axis-
    resolved), so taking the max of each component is the conservative,
    ISO-anchored bound available without a real joint geometry to resolve
    combined bending.
    """
    tip_mass, distributed_mass, _ = extract_outrigger_mass(mass_data)

    panels_per_half = params['panels_longitudinal'] // 2
    akas_per_panel = params.get('akas_per_panel', 1)
    num_akas = 2 * panels_per_half * akas_per_panel

    static_analysis = analyze_aka_cantilever(params, tip_mass, distributed_mass, num_akas, 'strong')
    static_moment_nmm = static_analysis['moment_breakdown']['M_total_nmm']
    static_shear_n = static_analysis['load']['total_force_per_aka_n']

    glc5 = calculate_glc5_longitudinal_force(params, mass_data)
    glc5_moment_nmm = glc5['moment_per_aka_nm'] * 1000
    glc5_shear_n = glc5['force_per_aka_n']

    governing_moment_nmm = max(static_moment_nmm, glc5_moment_nmm)
    governing_shear_n = max(static_shear_n, glc5_shear_n)

    return {
        'source': 'max(aka_analysis static suspended-ama, ISO 12215-7 GLC5 dynamic)',
        'moment_at_vaka_nmm': governing_moment_nmm,
        'shear_at_vaka_n': governing_shear_n,
        'section': static_analysis['section_properties'],
        'load_cases_compared': {
            'static_suspended_ama_strong_axis': {
                'moment_nmm': round(static_moment_nmm, 0),
                'shear_n': round(static_shear_n, 1),
            },
            'iso_12215_7_glc5_weak_axis': {
                'moment_nmm': round(glc5_moment_nmm, 0),
                'shear_n': round(glc5_shear_n, 1),
            },
            'governing_moment_source': 'GLC5' if glc5_moment_nmm > static_moment_nmm else 'static',
            'governing_shear_source': 'GLC5' if glc5_shear_n > static_shear_n else 'static',
        },
    }


def check_weld_capacity_by_analogy(params: Dict[str, Any],
                                    moment_nmm: float,
                                    shear_n: float) -> Dict[str, Any]:
    """
    First-pass ISO-minimum weld sizing, by analogy to ISO 12215-6 6.3.4.

    6.3.4 states (for a different connection type - floating frames) that
    "the weld or glue area shall generally not be less than the stiffener
    web area, A_w". Applied here to the aka-to-vaka joint as the closest
    available ISO-anchored rule of thumb: require the weld's shear-carrying
    area to be at least the aka's own web (side wall) area, then check that
    area against the applied shear using the ISO 12215-5 Table 17 aluminium
    shear design stress.

    This is NOT an ISO 12215-6 formula (none exists for this joint type) -
    it is an engineering analogy explicitly flagged as such, intended as a
    lower bound / sanity check, not a certified joint design.
    """
    aka_width = params['aka_width']
    aka_height = params['aka_height']
    aka_thickness = params['aka_thickness']

    section = calculate_rhs_section_properties(aka_width, aka_height, aka_thickness)

    # Web area: the two side walls of the RHS resisting vertical shear
    web_area_mm2 = 2 * (aka_height - 2 * aka_thickness) * aka_thickness

    # Required weld shear area to carry the applied shear at ISO's welded
    # aluminium shear design stress
    required_weld_area_mm2 = shear_n / ISO_AL_SHEAR_DESIGN_STRESS_WELDED_MPA if shear_n > 0 else 0.0

    # Required weld area to carry the applied moment as a couple over the
    # aka's own depth (first-pass bound - a real joint would use a proper
    # weld-group section modulus, not attempted here since no joint geometry
    # exists yet)
    lever_arm_mm = aka_height
    required_weld_force_from_moment_n = moment_nmm / lever_arm_mm if lever_arm_mm > 0 else 0.0
    required_weld_area_for_moment_mm2 = (
        required_weld_force_from_moment_n / ISO_AL_DESIGN_STRESS_WELDED_MPA
        if required_weld_force_from_moment_n > 0 else 0.0
    )

    governing_required_area_mm2 = max(required_weld_area_mm2, required_weld_area_for_moment_mm2)

    return {
        'method': (
            'Engineering analogy to ISO 12215-6 6.3.4 (weld/glue area >= '
            'stiffener web area), NOT a literal ISO 12215-6 formula - none '
            'exists for metal end connections. Demand is the governing '
            '(larger) of the aka_analysis.py static suspended-ama case and '
            'the ISO 12215-7 GLC5 dynamic case - see get_aka_peak_load().'
        ),
        'aka_web_area_mm2': round(web_area_mm2, 1),
        'applied_moment_nm': round(moment_nmm / 1000, 1),
        'applied_shear_n': round(shear_n, 1),
        'required_weld_area_for_shear_mm2': round(required_weld_area_mm2, 1),
        'required_weld_area_for_moment_mm2': round(required_weld_area_for_moment_mm2, 1),
        'governing_required_weld_area_mm2': round(governing_required_area_mm2, 1),
        'meets_web_area_rule_of_thumb': web_area_mm2 >= governing_required_area_mm2,
        'iso_design_stress_used_mpa': {
            'direct_welded': ISO_AL_DESIGN_STRESS_WELDED_MPA,
            'shear_welded': round(ISO_AL_SHEAR_DESIGN_STRESS_WELDED_MPA, 1),
        },
    }


def validate_aka_joint(params: Dict[str, Any], mass_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ISO 12215-6 aka-to-vaka joint traceability report.

    Informational rather than a strict pass/fail against the existing
    min_safety_factor convention: no joint design exists yet, so this
    derives an ISO-anchored minimum rather than validating a real design.
    """
    peak_load = get_aka_peak_load(params, mass_data)
    weld_check = check_weld_capacity_by_analogy(
        params, peak_load['moment_at_vaka_nmm'], peak_load['shear_at_vaka_n']
    )

    return {
        'test_name': 'iso_aka_joint_traceability',
        'description': 'ISO 12215-6 aka-to-vaka joint good practice + first-pass weld sizing',
        'passed': weld_check['meets_web_area_rule_of_thumb'],
        'known_gap': (
            'No aka-to-vaka joint/bracket design exists in this codebase yet '
            '- only the aka beam itself is checked elsewhere (aka_analysis.py, '
            'the 3.27 SF, and iso_global_loads.py GLC5). This module derives '
            'an ISO-anchored minimum, against the governing of those two load '
            'cases, for comparison once a real joint (welded bracket, bolted '
            'flange, etc.) is designed; it does not replace that design.'
        ),
        'good_practice_checklist': GOOD_PRACTICE_CHECKLIST,
        'peak_load': peak_load,
        'weld_capacity_check': weld_check,
        'summary': {
            'result': 'PASS (rule-of-thumb)' if weld_check['meets_web_area_rule_of_thumb'] else 'FAIL (rule-of-thumb)',
            'note': 'This checks the aka web area against a first-pass ISO-anchored analogy, not a real joint design.',
        },
    }
