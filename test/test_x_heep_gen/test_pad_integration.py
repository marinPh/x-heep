"""Integration tests for pad configuration in both hjson and Python formats."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import pytest
from deepdiff import DeepDiff


# Test parameters: (config_format, pads_cfg_path)
PAD_CONFIG_FORMATS = [
    ("hjson", "test/test_x_heep_gen/pads/pad_cfg.hjson"),
    ("python", "test/test_x_heep_gen/pads/pad_cfg.py"),
]


def _format_list_delta(prefix: str, old_list: list, new_list: list) -> str:
    """
    Produce a compact diff for two lists.
    Shows:
    - removed items
    - added items
    - changed items (same index but different content)
    """
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
                # If both are dicts → reuse dict diff
                if isinstance(old, dict) and isinstance(new, dict):
                    nested = _format_dict_delta(f"{prefix}[{i}]", old, new)
                    lines.append("  " + nested.replace("\n", "\n  "))
                else:
                    lines.append(f"  * [{i}]: {old!r} → {new!r}")

    return "\n".join(lines)


def _format_dict_delta(prefix: str, old: dict, new: dict) -> str:
    """
    Produce a compact, per-key diff for two dicts.
    prefix is the DeepDiff path up to the dict (e.g. root['total_pad_list'][0])
    """
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
    """
    Format a value change.
    If both sides are dicts, dig into keys for a more precise diff.
    """
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

    # Build a compact, human-oriented diff summary
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

    # Items added/removed in iterables (lists, etc.)
    for path, items in diff.get("iterable_item_added", {}).items():
        lines.append(f"{path}: item added {items!r}")
    for path, items in diff.get("iterable_item_removed", {}).items():
        lines.append(f"{path}: item removed {items!r}")

    # Fallback: if nothing above triggered (unlikely), at least dump pretty()
    if not lines:
        lines.append("Raw DeepDiff.pretty():")
        lines.append(diff.pretty())

    diff_message = "\n".join(lines)

    # Optionally write to file
    if diff_output_path:
        diff_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(diff_output_path, "w") as df:
            df.write(diff_message)

    return False, diff_message


@pytest.mark.integration
@pytest.mark.golden
@pytest.mark.parametrize("config_format,pads_cfg_path", PAD_CONFIG_FORMATS)
def test_pad_config_generates_expected_output(
    config_format: str,
    pads_cfg_path: str,
    mcu_gen_runner,
    repo_root: Path,
    tmp_path: Path,
):
    """
    Test that both hjson and Python pad configurations generate the expected output.

    This test:
    1. Runs mcu-gen with the specified pad configuration
    2. Generates the kwargs_output.json from template
    3. Compares it against the golden reference
    """
    # Paths
    golden_output = (
        repo_root / "test" / "test_x_heep_gen" / "pads" / "golden_pads" / "kwargs_output.json"
    )
    generated_output = (
        repo_root / "test" / "test_x_heep_gen" / "pads" / "output" / "kwargs_output.json"
    )
    diff_output = tmp_path / f"diff_{config_format}.txt"

    # Step 1: Run mcu-gen with the pad configuration
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg=pads_cfg_path,
    )

    assert result.returncode == 0, (
        f"mcu-gen failed for {config_format} format:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 2: Generate the output template
    template_path = str(
        repo_root / "test" / "test_x_heep_gen" / "pads" / "output" / "kwargs_output.json.tpl"
    )
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg=pads_cfg_path,
        template=template_path,
    )

    assert result.returncode == 0, (
        f"Template generation failed for {config_format} format:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 3: Verify the generated output exists
    assert generated_output.exists(), (
        f"Generated output file not found: {generated_output}"
    )

    # Step 4: Compare against golden reference
    are_equal, diff_message = compare_json_files(
        golden_output, generated_output, diff_output
    )

    assert are_equal, (
        f"Pad configuration output differs for {config_format} format!\n"
        f"Detailed diff written to: {diff_output}\n\n"
        f"Summary of differences:\n{diff_message}"
    )


@pytest.mark.integration
@pytest.mark.parametrize("config_format,pads_cfg_path", PAD_CONFIG_FORMATS)
def test_pad_config_format_consistency(
    config_format: str,
    pads_cfg_path: str,
    mcu_gen_runner,
    repo_root: Path,
):
    """
    Test that the pad configuration file is valid and can be processed.

    This ensures that both hjson and Python formats are syntactically correct
    and can be parsed by mcu_gen.py.
    """
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg=pads_cfg_path,
    )

    assert result.returncode == 0, (
        f"Failed to process {config_format} pad configuration:\n"
        f"Config file: {pads_cfg_path}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
@pytest.mark.golden
def test_hjson_and_python_configs_produce_identical_output(
    mcu_gen_runner,
    repo_root: Path,
    tmp_path: Path,
):
    """
    Test that hjson and Python configurations produce identical outputs.

    This is a critical test ensuring backwards compatibility and that the
    Python abstraction layer works correctly.
    """
    hjson_output = tmp_path / "hjson_output.json"
    python_output = tmp_path / "python_output.json"
    template_path = str(
        repo_root / "test" / "test_x_heep_gen" / "pads" / "output" / "kwargs_output.json.tpl"
    )

    # Generate output for hjson format
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg="test/test_x_heep_gen/pads/pad_cfg.hjson",
    )
    assert result.returncode == 0, "hjson mcu-gen failed"

    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg="test/test_x_heep_gen/pads/pad_cfg.hjson",
        template=template_path,
    )
    assert result.returncode == 0, "hjson template generation failed"

    # Copy hjson output
    generated_output = (
        repo_root / "test" / "test_x_heep_gen" / "pads" / "output" / "kwargs_output.json"
    )
    import shutil

    shutil.copy(generated_output, hjson_output)

    # Generate output for Python format
    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg="test/test_x_heep_gen/pads/pad_cfg.py",
    )
    assert result.returncode == 0, "python mcu-gen failed"

    result = mcu_gen_runner(
        xheep_cfg="configs/ci.hjson",
        pads_cfg="test/test_x_heep_gen/pads/pad_cfg.py",
        template=template_path,
    )
    assert result.returncode == 0, "python template generation failed"

    shutil.copy(generated_output, python_output)

    # Compare outputs
    are_equal, diff_message = compare_json_files(
        hjson_output, python_output, tmp_path / "format_diff.txt"
    )

    assert are_equal, (
        f"Hjson and Python configurations produce different outputs!\n"
        f"This indicates the Python abstraction layer is not compatible.\n\n"
        f"Diff details:\n{diff_message}"
    )
