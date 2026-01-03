"""Unit tests for JSON comparison logic (compare_json_files function)."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_scenarios import compare_json_files


def test_identical_files_returns_true(temp_json_files):
    """Test that identical JSON files return True."""
    data = {"key": "value", "number": 42, "nested": {"inner": "data"}}
    file1, file2 = temp_json_files(data, data)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is True
    assert "identical" in msg.lower()


def test_empty_files_are_identical(temp_json_files):
    """Test that empty JSON objects are considered identical."""
    file1, file2 = temp_json_files({}, {})

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is True


def test_value_change_detected(temp_json_files):
    """Test that value changes are detected and reported."""
    data1 = {"key": "old_value"}
    data2 = {"key": "new_value"}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "key" in msg
    assert "old_value" in msg
    assert "new_value" in msg


def test_type_change_detected(temp_json_files):
    """Test that type changes are detected (int → str)."""
    data1 = {"value": 42}
    data2 = {"value": "42"}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "TYPE" in msg
    assert "int" in msg
    assert "str" in msg


def test_nested_dict_addition_detected(temp_json_files):
    """Test that adding nested dictionary items is detected."""
    data1 = {"outer": {"inner1": "value"}}
    data2 = {"outer": {"inner1": "value", "inner2": "new"}}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "inner2" in msg
    assert "added" in msg.lower()


def test_nested_dict_removal_detected(temp_json_files):
    """Test that removing nested dictionary items is detected."""
    data1 = {"outer": {"inner1": "value", "inner2": "remove_me"}}
    data2 = {"outer": {"inner1": "value"}}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "inner2" in msg
    assert "removed" in msg.lower()


def test_list_item_addition_detected(temp_json_files):
    """Test that adding items to a list is detected."""
    data1 = {"items": [1, 2, 3]}
    data2 = {"items": [1, 2, 3, 4]}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "items" in msg
    assert "4" in msg


def test_list_item_removal_detected(temp_json_files):
    """Test that removing items from a list is detected."""
    data1 = {"items": [1, 2, 3, 4]}
    data2 = {"items": [1, 2, 3]}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "items" in msg


def test_mixed_nested_structures(temp_json_files):
    """Test dict containing lists containing dicts."""
    data1 = {"outer": [{"inner": 1}, {"inner": 2}]}
    data2 = {"outer": [{"inner": 1}, {"inner": 2}, {"inner": 3}]}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "inner" in msg or "outer" in msg


def test_none_values_handled(temp_json_files):
    """Test that None values are handled correctly."""
    data1 = {"key": None}
    data2 = {"key": "value"}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "None" in msg or "null" in msg.lower()


def test_empty_arrays_vs_empty_objects(temp_json_files):
    """Test that empty arrays and empty objects are different."""
    data1 = {"container": []}
    data2 = {"container": {}}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "TYPE" in msg


def test_floating_point_precision(temp_json_files):
    """Test that floating point comparison uses significant_digits=6."""
    # Values very close - within floating point representation
    data1 = {"value": 1.23456789}
    data2 = {"value": 1.23456789}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    # Identical floats should be equal
    assert are_equal is True


def test_floating_point_different_within_precision(temp_json_files):
    """Test that floats differing within precision are detected."""
    # Values differ within 6 significant digits - should be different
    data1 = {"value": 1.234567}
    data2 = {"value": 1.234568}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    assert "1.234567" in msg or "1.234568" in msg


def test_multiple_changes_all_reported(temp_json_files):
    """Test that multiple changes are all included in diff message."""
    data1 = {"a": 1, "b": {"nested": "old"}, "c": [1, 2]}
    data2 = {"a": 2, "b": {"nested": "new"}, "c": [1, 2, 3]}
    file1, file2 = temp_json_files(data1, data2)

    are_equal, msg = compare_json_files(file1, file2)

    assert are_equal is False
    # Should report change in 'a', 'nested', and list addition
    assert ("a" in msg or "root['a']" in msg)
    assert "nested" in msg
    assert ("c" in msg or "3" in msg)


def test_diff_output_path_writes_file(temp_json_files, tmp_path):
    """Test that diff_output_path parameter writes diff to file."""
    data1 = {"key": "old"}
    data2 = {"key": "new"}
    file1, file2 = temp_json_files(data1, data2)

    diff_output = tmp_path / "diff_output.txt"
    are_equal, msg = compare_json_files(file1, file2, diff_output_path=diff_output)

    assert are_equal is False
    assert diff_output.exists()

    diff_content = diff_output.read_text()
    assert "key" in diff_content
    assert "old" in diff_content
    assert "new" in diff_content
