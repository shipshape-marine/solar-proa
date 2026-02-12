"""
Load electrical simulation constants from JSON.
"""

import json
import sys

# Defaults (used if load_constants is never called)
GROUNDING_RESISTANCE = 1e-6
WIRE_RESISTANCE = 0.01
EPSILON = 1e-4
MPPT_BATTERY_VOLTAGE_BUFFER = 2.0
VOLTAGE_MISMATCH_TOLERANCE = 5.0
POWER_MISMATCH_TOLERANCE_PERCENTAGE = 1.0
ARRAY_DECODER_PATTERN = r"(arr|s|p)(\d+)(?=_|\s|$)"

# Formatting constants (internal, not from JSON)
BARF = "=" * 50 + "\n"
BARE = "\n" + "=" * 50

_KEY_MAP = {
    "grounding_resistance": "GROUNDING_RESISTANCE",
    "wire_resistance": "WIRE_RESISTANCE",
    "epsilon": "EPSILON",
    "mppt_battery_voltage_buffer": "MPPT_BATTERY_VOLTAGE_BUFFER",
    "voltage_mismatch_tolerance": "VOLTAGE_MISMATCH_TOLERANCE",
    "power_mismatch_tolerance_percentage": "POWER_MISMATCH_TOLERANCE_PERCENTAGE",
    "array_decoder_pattern": "ARRAY_DECODER_PATTERN",
}


def load_constants(path: str):
    """Load constants from a JSON file and update module-level variables."""
    module = sys.modules[__name__]
    with open(path, "r") as f:
        data = json.load(f)
    for json_key, attr_name in _KEY_MAP.items():
        if json_key in data:
            setattr(module, attr_name, data[json_key])
