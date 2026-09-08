"""
ISO 12215-3 / 12215-5 aluminium material traceability check.

This module does NOT validate a specific certified alloy against a load - no
aluminium alloy spec has been finalized for RP2 yet (per design team, 2026).
Instead it reports:

1. Whether the assumed section type (extruded RHS/SHS/round tube, used for
   aka/brace/mast) is consistent with the alloy family ISO 12215-3 Clause 4.7
   requires for that product form.
2. What ISO 12215-3 Clause 7.3 requires to be documented on a material data
   sheet, and flags that this documentation does not yet exist.
3. The ISO 12215-5 Annex B design-stress values that would apply once an
   alloy/temper is chosen, for use by the other iso_* modules.

See constant/standards/iso12215.json for citation details.
"""

from typing import Dict, Any

from .beam_mechanics import (
    ISO_AL_6061_ULTIMATE_MPA, ISO_AL_6061_ULTIMATE_WELDED_MPA,
    ISO_AL_6061_YIELD_MPA, ISO_AL_6061_YIELD_WELDED_MPA,
    ISO_AL_DESIGN_STRESS_WELDED_MPA, ISO_AL_DESIGN_STRESS_UNWELDED_MPA,
    ISO_AL_SHEAR_DESIGN_STRESS_WELDED_MPA,
)

# Sections in this codebase assumed to be aluminium extrusions (RHS/SHS/round
# tube) - product form per ISO 12215-3 4.7.3 is "profiles, bars, tubes,
# closed profiles", which is the heat-treatable (Si-based) alloy family.
EXTRUDED_ALUMINIUM_COMPONENTS = ['aka', 'diagonal_brace', 'cross_brace', 'mast', 'gunwale']


def check_alloy_family_consistency() -> Dict[str, Any]:
    """
    ISO 12215-3 Clause 4.7: classify the alloy family implied by product form.

    4.7.2 (non-heat-treatable, Mg-based) is typical for rolled sheet/plate.
    4.7.3 (heat-treatable, Si-based) is typical for extruded sections/tubes/
    closed profiles - i.e. exactly the product form used for the aka, braces,
    and mast in this design. 4.7.4 flags Al-Cu/Al-Zn (2000/7000-series) as
    unsuitable for small-craft construction without special protection.

    Returns:
        Classification result (informational, not a pass/fail against a load)
    """
    return {
        'clause': 'ISO 12215-3 4.7.1-4.7.4',
        'assumed_product_form': 'extruded profiles (RHS/SHS/round tube)',
        'required_alloy_family': 'heat-treatable (4.7.3), major alloying element Si, e.g. 6000-series',
        'components_this_applies_to': EXTRUDED_ALUMINIUM_COMPONENTS,
        'consistent': True,
        'note': (
            '6061/6082-type extrusions (the family beam_mechanics.py currently '
            'assumes via ALUMINUM_YIELD_STRENGTH_MPA=240) are heat-treatable, '
            'Si-based alloys and are the correct family for extruded closed '
            'profiles per 4.7.3. Alloys of the 2000 (Al-Cu) or 7000 (Al-Zn) '
            'series would NOT be appropriate per 4.7.4 unless specially protected.'
        ),
    }


def check_documentation_completeness(alloy_datasheet_available: bool = False) -> Dict[str, Any]:
    """
    ISO 12215-3 Clause 7.3: required material documentation.

    Per the design team (2026), no aluminium alloy/temper has been finalized
    yet, so this is expected to be incomplete at this stage - reported as a
    known, currently-open item rather than an urgent failure.

    Args:
        alloy_datasheet_available: set True once a data sheet exists

    Returns:
        Documentation completeness result
    """
    required_fields = [
        'chemical composition of the alloy',
        'grade of aluminium alloy',
        'condition of supply (temper)',
        'minimum mechanical properties (or reference standard)',
        'minimum/expected mechanical properties AFTER WELDING',
        'identification method (e.g. colour coding)',
    ]

    return {
        'clause': 'ISO 12215-3 7.3',
        'required_fields': required_fields,
        'datasheet_available': alloy_datasheet_available,
        'passed': alloy_datasheet_available,
        'note': (
            'No alloy/temper has been finalized for RP2 yet, so this data '
            'sheet does not exist. This is a documentation gap, not a '
            'structural failure - it must be closed before certification, '
            'but does not itself indicate the current design is undersized.'
        ) if not alloy_datasheet_available else 'Data sheet on file.',
    }


def get_design_stress_reference() -> Dict[str, Any]:
    """
    ISO 12215-5 Annex B / Table 17 design stresses for a representative
    heat-treatable extruded alloy (EN AW-6061 T5/T6 closed profile), for use
    by other iso_* modules when comparing computed stresses to ISO allowables.

    NOTE: these are ISO's allowable DESIGN stresses (already include the
    standard's own knockdown from ultimate/yield) - comparing a computed
    stress to sigma_d directly is the ISO-consistent check; it is NOT
    equivalent to comparing raw yield to computed stress with an additional
    safety factor of 2.0, which is the convention used elsewhere in this
    package (see ALUMINUM_YIELD_STRENGTH_MPA in beam_mechanics.py).

    Returns:
        Dict of ISO design stress values (MPa) plus underlying mechanical properties
    """
    return {
        'alloy_reference': 'EN AW-6061, closed profile, T5/T6 (ISO 12215-5 Table B.2)',
        'mechanical_properties_mpa': {
            'ultimate_unwelded': ISO_AL_6061_ULTIMATE_MPA,
            'ultimate_welded': ISO_AL_6061_ULTIMATE_WELDED_MPA,
            'yield_unwelded': ISO_AL_6061_YIELD_MPA,
            'yield_welded': ISO_AL_6061_YIELD_WELDED_MPA,
        },
        'design_stress_mpa': {
            'welded_direct': round(ISO_AL_DESIGN_STRESS_WELDED_MPA, 1),
            'unwelded_direct': round(ISO_AL_DESIGN_STRESS_UNWELDED_MPA, 1),
            'welded_shear': round(ISO_AL_SHEAR_DESIGN_STRESS_WELDED_MPA, 1),
        },
        'formula_welded': 'sigma_d = 0.7 * sigma_yw (ISO 12215-5 Table 17, stiffeners, heat-treatable)',
        'formula_unwelded': 'sigma_d = min(0.6*sigma_u, 0.9*sigma_y) (ISO 12215-5 Table 17, footnote b)',
        'note': (
            'Whether the aka-to-vaka connection ends up welded or mechanically '
            'fastened (bolted/riveted) changes which of these applies, and by '
            'a factor of ~1.8x (81 MPa welded vs 147 MPa unwelded). This is '
            'undetermined because no joint design exists yet - see '
            'iso_joint_check.py.'
        ),
    }


def validate_material_traceability(alloy_datasheet_available: bool = False) -> Dict[str, Any]:
    """
    Combined ISO 12215-3/5 material traceability report.

    This is informational/documentation-focused rather than a structural
    pass/fail against an applied load - see the other iso_* modules for
    stress-based checks that consume get_design_stress_reference().
    """
    family_check = check_alloy_family_consistency()
    doc_check = check_documentation_completeness(alloy_datasheet_available)
    design_stress = get_design_stress_reference()

    return {
        'test_name': 'iso_material_traceability',
        'description': 'ISO 12215-3 aluminium alloy classification and documentation traceability',
        'passed': family_check['consistent'],  # structural family choice is sound
        'alloy_family_check': family_check,
        'documentation_check': doc_check,
        'design_stress_reference': design_stress,
        'summary': {
            'result': 'PASS (family)' if family_check['consistent'] else 'FAIL (family)',
            'documentation_status': 'COMPLETE' if doc_check['passed'] else 'OPEN GAP',
        },
    }
