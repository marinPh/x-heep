import json
from pathlib import Path
import os
from deepdiff import DeepDiff


def _format_list_delta(prefix, old_list, new_list):
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


def _format_dict_delta(prefix, old, new):
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


def _format_value_change(path, old, new):
    """
    Format a value change.
    If both sides are dicts, dig into keys for a more precise diff.
    """
    if isinstance(old, dict) and isinstance(new, dict):
        return _format_dict_delta(path, old, new)
    elif isinstance(old, list) and isinstance(new, list):
        return _format_list_delta(path, old, new)
    return f"{path}: {old!r} → {new!r}"


def compare_json(file_a, file_b):
    base_dir = os.path.dirname(__file__)
    path_a = os.path.join(base_dir, file_a)
    path_b = os.path.join(base_dir, file_b)

    with open(path_a) as fa, open(path_b) as fb:
        a = json.load(fa)
        b = json.load(fb)

    if a == b:
        print("✅ JSONs are identical")
        return True

    print("❌ JSONs differ")

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

    diff_file = os.path.join(base_dir, "diff_output.txt")
    with open(diff_file, "w") as df:
        df.write("\n".join(lines))

    print(f"Diff written to {diff_file}")
    return False


if __name__ == "__main__":
    compare_json(
        "./pads/golden_pads/kwargs_output.json", "./pads/output/kwargs_output.json"
    )
