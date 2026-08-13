"""Unit tests for simulation result parsing (spec Task 5).

Covers ``parse_simulation_result``: keyword-based categorisation of node
voltages and branch currents into the result sections, array-index extraction
via ARRAY_DECODER_PATTERN, the per-cell voltage post-process applied to the
battery and panel sections, the ``v`` prefix stripped from branch names, and
the stdout report for names that match no section keyword.

No NgSpice: each test feeds the parser a stand-in analysis object whose
``.nodes`` / ``.branches`` values expose ``as_ndarray()`` returning a
one-element array, which is all the parser touches. The result dict and the
``struc`` template come from ``pyspice_simulator.__simulate__`` itself, so the
section key set and entry shape stay in sync with production. Node and branch
names are the real ones the components emit (``arr0_mppt_output``,
``p0_s0_battery_positive``, ``total_dc_bus_voltage``, ...). All ``src`` imports
happen inside helpers so collection stays green when the simulation
dependencies are unavailable.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

import numpy as np


# ---------------------------------------------------------------------------
# helpers — stand-in NgSpice analysis and a production-shaped result dict
# ---------------------------------------------------------------------------


class _FakeSignal:
    """A single NgSpice waveform: one operating-point sample in an ndarray."""

    def __init__(self, value: float):
        self.value = float(value)

    def as_ndarray(self):
        return np.array([self.value])


class _FakeAnalysis:
    """Analysis stand-in exposing only ``.nodes`` and ``.branches``."""

    def __init__(self, nodes: dict = None, branches: dict = None):
        self.nodes = {name: _FakeSignal(v) for name, v in (nodes or {}).items()}
        self.branches = {name: _FakeSignal(v) for name, v in (branches or {}).items()}


def _blank_result():
    """Return ``(result, struc)`` exactly as ``__simulate__`` initialises them.

    Called with NgSpice unavailable so no circuit is needed; the resulting
    "NgSpice is not available" error is cleared so tests start from an empty
    error section.
    """
    from src.electrical_simulation.pyspice_simulator import __simulate__

    meta_data = {
        "keyword": "info",
        "array_count": 0,
        "data": [],
        "name": "test_circuit",
        "date": "2026-01-01T00:00:00",
    }
    _, result, struc = __simulate__(None, meta_data, [], False)
    result["error"]["data"].clear()
    result["error"]["array_count"] = 0
    return result, struc


def _parse(constants: dict, nodes: dict = None, branches: dict = None) -> dict:
    """Parse a synthetic analysis and return the filled-in result dict."""
    from src.electrical_simulation.parse_result import parse_simulation_result

    result, struc = _blank_result()
    parse_simulation_result(
        _FakeAnalysis(nodes, branches), result, struc, constants=constants
    )
    return result


def _voltage(result: dict, section: str, index: int = 0) -> dict:
    """Voltage dict of one data entry, or {} when the section is empty."""
    data = result[section]["data"]
    return data[index]["voltage"] if len(data) > index else {}


def _current(result: dict, section: str, index: int = 0) -> dict:
    """Current dict of one data entry, or {} when the section is empty."""
    data = result[section]["data"]
    return data[index]["current"] if len(data) > index else {}


# ---------------------------------------------------------------------------
# Requirement 3.1 — node voltages categorised by section keyword
# ---------------------------------------------------------------------------


def test_nodes_categorized_by_keyword(constants, capsys):
    """Verify node voltages placed in correct result section based on keyword match."""
    result = _parse(
        constants,
        nodes={
            # DC bus and MPPT bus rails: both carry the "total" keyword.
            "total_dc_bus_voltage": 48.0,
            "total_mppt_output": 48.5,
            "arr0_mppt_output": 63.0,
            "arr0_solar_array_output": 40.0,
            # Panels are reported as terminal pairs; the post-process needs both.
            "arr0_p0_s0_panel_positive": 20.0,
            "arr0_p0_s0_panel_negative": 0.0,
            "arr0_load_Test_Load_Linear_positive": 47.9,
            "balancing_load": 48.0,
            "l_array_positive": 47.95,
            # Probe nodes are internal to the netlist and never reported.
            "battery_input_measured": 48.1,
        },
    )

    # Every section named by the requirement exists in the result dict.
    assert set(result) == {
        "info",
        "error",
        "warning",
        "summary",
        "mppt_result",
        "battery_result",
        "solar_result",
        "panel_result",
        "load_balancer",
        "load_result",
        "l_array_result",
    }

    # "total" is matched before "mppt", so both bus rails land in the summary.
    assert _voltage(result, "summary") == {
        "total_dc_bus_voltage": 48.0,
        "total_mppt_output": 48.5,
    }
    assert _voltage(result, "mppt_result") == {"mppt_output": 63.0}
    assert _voltage(result, "solar_result") == {"solar_array_output": 40.0}
    assert _voltage(result, "panel_result") == {
        "p0_s0_panel_positive": 20.0,
        "p0_s0_panel_negative": 0.0,
    }
    assert _voltage(result, "load_result") == {
        "load_Test_Load_Linear_positive": 47.9
    }
    # "balancing_load" is matched before the bare "load" keyword.
    assert _voltage(result, "load_balancer") == {"balancing_load": 48.0}
    assert _voltage(result, "l_array_result") == {"l_array_positive": 47.95}

    # The "measured" probe node is dropped, not reported as unmatched.
    assert result["battery_result"]["data"] == []
    assert "battery_input_measured" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Requirement 3.3 — array index extraction
# ---------------------------------------------------------------------------


def test_array_index_extraction(constants):
    """Verify array index correctly extracted from node name pattern arr{N}_."""
    # Deliberately out of order and starting past index 0: the parser must grow
    # the data list to fit whichever index arrives.
    result = _parse(
        constants,
        nodes={
            "arr2_mppt_output": 62.0,
            "arr0_mppt_output": 60.0,
            "arr1_mppt_output": 61.0,
        },
    )

    mppt = result["mppt_result"]
    assert mppt["array_count"] == 3
    assert len(mppt["data"]) == 3
    for index, voltage in enumerate([60.0, 61.0, 62.0]):
        # The arr{N}_ prefix is stripped from the key and recorded separately.
        assert mppt["data"][index]["array_index"] == index
        assert mppt["data"][index]["voltage"] == {"mppt_output": voltage}

    # A section without an array prefix stays a single entry at index 0.
    single = _parse(constants, nodes={"total_dc_bus_voltage": 48.0})["summary"]
    assert single["array_count"] == 1
    assert single["data"][0]["array_index"] == 0


# ---------------------------------------------------------------------------
# Requirement 3.4 — per-cell voltage post-processing
# ---------------------------------------------------------------------------


def test_battery_voltage_postprocess(constants):
    """Verify per-cell voltage computed as positive minus negative terminal."""
    # Two cells in series, measured against ground: 24 V and 48 V at the
    # positive terminals, so cell 1 reads 48 V before post-processing.
    result = _parse(
        constants,
        nodes={
            "p0_s0_battery_positive": 24.0,
            "p0_s0_battery_negative": 0.0,
            "p0_s1_battery_positive": 48.0,
            "p0_s1_battery_negative": 24.0,
        },
    )

    assert _voltage(result, "battery_result") == {
        "p0_s0_battery_positive": 24.0,
        "p0_s0_battery_negative": 0.0,
        "p0_s1_battery_positive": 24.0,
        "p0_s1_battery_negative": 0.0,
    }


def test_panel_voltage_postprocess(constants):
    """Verify panel voltages are post-processed per cell like the battery ones."""
    result = _parse(
        constants,
        nodes={
            "arr0_p0_s0_panel_positive": 20.0,
            "arr0_p0_s0_panel_negative": 0.0,
            "arr0_p0_s1_panel_positive": 40.0,
            "arr0_p0_s1_panel_negative": 20.0,
        },
    )

    assert _voltage(result, "panel_result") == {
        "p0_s0_panel_positive": 20.0,
        "p0_s0_panel_negative": 0.0,
        "p0_s1_panel_positive": 20.0,
        "p0_s1_panel_negative": 0.0,
    }


# ---------------------------------------------------------------------------
# Requirement 3.5 — unmatched names reported
# ---------------------------------------------------------------------------


def test_unmatched_node_printed(constants, capsys):
    """Verify unmatched node names printed to stdout."""
    result = _parse(constants, nodes={"mystery_rail": 12.345})

    out = capsys.readouterr().out
    assert "Missing node (mystery_rail): 12.35 V" in out
    # Nothing was stored anywhere: every section is still empty.
    assert all(
        section["data"] == []
        for key, section in result.items()
        if key not in ("info",)
    )


# ---------------------------------------------------------------------------
# Requirement 3.2 — branch currents categorised by section keyword
# ---------------------------------------------------------------------------


def test_branch_current_categorization(constants, capsys):
    """Verify branch currents placed in correct section with v-prefix stripped."""
    result = _parse(
        constants,
        branches={
            # PySpice reports voltage-source branches with a leading "v".
            "vtotal_battery_input_current": 4.0,
            "varr0_mppt_output": 10.0,
            "varr1_mppt_output": 9.0,
            "vp0_s0_battery": -4.0,
            "varr0_solar_array_output": 5.5,
            "varr0_load_Test_Load_Linear": 5.0,
            "vbalancing_load": 1.0,
            "vl_array": 5.0,
            "vmystery_probe": 0.25,
            # Probe branches are internal and never reported.
            "vbattery_input_measured": 4.0,
        },
    )

    assert _current(result, "summary") == {"total_battery_input_current": 4.0}
    assert _current(result, "mppt_result", 0) == {"mppt_output": 10.0}
    assert _current(result, "mppt_result", 1) == {"mppt_output": 9.0}
    assert result["mppt_result"]["array_count"] == 2
    assert _current(result, "battery_result") == {"p0_s0_battery": -4.0}
    assert _current(result, "solar_result") == {"solar_array_output": 5.5}
    assert _current(result, "load_result") == {"load_Test_Load_Linear": 5.0}
    assert _current(result, "load_balancer") == {"balancing_load": 1.0}
    assert _current(result, "l_array_result") == {"l_array": 5.0}

    out = capsys.readouterr().out
    assert "Branch mystery_probe: 0.25 A" in out
    assert "battery_input_measured" not in out
