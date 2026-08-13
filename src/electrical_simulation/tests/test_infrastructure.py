"""Sanity checks for the test infrastructure itself (spec Task 1)."""

import json


def test_repo_root_contains_project_dirs(repo_root):
    """Verify repo_root resolves to the directory holding src/ and constant/."""
    assert (repo_root / "src" / "electrical_simulation").is_dir()
    assert (repo_root / "constant" / "electrical").is_dir()


def test_constants_fixture_exposes_required_keys(constants):
    """Verify the constants fixture loads the keys the simulator relies on."""
    for key in (
        "GROUNDING_RESISTANCE",
        "WIRE_RESISTANCE",
        "EPSILON",
        "ARRAY_DECODER_PATTERN",
        "POWER_MISMATCH_TOLERANCE_PERCENTAGE",
    ):
        assert key in constants, f"missing constant: {key}"


def test_constants_fixture_matches_file_on_disk(constants, constants_path):
    """Verify the fixture is the real constants file, not a stand-in."""
    with constants_path.open(encoding="utf-8") as handle:
        assert constants == json.load(handle)


def test_integration_marker_is_registered(pytestconfig):
    """Verify the 'integration' marker is declared so -m filtering works."""
    markers = pytestconfig.getini("markers")
    assert any(marker.startswith("integration:") for marker in markers)
