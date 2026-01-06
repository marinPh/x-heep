"""Unit tests for PadRing.build() orchestration logic."""

import pytest
import sys
from pathlib import Path

# Add util/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "util"))

from x_heep_gen.pads.PadDef import (
    PadGroup,
    SinglePad,
    RangePad,
    MultiplexedPad,
    Dimension,
    Layout,
    PadType,
)
from x_heep_gen.pads.Pad import PadMapping, Orientation
from x_heep_gen.pads.PadRing import PadRing


def test_empty_padgroup_builds_successfully():
    """Test that empty PadGroup builds without errors."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="empty_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should have zero pads
    assert pad_ring.total_pad == 0
    assert pad_ring.total_pad_muxed == 0
    assert len(pad_ring.pad_list) == 0


def test_single_pads_only(sample_pad_layout):
    """Test PadGroup with only SinglePads."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="single_pads_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Add 3 single pads
    for i in range(3):
        pad = SinglePad(
            name=f"pad_{i}",
            layout_index=i,
            type=PadType.INOUT,
            mapping=PadMapping.TOP,
            layout=sample_pad_layout,
            orient=Orientation.R0,
        )
        pad_group.add_pad(pad)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should have 3 pads
    assert pad_ring.total_pad == 3
    assert pad_ring.total_pad_muxed == 0
    assert len(pad_ring.pad_list) == 3
    assert len(pad_ring.top_pad_list) == 3


def test_range_pad_expansion(sample_pad_layout):
    """Test that RangePad expands into multiple pads."""
    fp_dim = Dimension(width=2000, length=2000)
    pad_group = PadGroup(
        name="range_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Add RangePad that should expand to 5 pads
    range_pad = RangePad(
        name="gpio",
        layout_index=0,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=sample_pad_layout,
        num=5,
        offset=0,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(range_pad)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should have 5 pads from expansion
    assert pad_ring.total_pad == 5
    assert len(pad_ring.pad_list) == 5
    assert len(pad_ring.left_pad_list) == 5


def test_multiplexed_pad_mux_selector_width(sample_pad_layout):
    """Test mux selector width calculation for MultiplexedPad."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="mux_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Create multiplexed pad with 4 alternatives
    # 4 alts -> (4-1).bit_length() = 3.bit_length() = 2 bits needed
    alt1 = SinglePad(
        name="alt1",
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )
    alt2 = SinglePad(
        name="alt2",
        type=PadType.OUTPUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )
    alt3 = SinglePad(
        name="alt3",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )
    alt4 = SinglePad(
        name="alt4",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )

    mux_pad = MultiplexedPad(
        name="mux_pad",
        layout_index=0,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
        alts=[("alt1", alt1), ("alt2", alt2), ("alt3", alt3), ("alt4", alt4)],
    )
    pad_group.add_pad(mux_pad)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should have 1 multiplexed pad
    assert pad_ring.total_pad_muxed == 1
    # Mux selector width should be 2 bits (for 4 alternatives)
    assert pad_ring.max_total_pad_mux_bitlengh == 2


def test_mux_selector_width_edge_cases(sample_pad_layout):
    """Test mux selector width for different numbers of alternatives."""
    test_cases = [
        (2, 1),  # 2 alts -> (2-1).bit_length() = 1.bit_length() = 1 bit
        (3, 2),  # 3 alts -> (3-1).bit_length() = 2.bit_length() = 2 bits
        (4, 2),  # 4 alts -> (4-1).bit_length() = 3.bit_length() = 2 bits
        (8, 3),  # 8 alts -> (8-1).bit_length() = 7.bit_length() = 3 bits
        (16, 4),  # 16 alts -> (16-1).bit_length() = 15.bit_length() = 4 bits
    ]

    for num_alts, expected_bits in test_cases:
        fp_dim = Dimension(width=1000, length=1000)
        pad_group = PadGroup(
            name=f"mux_test_{num_alts}",
            pad_edge_offset=50,
            bondpad_edge_offset=20,
            bp_spacing=25,
            cell_spacing=None,
            fp_dim=fp_dim,
        )

        # Create alternatives
        alts = []
        for i in range(num_alts):
            alt = SinglePad(
                name=f"alt{i}",
                type=PadType.INOUT,
                mapping=PadMapping.TOP,
                layout=sample_pad_layout,
                orient=Orientation.R0,
            )
            alts.append((f"alt{i}", alt))

        mux_pad = MultiplexedPad(
            name="mux_pad",
            layout_index=0,
            type=PadType.INOUT,
            mapping=PadMapping.TOP,
            layout=sample_pad_layout,
            orient=Orientation.R0,
            alts=alts,
        )
        pad_group.add_pad(mux_pad)

        pad_ring = PadRing(pad_group)
        pad_ring.build()

        assert (
            pad_ring.max_total_pad_mux_bitlengh == expected_bits
        ), f"Failed for {num_alts} alternatives: expected {expected_bits} bits, got {pad_ring.max_total_pad_mux_bitlengh}"


def test_mixed_pad_types(sample_pad_layout):
    """Test PadGroup with mix of Single, Range, and Multiplexed pads."""
    fp_dim = Dimension(width=3000, length=3000)
    pad_group = PadGroup(
        name="mixed_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Add 2 single pads
    clk = SinglePad(
        name="clk",
        layout_index=0,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=sample_pad_layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(clk)

    rst = SinglePad(
        name="rst",
        layout_index=1,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=sample_pad_layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(rst)

    # Add range pad (3 GPIOs)
    gpio = RangePad(
        name="gpio",
        layout_index=2,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=sample_pad_layout,
        num=3,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(gpio)

    # Add multiplexed pad (2 alts)
    alt1 = SinglePad(
        name="uart_rx",
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )
    alt2 = SinglePad(
        name="spi_miso",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )

    mux_pad = MultiplexedPad(
        name="mux_pad",
        layout_index=3,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
        alts=[("uart_rx", alt1), ("spi_miso", alt2)],
    )
    pad_group.add_pad(mux_pad)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Total: 2 single + 3 from range + 1 mux = 6 pads
    assert pad_ring.total_pad == 6
    # 1 multiplexed pad
    assert pad_ring.total_pad_muxed == 1
    # Mux width: 2 alts -> 1 bit
    assert pad_ring.max_total_pad_mux_bitlengh == 1


def test_side_based_separation(sample_pad_layout):
    """Test that pads are correctly separated by side."""
    fp_dim = Dimension(width=2000, length=2000)
    pad_group = PadGroup(
        name="sides_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Add pads to each side
    pad_top = SinglePad(
        name="top",
        layout_index=0,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=sample_pad_layout,
        orient=Orientation.R0,
    )
    pad_bottom = SinglePad(
        name="bottom",
        layout_index=1,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=sample_pad_layout,
        orient=Orientation.MX,
    )
    pad_left = SinglePad(
        name="left",
        layout_index=2,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=sample_pad_layout,
        orient=Orientation.MX90,
    )
    pad_right = SinglePad(
        name="right",
        layout_index=3,
        type=PadType.INOUT,
        mapping=PadMapping.RIGHT,
        layout=sample_pad_layout,
        orient=Orientation.R90,
    )

    pad_group.add_pad(pad_top)
    pad_group.add_pad(pad_bottom)
    pad_group.add_pad(pad_left)
    pad_group.add_pad(pad_right)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should have 1 pad on each side
    assert len(pad_ring.top_pad_list) == 1
    assert len(pad_ring.bottom_pad_list) == 1
    assert len(pad_ring.left_pad_list) == 1
    assert len(pad_ring.right_pad_list) == 1
    assert pad_ring.total_pad == 4


def test_pads_without_physical_layout():
    """Test pads without physical layout attributes."""
    # No fp_dim - should still build
    pad_group = PadGroup(
        name="no_layout_test",
        pad_edge_offset=None,
        bondpad_edge_offset=None,
        bp_spacing=None,
        cell_spacing=None,
        fp_dim=None,
    )

    # Add pad without layout
    pad = SinglePad(
        name="bypass_pad",
        layout_index=0,
        type=PadType.BYPASS_INPUT,
        mapping=None,
        layout=None,
        orient=None,
    )
    pad_group.add_pad(pad)

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Should still build successfully
    assert pad_ring.total_pad == 1
    assert len(pad_ring.pad_list) == 1


def test_physical_attributes_populated():
    """Test that physical attributes are populated after build."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="attrs_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pad_ring = PadRing(pad_group)
    pad_ring.build()

    # Physical attributes should be populated
    assert pad_ring.physical_attributes is not None
    assert pad_ring.bondpad_offsets is not None
