#!/usr/bin/env python3
"""
CLI pad-ring visualiser for kwargs_output.json.

Usage:
    python pad_visualizer.py kwargs_output.json
"""

import json
import argparse
from collections import defaultdict
from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Data loading / grouping
# ---------------------------------------------------------------------------


def load_kwargs(path: str) -> Dict[str, Any]:
    """Load the kwargs_output.json produced by PadRing."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def group_pads_by_side(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group pads by pad_mapping (top/right/bottom/left) and sort them in a
    reasonably physical order using layout_index and layout_offset.
    """
    pads = data.get("pad_list", [])
    sides: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for p in pads:
        side = p.get("pad_mapping", "top")
        sides[side].append(p)

    def sort_key(p: Dict[str, Any]):
        offset = p.get("layout_offset")
        if offset is None:
            offset = 0.0
        return (p.get("layout_index", 0), float(offset), p.get("index", 0))

    for side in sides:
        sides[side].sort(key=sort_key)

    return sides


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_side_horizontal(
    prefix: str, pads: List[Dict[str, Any]], width: int = 100
) -> str:
    """
    Single line listing pads on one side:
      TOP   [jtag_tdi] [uart_rx] [uart_tx] ...
    """
    if not pads:
        return f"{prefix:<6}(no pads)"

    names = [f"[{p['name']}]" for p in pads]
    line = f"{prefix:<6}" + " ".join(names)
    if len(line) > width:
        line = line[: width - 3] + "..."
    return line


def format_side_offsets(
    prefix: str, pads: List[Dict[str, Any]], width: int = 120
) -> str:
    """
    Show offset / skip values along an edge, e.g.:

      TOP   offset=705->[jtag_tdi] --40->[uart_rx] --37.5->[uart_tx] ...
    """
    if not pads:
        return f"{prefix:<6}(no pads)"

    parts = [f"{prefix:<6}"]
    first = True

    for p in pads:
        name = p["name"]
        off = p.get("layout_offset")
        skip = p.get("layout_skip")

        if first:
            if off is not None:
                parts.append(f"offset={off:g}->[{name}]")
            else:
                parts.append(f"[{name}]")
            first = False
        else:
            if skip is not None:
                parts.append(f"--{skip:g}->[{name}]")
            else:
                parts.append(f"-->[{name}]")

    line = " ".join(parts)
    if len(line) > width:
        line = line[: width - 3] + "..."
    return line


def format_vertical_sides(
    left: List[Dict[str, Any]],
    right: List[Dict[str, Any]],
    core_width: int = 30,
) -> List[str]:
    """
    Produce vertical view:

           +------------------------------+
      gpio_7 |           CORE AREA        | clk
      gpio_8 |                            | rst
           +------------------------------+
    """
    max_rows = max(len(left), len(right), 3)
    left_names = [p["name"] for p in left]
    right_names = [p["name"] for p in right]

    lines: List[str] = []
    border = "-" * core_width
    header = f"{'':>12} +{border}+"
    lines.append(header)

    for i in range(max_rows):
        ln = left_names[i] if i < len(left) else ""
        rn = right_names[i] if i < len(right) else ""
        core_label = "CORE AREA" if i == max_rows // 2 else ""
        core_str = core_label.center(core_width)
        line = f"{ln:>12} |{core_str}| {rn:<12}"
        lines.append(line)

    footer = f"{'':>12} +{border}+"
    lines.append(footer)
    return lines


def format_side_vertical_offsets(side_name: str, pads: List[Dict[str, Any]]) -> str:
    """
    Vertical listing of offset/skip for LEFT/RIGHT sides (top → bottom):

      LEFT side (top→bottom):
        offset=90     -> pad0
        skip=40       -> pad1
        skip=40       -> pad2
        ...
    """
    lines: List[str] = [f"{side_name} side (top→bottom):"]
    if not pads:
        lines.append("  (no pads)")
        return "\n".join(lines)

    first = True
    for p in pads:
        name = p["name"]
        off = p.get("layout_offset")
        skip = p.get("layout_skip")

        if first:
            if off is not None:
                # 8-char, generic float/int formatting
                lines.append(f"  offset={off:<8g} -> {name}")
            else:
                lines.append(f"  -> {name}")
            first = False
        else:
            if skip is not None:
                lines.append(f"  skip={skip:<8g} -> {name}")
            else:
                lines.append(f"  -> {name}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Summary (edge_offset, spacing, etc.)
# ---------------------------------------------------------------------------


def print_summary(data: Dict[str, Any]) -> None:
    pa = data.get("physical_attributes", {})
    fp = pa.get("floorplan_dimensions", {})
    edge = pa.get("edge_offset", {})
    spacing = pa.get("spacing", {})
    dims = pa.get("dimensions", {})

    print("== Physical attributes ==")
    print(
        f"  floorplan_dimensions: width={fp.get('width')}um, length={fp.get('length')}um"
    )
    print(
        f"  edge_offset:          pad={edge.get('pad')}um, bondpad={edge.get('bondpad')}um"
    )
    print(f"  spacing:              bondpad={spacing.get('bondpad')}um")
    if "cell" in spacing:
        print(f"                         cell={spacing.get('cell')}um")
    print(f"  # distinct cells in 'dimensions': {len(dims)}")
    print()

    bp_offsets = data.get("bondpad_offsets") or {}
    if bp_offsets:
        print("  bondpad_offsets per side (distance from corner along edge):")
        for side, val in bp_offsets.items():
            print(f"    {side:>6}: {val}um")
        print()
    print()


# ---------------------------------------------------------------------------
# Top-level visualisation
# ---------------------------------------------------------------------------


def visualize(path: str) -> None:
    data = load_kwargs(path)
    print_summary(data)

    sides = group_pads_by_side(data)
    top = sides.get("top", [])
    bottom = sides.get("bottom", [])
    left = sides.get("left", [])
    right = sides.get("right", [])

    print("== Pad mapping by side ==")
    # TOP
    print(format_side_horizontal("TOP", top))
    print(format_side_offsets("TOP", top))
    print()

    # LEFT / RIGHT + core box
    for line in format_vertical_sides(left, right):
        print(line)
    print()

    # LEFT / RIGHT offsets/skips
    print(format_side_vertical_offsets("LEFT", left))
    print()
    print(format_side_vertical_offsets("RIGHT", right))
    print()

    # BOTTOM
    print(format_side_horizontal("BOTTOM", bottom))
    print(format_side_offsets("BOTTOM", bottom))
    print()

    print("Legend:")
    print(
        "  offset=X->[pad]: along-edge distance from corner to the FIRST pad on that side."
    )
    print("  skip=Y  ->[pad]: spacing between consecutive pads along that side.")
    print(
        "  edge_offset.pad / .bondpad: radial distance from chip edge to pad/bondpad rows."
    )
    print(
        "  bondpad_offsets[side]: along-edge offset of the first bondpad on that side."
    )
    print("  Vertical box: conceptual core area with left/right pads top→bottom.")


# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="CLI pad-ring visualiser.")
    parser.add_argument(
        "json_path",
        help="Path to kwargs_output.json generated by PadRing",
    )
    args = parser.parse_args()
    visualize(args.json_path)


if __name__ == "__main__":
    main()
