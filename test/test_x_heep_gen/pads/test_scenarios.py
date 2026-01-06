"""Scenario-based integration tests for pad configurations.

This module automatically discovers and tests all pad configuration scenarios.
Each scenario is a directory containing hjson and python configurations with
expected golden outputs.

Adding a new scenario:
    1. Create directory: test/test_x_heep_gen/scenarios/<scenario_name>/
    2. Add configs: hjson/config.hjson and python/config.py
    3. Add golden: golden/kwargs_output.json
    4. Run tests - new scenario automatically discovered!
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pytest
from deepdiff import DeepDiff


# Scenario discovery
def discover_scenarios(scenarios_dir: Path) -> List[str]:
    """
    Discover all test scenarios by finding subdirectories.

    Returns:
        List of scenario names (directory names)
    """
    if not scenarios_dir.exists():
        return []

    scenarios = []
    for path in scenarios_dir.iterdir():
        if path.is_dir() and not path.name.startswith("_"):
            # Verify scenario structure
            hjson_dir = path / "hjson"
            python_dir = path / "python"
            golden_dir = path / "golden"

            if hjson_dir.exists() or python_dir.exists():
                scenarios.append(path.name)

    return sorted(scenarios)


# Get scenarios directory
SCENARIOS_DIR = Path(__file__).parent / "scenarios"
AVAILABLE_SCENARIOS = discover_scenarios(SCENARIOS_DIR)


def get_scenario_configs(scenario_name: str) -> Dict[str, Path]:
    """
    Get configuration file paths for a scenario.

    Args:
        scenario_name: Name of the scenario

    Returns:
        Dictionary with keys: 'hjson', 'python', 'golden'
    """
    scenario_dir = SCENARIOS_DIR / scenario_name

    return {
        "hjson": scenario_dir / "hjson" / "config.hjson",
        "python": scenario_dir / "python" / "config.py",
        "golden": scenario_dir / "golden" / "kwargs_output.json",
        "output_dir": scenario_dir / "output",
    }


# Build test parameters: [(scenario, format, config_path), ...]
def build_test_parameters() -> List[Tuple[str, str, Path]]:
    """
    Build parametrized test cases for all scenarios and formats.

    Returns:
        List of tuples: (scenario_name, format_name, config_path)
    """
    params = []
    for scenario in AVAILABLE_SCENARIOS:
        configs = get_scenario_configs(scenario)

        if configs["hjson"].exists():
            params.append((scenario, "hjson", configs["hjson"]))

        if configs["python"].exists():
            params.append((scenario, "python", configs["python"]))

    return params


TEST_PARAMETERS = build_test_parameters()


def _format_list_delta(prefix: str, old_list: list, new_list: list) -> str:
    """Produce a compact diff for two lists."""
    lines = [f"{prefix}: list changed:"]
    max_len = max(len(old_list), len(new_list))

    for i in range(max_len):
        in_old = i < len(old_list)
        in_new = i < len(new_list)

        if in_old and not in_new:
            lines.append(f"  - [{i}]: {old_list[i]!r}  (removed)")
        elif not in_old and in_new:
            lines.append(f"  + [{i}]: {new_list[i]!r}  (added)")
        else:
            old = old_list[i]
            new = new_list[i]
            if old != new:
                if isinstance(old, dict) and isinstance(new, dict):
                    nested = _format_dict_delta(f"{prefix}[{i}]", old, new)
                    lines.append("  " + nested.replace("\n", "\n  "))
                else:
                    lines.append(f"  * [{i}]: {old!r} → {new!r}")

    return "\n".join(lines)


def _format_dict_delta(prefix: str, old: dict, new: dict) -> str:
    """Produce a compact, per-key diff for two dicts."""
    lines = [f"{prefix}: dict changed:"]
    all_keys = sorted(set(old.keys()) | set(new.keys()))

    for k in all_keys:
        in_old = k in old
        in_new = k in new

        if in_old and not in_new:
            lines.append(f"  - {k}: {old[k]!r}  (removed)")
        elif not in_old and in_new:
            lines.append(f"  + {k}: {new[k]!r}  (added)")
        else:
            if old[k] != new[k]:
                if type(old[k]) == type(new[k]):
                    return _format_value_change(f"{prefix}['{k}']", old[k], new[k])
                else:
                    lines.append(f"  * {k}: {old[k]!r} → {new[k]!r}")

    return "\n".join(lines)


def _format_value_change(path: str, old: Any, new: Any) -> str:
    """Format a value change."""
    if isinstance(old, dict) and isinstance(new, dict):
        return _format_dict_delta(path, old, new)
    elif isinstance(old, list) and isinstance(new, list):
        return _format_list_delta(path, old, new)
    return f"{path}: {old!r} → {new!r}"


def compare_json_files(
    file_a: Path, file_b: Path, diff_output_path: Path = None
) -> Tuple[bool, str]:
    """
    Compare two JSON files and return (are_equal, diff_message).

    Args:
        file_a: Path to first JSON file (typically golden)
        file_b: Path to second JSON file (typically generated)
        diff_output_path: Optional path to write detailed diff output

    Returns:
        Tuple of (are_equal: bool, diff_message: str)
    """
    with open(file_a) as fa, open(file_b) as fb:
        a = json.load(fa)
        b = json.load(fb)

    if a == b:
        return True, "JSONs are identical"

    diff = DeepDiff(a, b, ignore_order=True, significant_digits=6)

    lines = []

    # Values changed
    for path, change in diff.get("values_changed", {}).items():
        old = change["old_value"]
        new = change["new_value"]
        lines.append(_format_value_change(path, old, new))

    # Type changes
    for path, change in diff.get("type_changes", {}).items():
        old = change["old_value"]
        new = change["new_value"]
        lines.append(
            f"{path}: TYPE {type(old).__name__} → {type(new).__name__} "
            f"(values: {old!r} → {new!r})"
        )

    # Items added/removed in dicts
    for path in diff.get("dictionary_item_added", []):
        lines.append(f"{path}: (dict item added)")
    for path in diff.get("dictionary_item_removed", []):
        lines.append(f"{path}: (dict item removed)")

    # Items added/removed in iterables
    for path, items in diff.get("iterable_item_added", {}).items():
        lines.append(f"{path}: item added {items!r}")
    for path, items in diff.get("iterable_item_removed", {}).items():
        lines.append(f"{path}: item removed {items!r}")

    if not lines:
        lines.append("Raw DeepDiff.pretty():")
        lines.append(diff.pretty())

    diff_message = "\n".join(lines)

    if diff_output_path:
        diff_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(diff_output_path, "w") as df:
            df.write(diff_message)

    return False, diff_message


@pytest.mark.integration
@pytest.mark.golden
@pytest.mark.parametrize("scenario,config_format,config_path", TEST_PARAMETERS)
def test_scenario_generates_expected_output(
    scenario: str,
    config_format: str,
    config_path: Path,
    mcu_gen_runner,
    repo_root: Path,
    tmp_path: Path,
):
    """
    Test that each scenario's configuration generates the expected output.

    This test runs for every (scenario, format) combination discovered.
    Adding a new scenario directory automatically adds test cases.

    Args:
        scenario: Name of the test scenario
        config_format: Configuration format (hjson or python)
        config_path: Path to the configuration file
        mcu_gen_runner: Fixture to run mcu_gen.py
        repo_root: Repository root path
        tmp_path: Pytest temporary directory
    """
    configs = get_scenario_configs(scenario)
    golden_output = configs["golden"]

    # Ensure output directory exists
    output_dir = configs["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_output = output_dir / "kwargs_output.json"

    # Construct relative path for mcu_gen
    relative_config_path = config_path.relative_to(repo_root)

    # Step 1: Run mcu-gen with the scenario configuration
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg=str(relative_config_path),
    )

    assert result.returncode == 0, (
        f"mcu-gen failed for scenario '{scenario}' with {config_format} format:\n"
        f"Config: {config_path}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 2: Generate the output template
    template_path = str(output_dir / "kwargs_output.json.tpl")

    # Create template if it doesn't exist (copy from reference)
    template_file = Path(template_path)
    if not template_file.exists():
        reference_template = (
            repo_root
            / "test"
            / "test_x_heep_gen"
            / "pads"
            / "output"
            / "kwargs_output.json.tpl"
        )
        if reference_template.exists():
            shutil.copy(reference_template, template_file)

    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg=str(relative_config_path),
        template=template_path,
    )

    assert result.returncode == 0, (
        f"Template generation failed for scenario '{scenario}' with {config_format}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 3: Verify the generated output exists
    assert generated_output.exists(), (
        f"Generated output file not found: {generated_output}\n"
        f"Scenario: {scenario}, Format: {config_format}"
    )

    # Step 4: Compare against golden reference (if exists)
    if golden_output.exists():
        diff_output = tmp_path / f"diff_{scenario}_{config_format}.txt"

        are_equal, diff_message = compare_json_files(
            golden_output, generated_output, diff_output
        )

        assert are_equal, (
            f"Scenario '{scenario}' output differs for {config_format} format!\n"
            f"Detailed diff written to: {diff_output}\n\n"
            f"Summary of differences:\n{diff_message}"
        )
    else:
        pytest.skip(
            f"Golden reference not found for scenario '{scenario}': {golden_output}\n"
            f"Generated output saved to: {generated_output}\n"
            f"Review and copy to golden if correct."
        )


@pytest.mark.integration
def test_all_scenarios_cross_format_consistency(
    mcu_gen_runner,
    repo_root: Path,
    tmp_path: Path,
):
    """
    Test that hjson and python formats produce identical outputs for each scenario.

    This ensures backwards compatibility across all scenarios.
    """
    failures = []

    for scenario in AVAILABLE_SCENARIOS:
        configs = get_scenario_configs(scenario)

        # Skip if either format is missing
        if not configs["hjson"].exists() or not configs["python"].exists():
            continue

        # Output directory
        output_dir = configs["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        hjson_output = tmp_path / f"{scenario}_hjson_output.json"
        python_output = tmp_path / f"{scenario}_python_output.json"
        template_path = str(output_dir / "kwargs_output.json.tpl")

        # Create template if needed
        template_file = Path(template_path)
        if not template_file.exists():
            reference_template = (
                repo_root
                / "test"
                / "test_x_heep_gen"
                / "pads"
                / "output"
                / "kwargs_output.json.tpl"
            )
            if reference_template.exists():
                shutil.copy(reference_template, template_file)

        # Generate output for hjson
        relative_hjson = configs["hjson"].relative_to(repo_root)
        result = mcu_gen_runner(
            xheep_cfg="configs/ci.hjson",
            pads_cfg=str(relative_hjson),
        )
        if result.returncode != 0:
            failures.append(
                f"Scenario '{scenario}': hjson mcu-gen failed\n{result.stderr}"
            )
            continue

        result = mcu_gen_runner(
            xheep_cfg="configs/ci.hjson",
            pads_cfg=str(relative_hjson),
            template=template_path,
        )
        if result.returncode != 0:
            failures.append(
                f"Scenario '{scenario}': hjson template generation failed\n{result.stderr}"
            )
            continue

        generated = output_dir / "kwargs_output.json"
        shutil.copy(generated, hjson_output)

        # Generate output for python
        relative_python = configs["python"].relative_to(repo_root)
        result = mcu_gen_runner(
            xheep_cfg="configs/ci.hjson",
            pads_cfg=str(relative_python),
        )
        if result.returncode != 0:
            failures.append(
                f"Scenario '{scenario}': python mcu-gen failed\n{result.stderr}"
            )
            continue

        result = mcu_gen_runner(
            xheep_cfg="configs/ci.hjson",
            pads_cfg=str(relative_python),
            template=template_path,
        )
        if result.returncode != 0:
            failures.append(
                f"Scenario '{scenario}': python template generation failed\n{result.stderr}"
            )
            continue

        shutil.copy(generated, python_output)

        # Compare outputs
        are_equal, diff_message = compare_json_files(
            hjson_output, python_output, tmp_path / f"diff_{scenario}_formats.txt"
        )

        if not are_equal:
            failures.append(
                f"Scenario '{scenario}': hjson and python produce different outputs!\n"
                f"{diff_message}"
            )

    # Assert all scenarios passed
    if failures:
        failure_report = "\n\n".join(failures)
        pytest.fail(
            f"Cross-format consistency check failed for {len(failures)} scenario(s):\n\n"
            f"{failure_report}"
        )


def test_scenario_discovery():
    """Test that scenario discovery works and finds expected scenarios."""
    assert len(AVAILABLE_SCENARIOS) > 0, (
        f"No scenarios discovered in {SCENARIOS_DIR}\n"
        f"Expected at least one scenario directory with hjson/ or python/ subdirectories."
    )

    print(f"\nDiscovered {len(AVAILABLE_SCENARIOS)} scenario(s):")
    for scenario in AVAILABLE_SCENARIOS:
        configs = get_scenario_configs(scenario)
        has_hjson = "✓" if configs["hjson"].exists() else "✗"
        has_python = "✓" if configs["python"].exists() else "✗"
        has_golden = "✓" if configs["golden"].exists() else "✗"

        print(
            f"  - {scenario}: hjson={has_hjson}, python={has_python}, golden={has_golden}"
        )
