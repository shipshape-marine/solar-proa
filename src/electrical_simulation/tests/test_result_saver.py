"""Unit tests for saving simulation results to disk (spec Task 5).

Covers ``save_to_file``: the result dict is written to the requested path as
valid JSON with 4-space indentation, and reads back equal to what was passed
in. The payload is a result dict shaped by ``pyspice_simulator.__simulate__``
and filled with the kind of values a parsed run produces, so nested sections,
floats, ``None`` and booleans all go through the serialiser.

No NgSpice and no circuit; files are written under ``tmp_path``.

Validates: Requirements 9.1, 9.2
"""

import json


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _save(result: dict, save_path, constants: dict) -> None:
    """Write a result dict through the production saver."""
    from src.electrical_simulation.result_saver import save_to_file

    save_to_file(result, str(save_path), constants=constants)


def _sample_result() -> dict:
    """A result dict in production shape carrying representative values."""
    from src.electrical_simulation.pyspice_simulator import __simulate__

    meta_data = {
        "keyword": "info",
        "array_count": 0,
        "data": [],
        "name": "test_circuit",
        "date": "2026-01-01T00:00:00",
    }
    _, result, _ = __simulate__(None, meta_data, ["a setup error"], False)

    result["warning"]["array_count"] = 1
    result["warning"]["data"] = ["Battery is overcharged by 3.0 A"]
    result["summary"]["array_count"] = 1
    result["summary"]["data"] = [
        {
            "array_index": 0,
            "voltage": {"total_dc_bus_voltage": 48.0},
            "current": {
                "total_mppt_output_current": 10.0,
                "total_battery_input_current": -4.6875,
            },
        }
    ]
    result["load_result"]["array_count"] = 1
    result["load_result"]["data"] = [
        {
            "array_index": 0,
            "voltage": {"load_Test_Load_Linear_positive": 47.9},
            "current": {"load_Test_Load_Linear": 5.0},
            "motor_physics": {
                "model_type": "linear",
                "power_electrical_w": 225.0,
                "speed_rpm": None,
                "is_stalled": None,
            },
        }
    ]
    return result


# ---------------------------------------------------------------------------
# Requirements 9.1, 9.2
# ---------------------------------------------------------------------------


def test_saves_valid_json(tmp_path, constants, capsys):
    """Verify result dict saved as valid JSON with 4-space indent."""
    result = _sample_result()
    save_path = tmp_path / "rp2.test.operating_point.json"

    _save(result, save_path, constants)

    assert save_path.exists()
    text = save_path.read_text(encoding="utf-8")
    # Valid JSON, and indented exactly as json.dumps(..., indent=4) produces.
    json.loads(text)
    assert text == json.dumps(result, indent=4)
    # First nested key sits four spaces in, one indent level below the root.
    assert '\n    "info": {' in text
    assert '\n        "keyword": "info",' in text

    assert str(save_path) in capsys.readouterr().out


def test_file_is_readable(tmp_path, constants):
    """Verify saved file can be loaded back and matches original."""
    result = _sample_result()
    save_path = tmp_path / "rp2.test.operating_point.json"

    _save(result, save_path, constants)

    with save_path.open(encoding="utf-8") as handle:
        loaded = json.load(handle)

    assert loaded == result
    # Round-tripping preserves types, not just values.
    assert loaded["summary"]["data"][0]["current"][
        "total_battery_input_current"
    ] == -4.6875
    assert loaded["load_result"]["data"][0]["motor_physics"]["speed_rpm"] is None
    assert loaded["error"]["data"] == ["a setup error", "NgSpice is not available. Simulation cannot proceed."]
