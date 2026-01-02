"""Pytest configuration for x_heep_gen tests."""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any
import pytest


@pytest.fixture(scope="session")
def test_dir() -> Path:
    """Return the test directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def build_dir(repo_root: Path) -> Path:
    """Return the build directory path."""
    return repo_root / "build"


@pytest.fixture
def xheep_config_cache(build_dir: Path) -> Path:
    """Return the cached xheep configuration file path."""
    return build_dir / "xheep_config_cache.pickle"


def run_mcu_gen(
    repo_root: Path,
    xheep_cfg: str,
    pads_cfg: str,
    xheep_config_cache: Path,
    template: str = None,
) -> subprocess.CompletedProcess:
    """
    Run mcu_gen.py with the specified configuration.

    Args:
        repo_root: Repository root directory
        xheep_cfg: Path to X-HEEP configuration file
        pads_cfg: Path to pads configuration file
        xheep_config_cache: Path to the cache file
        template: Optional template file to generate

    Returns:
        CompletedProcess with command results
    """
    python_cmd = repo_root / ".venv" / "bin" / "python"
    if not python_cmd.exists():
        python_cmd = "python3"

    mcu_gen_script = repo_root / "util" / "mcu_gen.py"

    if template:
        # Run cached template generation
        cmd = [
            str(python_cmd),
            str(mcu_gen_script),
            "--cached_path",
            str(xheep_config_cache),
            "--cached",
            "--outtpl",
            template,
        ]
    else:
        # Run full mcu-gen
        cmd = [
            str(python_cmd),
            str(mcu_gen_script),
            "--cached_path",
            str(xheep_config_cache),
            "--config",
            xheep_cfg,
            "--pads_cfg",
            pads_cfg,
        ]

    result = subprocess.run(
        cmd, cwd=repo_root, capture_output=True, text=True, check=False
    )

    return result


@pytest.fixture
def mcu_gen_runner(repo_root: Path, xheep_config_cache: Path):
    """
    Fixture that returns a function to run mcu_gen.py.

    Usage:
        def test_something(mcu_gen_runner):
            result = mcu_gen_runner(xheep_cfg="...", pads_cfg="...")
            assert result.returncode == 0
    """

    def _runner(xheep_cfg: str, pads_cfg: str, template: str = None):
        return run_mcu_gen(repo_root, xheep_cfg, pads_cfg, xheep_config_cache, template)

    return _runner


@pytest.fixture
def load_json():
    """Fixture that returns a function to load JSON files."""

    def _load(file_path: Path) -> Dict[str, Any]:
        with open(file_path, "r") as f:
            return json.load(f)

    return _load
