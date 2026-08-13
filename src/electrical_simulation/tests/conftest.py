"""Fixtures for the electrical_simulation test suite.

The JSON payloads live in ``src/electrical_simulation/tests/fixtures/`` and are
authored in Task 2 of the spec. All loaders here are lazy: they resolve and
read files at test-run time, never at collection time, so collection stays
green before the fixture files exist.

Dict-returning fixtures hand out deep copies. ``build_circuit_from_json`` and
``combine_config_setup`` mutate the config they are given (calculated_power,
resolved choices), so each test needs a pristine copy.

The repo-level fixtures (``repo_root``, ``constants_path``, ``constants``,
``production_components_path``) are intentionally free of any ``src`` imports so
that test collection works even when optional simulation dependencies (PySpice /
NgSpice) are not installed.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

TEST_COMPONENTS_FILE = "test_components.json"
TEST_VOYAGE_FILE = "test_voyage_setup.json"


def _read_json(path: Path) -> dict:
    """Read a JSON fixture, skipping the test with a clear message if absent."""
    if not path.exists():
        pytest.skip(f"Test fixture not found: {path} (authored in spec Task 2)")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root (the directory holding src/)."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def constants_path() -> Path:
    """Path to the production electrical constants JSON."""
    return REPO_ROOT / "constant" / "electrical" / "constants.json"


@pytest.fixture(scope="session")
def constants(constants_path: Path) -> dict:
    """Electrical constants dict as consumed by the simulation modules.

    Loaded from ``constant/electrical/constants.json`` so tests exercise the
    same tolerances and regex patterns as production runs.
    """
    with constants_path.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def production_components_path() -> Path:
    """Path to the production component specification JSON."""
    return REPO_ROOT / "constant" / "electrical" / "electrical_components.json"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory holding the electrical_simulation test fixture JSONs."""
    return FIXTURES_DIR


@pytest.fixture
def fixture_json(fixtures_dir: Path):
    """Factory: ``fixture_json("name.json")`` -> parsed dict (fresh copy)."""

    def _load(filename: str) -> dict:
        return deepcopy(_read_json(fixtures_dir / filename))

    return _load


@pytest.fixture
def test_components_path(fixtures_dir: Path) -> Path:
    """Path to the test component specification JSON."""
    return fixtures_dir / TEST_COMPONENTS_FILE


@pytest.fixture
def test_components(fixture_json) -> dict:
    """Test component specs (Test_Panel, Test_MPPT, Test_Battery, loads...)."""
    return fixture_json(TEST_COMPONENTS_FILE)


@pytest.fixture
def circuit_config_path(fixtures_dir: Path):
    """Factory: circuit name -> path of its circuit setup JSON fixture."""

    def _path(name: str) -> Path:
        filename = name if name.endswith(".json") else f"{name}.json"
        return fixtures_dir / filename

    return _path


@pytest.fixture
def circuit_config(fixture_json):
    """Factory: circuit name (e.g. "charging_only_1panel") -> config dict.

    Returns an unresolved circuit setup: component choices are still
    references, so tests decide whether to call ``combine_config_setup``.
    """

    def _load(name: str) -> dict:
        filename = name if name.endswith(".json") else f"{name}.json"
        return fixture_json(filename)

    return _load


@pytest.fixture
def resolved_circuit_config(circuit_config, test_components):
    """Factory: circuit name -> config dict with component choices merged in.

    Mirrors what ``__main__.main`` does before handing the config to
    ``build_circuit_from_json``.
    """

    def _load(name: str) -> dict:
        from src.electrical_simulation.__main__ import combine_config_setup

        config = circuit_config(name)
        combine_config_setup(config, test_components)
        return config

    return _load


@pytest.fixture
def voyage_config(fixture_json) -> dict:
    """Short multi-segment voyage config used by voyage tests."""
    return fixture_json(TEST_VOYAGE_FILE)


@pytest.fixture
def test_boat_params() -> dict:
    """Minimal boat params exercising the panel arrangement override path.

    Keys match those read by ``apply_boat_panel_config``: in_series becomes
    panels_per_string (2) and in_parallel becomes
    panels_longitudinal // panels_transversal (4 // 2 = 2).
    """
    return {
        "panels_per_string": 2,
        "panels_longitudinal": 4,
        "panels_transversal": 2,
    }
