"""Unit tests for geometric pad positioning logic (set_pad_positions function)."""

import pytest
import sys
from pathlib import Path

# Add util/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "util"))

from x_heep_gen.pads.PadDef import (
    PadGroup,
    SinglePad,
    Dimension,
    Layout,
    PadType,
    ValidationError,
)
from x_heep_gen.pads.Pad import PadMapping, Orientation
from x_heep_gen.pads.PadRing import set_pad_positions


def create_test_pad(
    name: str,
    mapping: PadMapping,
    bondpad_width: float,
    cell_width: float,
    layout_index: int = 0,
):
    """Helper to create a test pad with layout."""
    bondpad_dim = Dimension(width=bondpad_width, length=None, name=f"{name}_BP")
    cell_dim = Dimension(width=cell_width, length=None, name=f"{name}_CELL")
    layout = Layout(bond_pad=bondpad_dim, cell_pad=cell_dim)

    pad = SinglePad(
        name=name,
        layout_index=layout_index,
        type=PadType.INOUT,
        mapping=mapping,
        layout=layout,
        orient=Orientation.R0,
    )
    return pad


def calculate_expected_bp_offset(
    side_length: float, bp_widths: list, bp_spacing: float, edge_to_bp: float
) -> float:
    """Calculate expected bondpad offset using the algorithm formula."""
    bp_space = sum(bp_widths) + bp_spacing * (len(bp_widths) - 1)
    extra_space = side_length - bp_space - 2 * edge_to_bp
    return extra_space / 2


def calculate_expected_pad_offset(
    bp_offset: float,
    edge_to_pad: float,
    edge_to_bp: float,
    bp_width: float,
    pad_width: float,
) -> float:
    """Calculate expected first pad offset using the algorithm formula."""
    return bp_offset - (edge_to_pad - edge_to_bp) + (bp_width / 2) - (pad_width / 2)


def calculate_expected_skip(
    last_bp_width: float,
    bp_width: float,
    bp_spacing: float,
    last_pad_width: float,
    pad_width: float,
) -> float:
    """Calculate expected skip between pads using the algorithm formula."""
    return (
        (last_bp_width + bp_width) / 2 + bp_spacing - (last_pad_width + pad_width) / 2
    )


def test_single_pad_is_centered(sample_pad_group):
    """Test that a single pad is centered on the side."""
    # Floorplan is 1000x1000, bondpad edge offset is 20
    # Expected usable space: 1000 - 2*20 = 960
    # Bondpad is 60 wide
    # Extra space = 960 - 60 = 900
    # Offset should be 900/2 = 450

    pad = create_test_pad("test_pad", PadMapping.TOP, bondpad_width=60, cell_width=50)
    pad_list = [pad]

    set_pad_positions(sample_pad_group, pad_list)

    # Calculate expected offset using helper
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60], bp_spacing=25, edge_to_bp=20
    )
    expected_pad_offset = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=60,
        pad_width=50,
    )

    # Assert directly on pad properties
    # Manual: 450 - (50-20) + (60/2) - (50/2) = 450 - 30 + 30 - 25 = 425
    assert pad.layout.offset == pytest.approx(expected_pad_offset)
    assert pad.layout.offset == pytest.approx(425.0)


def test_multiple_equal_pads_evenly_spaced(sample_pad_group):
    """Test that multiple pads with equal sizes are evenly spaced."""
    # 3 pads, each with bondpad width 60
    # Spacing between bondpads is 25 (from sample_pad_group)
    # Total bondpad space = 60*3 + 25*2 = 230
    # Extra space = 1000 - 2*20 - 230 = 730
    # Offset = 730/2 = 365

    pads = [
        create_test_pad(
            f"pad_{i}", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=i
        )
        for i in range(3)
    ]

    bp_offset = set_pad_positions(sample_pad_group, pads)

    # Verify bondpad offset calculation
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60, 60, 60], bp_spacing=25, edge_to_bp=20
    )
    assert bp_offset == pytest.approx(expected_bp_offset)
    assert bp_offset == pytest.approx(365.0)

    # First pad should have calculated offset
    expected_first_offset = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=60,
        pad_width=50,
    )
    assert pads[0].layout.offset == pytest.approx(expected_first_offset)
    # Manual: 365 - (50-20) + (60/2) - (50/2) = 365 - 30 + 30 - 25 = 340
    assert pads[0].layout.offset == pytest.approx(340.0)

    # Second and third pads should have calculated skip (equal for equal-sized pads)
    expected_skip = calculate_expected_skip(
        last_bp_width=60, bp_width=60, bp_spacing=25, last_pad_width=50, pad_width=50
    )
    assert pads[1].layout.skip == pytest.approx(expected_skip)
    assert pads[2].layout.skip == pytest.approx(expected_skip)
    # Manual: (60+60)/2 + 25 - (50+50)/2 = 60 + 25 - 50 = 35
    assert pads[1].layout.skip == pytest.approx(35.0)
    assert pads[2].layout.skip == pytest.approx(35.0)


def test_pads_that_dont_fit_raise_error(sample_pad_group):
    """Test that pads exceeding side length raise ValueError."""
    # Floorplan is 1000 wide
    # Create 20 pads with bondpad width 60 each
    # Total: 60*20 + 25*19 = 1675 > 1000 - 2*20 = 960

    pads = [
        create_test_pad(
            f"pad_{i}", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=i
        )
        for i in range(20)
    ]

    with pytest.raises(ValueError, match="cannot fit"):
        set_pad_positions(sample_pad_group, pads)


def test_bondpad_centering_with_variable_widths(sample_pad_group):
    """Test bondpad centering with pads of different widths."""
    pads = [
        create_test_pad(
            "pad_0", PadMapping.TOP, bondpad_width=50, cell_width=40, layout_index=0
        ),
        create_test_pad(
            "pad_1", PadMapping.TOP, bondpad_width=70, cell_width=60, layout_index=1
        ),
        create_test_pad(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
    ]

    # Total bondpad space = 50 + 70 + 60 + 25*2 = 230
    # Extra space = 1000 - 2*20 - 230 = 730
    # Offset = 730/2 = 365

    bp_offset = set_pad_positions(sample_pad_group, pads)

    # Verify bondpad offset with variable widths
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[50, 70, 60], bp_spacing=25, edge_to_bp=20
    )
    assert bp_offset == pytest.approx(expected_bp_offset)
    assert bp_offset == pytest.approx(365.0)

    # Verify first pad offset
    expected_first_offset = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=50,
        pad_width=40,
    )
    assert pads[0].layout.offset == pytest.approx(expected_first_offset)
    # Manual: 365 - (50-20) + (50/2) - (40/2) = 365 - 30 + 25 - 20 = 340
    assert pads[0].layout.offset == pytest.approx(340.0)

    # Verify skip calculations for variable widths
    expected_skip_1 = calculate_expected_skip(
        last_bp_width=50, bp_width=70, bp_spacing=25, last_pad_width=40, pad_width=60
    )
    assert pads[1].layout.skip == pytest.approx(expected_skip_1)
    # Manual: (50+70)/2 + 25 - (40+60)/2 = 60 + 25 - 50 = 35
    assert pads[1].layout.skip == pytest.approx(35.0)

    expected_skip_2 = calculate_expected_skip(
        last_bp_width=70, bp_width=60, bp_spacing=25, last_pad_width=60, pad_width=50
    )
    assert pads[2].layout.skip == pytest.approx(expected_skip_2)
    # Manual: (70+60)/2 + 25 - (60+50)/2 = 65 + 25 - 55 = 35
    assert pads[2].layout.skip == pytest.approx(35.0)


def test_skip_parameter_calculation(sample_pad_group):
    """Test that skip parameter is calculated correctly."""
    pads = [
        create_test_pad(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad(
            "pad_1", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=1
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Skip calculation: (last_bp_width + bp_width)/2 + bp_spacing - (last_pad_width + pad_width)/2
    # = (60 + 60)/2 + 25 - (50 + 50)/2
    # = 60 + 25 - 50
    # = 35

    expected_skip = calculate_expected_skip(
        last_bp_width=60, bp_width=60, bp_spacing=25, last_pad_width=50, pad_width=50
    )
    assert pads[1].layout.skip == pytest.approx(expected_skip)
    assert pads[1].layout.skip == pytest.approx(35.0)


def test_different_edge_orientations():
    """Test positioning works for all edge orientations."""
    # Test TOP, BOTTOM, LEFT, RIGHT
    for mapping in [
        PadMapping.TOP,
        PadMapping.BOTTOM,
        PadMapping.LEFT,
        PadMapping.RIGHT,
    ]:
        fp_dim = Dimension(width=1000, length=1500)
        pad_group = PadGroup(
            name="test",
            pad_edge_offset=50,
            bondpad_edge_offset=20,
            bp_spacing=25,
            cell_spacing=None,
            fp_dim=fp_dim,
        )

        pad = create_test_pad("test_pad", mapping, bondpad_width=60, cell_width=50)
        pad_list = [pad]

        bp_offset = set_pad_positions(pad_group, pad_list)

        # Should calculate offset without errors
        assert bp_offset is not None
        assert pad.layout.offset is not None


def test_top_bottom_use_width_dimension():
    """Test that TOP and BOTTOM edges use floorplan width."""
    fp_dim = Dimension(width=800, length=1200)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pad = create_test_pad("test_pad", PadMapping.TOP, bondpad_width=60, cell_width=50)
    pad_list = [pad]

    bp_offset = set_pad_positions(pad_group, pad_list)

    # Width is 800, usable = 800 - 2*20 = 760
    # Extra space = 760 - 60 = 700
    # Offset = 700/2 = 350
    assert bp_offset == pytest.approx(350.0)


def test_left_right_use_length_dimension():
    """Test that LEFT and RIGHT edges use floorplan length."""
    fp_dim = Dimension(width=800, length=1200)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pad = create_test_pad("test_pad", PadMapping.RIGHT, bondpad_width=60, cell_width=50)
    pad_list = [pad]

    bp_offset = set_pad_positions(pad_group, pad_list)

    # Length is 1200, usable = 1200 - 2*20 = 1160
    # Extra space = 1160 - 60 = 1100
    # Offset = 1100/2 = 550
    assert bp_offset == pytest.approx(550.0)


def test_empty_pad_list_returns_zero():
    """Test that empty pad list returns 0."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    result = set_pad_positions(pad_group, [])

    assert result == 0.0


def test_maximum_pads_that_exactly_fit():
    """Test maximum number of pads that exactly fit the edge."""
    # Floorplan width = 1000, edge offsets = 20 each side
    # Usable space = 1000 - 2*20 = 960
    # Bondpad width = 60, spacing = 25
    # Equation: n*60 + (n-1)*25 = 960
    # 60n + 25n - 25 = 960
    # 85n = 985
    # n = 11.58... so n=11 should fit, n=12 should not

    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # 11 pads should fit
    pads_11 = [
        create_test_pad(
            f"pad_{i}", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=i
        )
        for i in range(11)
    ]

    bp_offset = set_pad_positions(pad_group, pads_11)
    assert bp_offset >= 0  # Should succeed

    # 12 pads should not fit
    pads_12 = [
        create_test_pad(
            f"pad_{i}", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=i
        )
        for i in range(12)
    ]

    with pytest.raises(ValueError, match="cannot fit"):
        set_pad_positions(pad_group, pads_12)


def test_edge_offset_spacing_interaction():
    """Test interaction between edge offset and spacing."""
    # Large edge offset reduces available space
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=100,  # Large offset
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pad = create_test_pad("test_pad", PadMapping.TOP, bondpad_width=60, cell_width=50)
    pad_list = [pad]

    bp_offset = set_pad_positions(pad_group, pad_list)

    # Usable space = 1000 - 2*100 = 800
    # Extra space = 800 - 60 = 740
    # Offset = 740/2 = 370
    assert bp_offset == pytest.approx(370.0)


# =============================================================================
# Manual Offset/Skip Override Tests
# =============================================================================


def create_test_pad_with_layout(
    name: str,
    mapping: PadMapping,
    bondpad_width: float,
    cell_width: float,
    layout_index: int = 0,
    manual_offset: float = None,
    manual_skip: float = None,
):
    """Helper to create a test pad with optional manual offset/skip."""
    bondpad_dim = Dimension(width=bondpad_width, length=None, name=f"{name}_BP")
    cell_dim = Dimension(width=cell_width, length=None, name=f"{name}_CELL")
    layout = Layout(
        bond_pad=bondpad_dim,
        cell_pad=cell_dim,
        offset=manual_offset,
        skip=manual_skip,
    )

    pad = SinglePad(
        name=name,
        layout_index=layout_index,
        type=PadType.INOUT,
        mapping=mapping,
        layout=layout,
        orient=Orientation.R0,
    )
    return pad


def test_manual_offset_on_first_pad_is_respected(sample_pad_group):
    """Test that manual offset on first pad is used instead of auto-calculated value."""
    # First, calculate what auto-calc would produce
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60], bp_spacing=25, edge_to_bp=20
    )
    auto_offset_value = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=60,
        pad_width=50,
    )
    # Manual: 450 - (50-20) + (60/2) - (50/2) = 425.0
    assert auto_offset_value == pytest.approx(425.0)

    # Set manual offset to something DIFFERENT from auto-calc
    manual_offset_value = 123.45
    assert manual_offset_value != auto_offset_value  # Ensure they're different!

    pad = create_test_pad_with_layout(
        "test_pad",
        PadMapping.TOP,
        bondpad_width=60,
        cell_width=50,
        manual_offset=manual_offset_value,
    )
    pad_list = [pad]

    bp_offset = set_pad_positions(sample_pad_group, pad_list)

    # Manual offset MUST be preserved, NOT auto-calculated value
    assert pad.layout.offset == pytest.approx(manual_offset_value)
    assert pad.layout.offset != pytest.approx(
        auto_offset_value
    )  # Verify override worked!
    # Should still return bondpad offset
    assert bp_offset is not None


def test_manual_skip_on_middle_pad_is_respected(sample_pad_group):
    """Test that manual skip on middle pad is used instead of auto-calculated value."""
    # First, calculate what auto-calc would produce
    auto_skip_value = calculate_expected_skip(
        last_bp_width=60, bp_width=60, bp_spacing=25, last_pad_width=50, pad_width=50
    )
    # Manual: (60+60)/2 + 25 - (50+50)/2 = 35.0
    assert auto_skip_value == pytest.approx(35.0)

    # Set manual skip to something DIFFERENT from auto-calc
    manual_skip_value = 100.0
    assert manual_skip_value != auto_skip_value  # Ensure they're different!

    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=manual_skip_value,
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # First pad should have auto-calculated offset
    assert pads[0].layout.offset is not None

    # Second pad MUST have manual skip, NOT the auto-calculated value
    assert pads[1].layout.skip == pytest.approx(manual_skip_value)
    assert pads[1].layout.skip != pytest.approx(
        auto_skip_value
    )  # Verify override worked!

    # Third pad should have auto-calculated skip
    assert pads[2].layout.skip is not None
    assert pads[2].layout.skip == pytest.approx(auto_skip_value)  # Should use auto


def test_manual_skip_maintains_positioning_chain(sample_pad_group):
    """Test that manual skip doesn't break auto-calculation for subsequent pads."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=150.0,  # Manual skip
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
        create_test_pad_with_layout(
            "pad_3", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=3
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # All pads should have their positioning values set
    assert pads[0].layout.offset is not None
    assert pads[1].layout.skip == pytest.approx(150.0)
    assert pads[2].layout.skip is not None
    assert pads[3].layout.skip is not None


def test_manual_offset_on_middle_pad_breaks_chain(sample_pad_group):
    """Test that manual offset on middle pad prevents auto-calculation for that pad."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_offset=500.0,  # Manual offset on middle pad
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # First pad should have auto-calculated offset
    assert pads[0].layout.offset is not None

    # Second pad has manual offset
    assert pads[1].layout.offset == pytest.approx(500.0)

    assert pads[2].layout.skip is not None


def test_all_manual_offsets_are_preserved(sample_pad_group):
    """Test that all pads can have manual offsets."""
    pads = [
        create_test_pad_with_layout(
            "pad_0",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=0,
            manual_offset=100.0,
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_offset=200.0,
        ),
        create_test_pad_with_layout(
            "pad_2",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=2,
            manual_offset=300.0,
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # All manual offsets should be preserved
    assert pads[0].layout.offset == pytest.approx(100.0)
    assert pads[1].layout.offset == pytest.approx(200.0)
    assert pads[2].layout.offset == pytest.approx(300.0)

    # Skip should not be set (only offset is manual)
    assert pads[0].layout.skip is None
    assert pads[1].layout.skip is None
    assert pads[2].layout.skip is None


def test_all_manual_skips_are_preserved(sample_pad_group):
    """Test that all pads can have manual skips."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=50.0,
        ),
        create_test_pad_with_layout(
            "pad_2",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=2,
            manual_skip=75.0,
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # First pad should have auto-calculated offset
    assert pads[0].layout.offset is not None

    # Manual skips should be preserved
    assert pads[1].layout.skip == pytest.approx(50.0)
    assert pads[2].layout.skip == pytest.approx(75.0)


def test_mixed_manual_auto_scenario(sample_pad_group):
    """Test realistic scenario with mix of manual and auto values."""
    pads = [
        create_test_pad_with_layout(
            "clk", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "rst",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=100.0,  # Extra spacing after reset
        ),
        create_test_pad_with_layout(
            "gpio_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
        create_test_pad_with_layout(
            "gpio_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=3,
            manual_skip=150.0,  # Extra spacing after gpio_1
        ),
        create_test_pad_with_layout(
            "gpio_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=4
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Check all values are set
    assert pads[0].layout.offset is not None  # Auto
    assert pads[1].layout.skip == pytest.approx(100.0)  # Manual
    assert pads[2].layout.skip is not None  # Auto
    assert pads[3].layout.skip == pytest.approx(150.0)  # Manual
    assert pads[4].layout.skip is not None  # Auto


def test_manual_offset_and_skip_on_same_pad(sample_pad_group):
    """Test pad with both manual offset and skip."""
    pads = [
        create_test_pad_with_layout(
            "pad_0",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=0,
            manual_offset=200.0,
            manual_skip=100.0,
        ),
        create_test_pad_with_layout(
            "pad_1", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=1
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Both manual values should be preserved
    assert pads[0].layout.offset == pytest.approx(200.0)
    assert pads[0].layout.skip == pytest.approx(100.0)

    # Second pad should NOT get auto skip (both are set on pad_0)
    # The condition: (pad.layout.skip is None) and (pad.layout.offset is None)
    # For pad_1: skip is None AND offset is None = True, so should get auto-calculated
    assert pads[1].layout.skip is not None


def test_manual_skip_zero_is_valid(sample_pad_group):
    """Test that manual skip of 0.0 is a valid value and is preserved."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=0.0,  # Zero spacing
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Zero skip should be preserved (not treated as None)
    assert pads[1].layout.skip == pytest.approx(0.0)


def test_manual_offset_zero_is_valid(sample_pad_group):
    """Test that manual offset of 0.0 is a valid value and is preserved."""
    pad = create_test_pad_with_layout(
        "pad_0",
        PadMapping.TOP,
        bondpad_width=60,
        cell_width=50,
        layout_index=0,
        manual_offset=0.0,  # Offset from edge
    )
    pad_list = [pad]

    set_pad_positions(sample_pad_group, pad_list)

    # Zero offset should be preserved (not treated as None)
    assert pad.layout.offset == pytest.approx(0.0)


def test_negative_manual_skip_is_preserved(sample_pad_group):
    """Test that negative manual skip values are preserved (though may be unusual)."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=-10.0,  # Negative spacing (overlap)
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Negative skip should be preserved (algorithm doesn't validate)
    assert pads[1].layout.skip == pytest.approx(-10.0)


def test_manual_values_with_variable_bondpad_widths(sample_pad_group):
    """Test manual skip works correctly with pads of different sizes."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=50, cell_width=40, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=70,
            cell_width=60,
            layout_index=1,
            manual_skip=200.0,  # Manual skip despite different sizes
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Manual skip should be preserved regardless of pad sizes
    assert pads[1].layout.skip == pytest.approx(200.0)

    # Auto values should still work
    assert pads[0].layout.offset is not None
    assert pads[2].layout.skip is not None


def test_manual_skip_preserves_chain_across_multiple_sides():
    """Test manual skip behavior on different edges of the die."""
    fp_dim = Dimension(width=1000, length=1500)
    pad_group = PadGroup(
        name="test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Test on different sides
    for mapping in [
        PadMapping.TOP,
        PadMapping.BOTTOM,
        PadMapping.LEFT,
        PadMapping.RIGHT,
    ]:
        pads = [
            create_test_pad_with_layout(
                "pad_0", mapping, bondpad_width=60, cell_width=50, layout_index=0
            ),
            create_test_pad_with_layout(
                "pad_1",
                mapping,
                bondpad_width=60,
                cell_width=50,
                layout_index=1,
                manual_skip=100.0,
            ),
            create_test_pad_with_layout(
                "pad_2", mapping, bondpad_width=60, cell_width=50, layout_index=2
            ),
        ]

        set_pad_positions(pad_group, pads)

        # Should work on all sides
        assert pads[0].layout.offset is not None
        assert pads[1].layout.skip == pytest.approx(100.0)
        assert pads[2].layout.skip is not None


# =============================================================================
# Comprehensive Calculation Verification Tests
# =============================================================================


def test_verify_auto_calculation_with_manual_skip_override(sample_pad_group):
    """Test that auto-calculated values are correct when mixed with manual skip."""
    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=60,
            cell_width=50,
            layout_index=1,
            manual_skip=100.0,  # Manual override
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=2
        ),
    ]

    set_pad_positions(sample_pad_group, pads)

    # Verify bondpad offset calculation
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60, 60, 60], bp_spacing=25, edge_to_bp=20
    )
    # Manual: bp_space = 60*3 + 25*2 = 230, extra = 1000 - 230 - 40 = 730, offset = 365
    assert expected_bp_offset == pytest.approx(365.0)

    # Verify first pad offset (auto-calculated)
    expected_first_offset = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=60,
        pad_width=50,
    )
    assert pads[0].layout.offset == pytest.approx(expected_first_offset)
    # Manual: 365 - (50-20) + (60/2) - (50/2) = 365 - 30 + 30 - 25 = 340
    assert pads[0].layout.offset == pytest.approx(340.0)

    # Second pad has manual skip
    assert pads[1].layout.skip == pytest.approx(100.0)

    # Third pad should have auto-calculated skip
    expected_skip = calculate_expected_skip(
        last_bp_width=60, bp_width=60, bp_spacing=25, last_pad_width=50, pad_width=50
    )
    assert pads[2].layout.skip == pytest.approx(expected_skip)
    assert pads[2].layout.skip == pytest.approx(35.0)


def test_calculation_formulas_comprehensive():
    """Comprehensive test of all calculation formulas with known values."""
    # Create custom pad group with specific values for testing
    fp_dim = Dimension(width=2000, length=1800)
    pad_group = PadGroup(
        name="calc_test",
        pad_edge_offset=100,
        bondpad_edge_offset=50,
        bp_spacing=30,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pads = [
        create_test_pad_with_layout(
            "pad_0", PadMapping.TOP, bondpad_width=80, cell_width=70, layout_index=0
        ),
        create_test_pad_with_layout(
            "pad_1", PadMapping.TOP, bondpad_width=90, cell_width=75, layout_index=1
        ),
        create_test_pad_with_layout(
            "pad_2", PadMapping.TOP, bondpad_width=85, cell_width=72, layout_index=2
        ),
    ]

    bp_offset = set_pad_positions(pad_group, pads)

    # Test bondpad offset calculation
    # bp_space = 80 + 90 + 85 + 30*2 = 315
    # extra_space = 2000 - 315 - 2*50 = 1585
    # bp_offset = 1585 / 2 = 792.5
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=2000, bp_widths=[80, 90, 85], bp_spacing=30, edge_to_bp=50
    )
    assert bp_offset == pytest.approx(expected_bp_offset)
    assert bp_offset == pytest.approx(792.5)

    # Test first pad offset calculation
    # offset = 792.5 - (100-50) + (80/2) - (70/2) = 792.5 - 50 + 40 - 35 = 747.5
    expected_pad0_offset = calculate_expected_pad_offset(
        bp_offset=792.5, edge_to_pad=100, edge_to_bp=50, bp_width=80, pad_width=70
    )
    assert pads[0].layout.offset == pytest.approx(expected_pad0_offset)
    assert pads[0].layout.offset == pytest.approx(747.5)

    # Test skip calculation for pad_1
    # skip = (80+90)/2 + 30 - (70+75)/2 = 85 + 30 - 72.5 = 42.5
    expected_pad1_skip = calculate_expected_skip(
        last_bp_width=80, bp_width=90, bp_spacing=30, last_pad_width=70, pad_width=75
    )
    assert pads[1].layout.skip == pytest.approx(expected_pad1_skip)
    assert pads[1].layout.skip == pytest.approx(42.5)

    # Test skip calculation for pad_2
    # skip = (90+85)/2 + 30 - (75+72)/2 = 87.5 + 30 - 73.5 = 44.0
    expected_pad2_skip = calculate_expected_skip(
        last_bp_width=90, bp_width=85, bp_spacing=30, last_pad_width=75, pad_width=72
    )
    assert pads[2].layout.skip == pytest.approx(expected_pad2_skip)
    assert pads[2].layout.skip == pytest.approx(44.0)


def test_calculation_with_fractional_values():
    """Test that calculations work correctly with fractional pad dimensions."""
    fp_dim = Dimension(width=1500, length=1500)
    pad_group = PadGroup(
        name="frac_test",
        pad_edge_offset=75.5,
        bondpad_edge_offset=30.25,
        bp_spacing=22.75,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    pads = [
        create_test_pad_with_layout(
            "pad_0",
            PadMapping.TOP,
            bondpad_width=55.5,
            cell_width=45.25,
            layout_index=0,
        ),
        create_test_pad_with_layout(
            "pad_1",
            PadMapping.TOP,
            bondpad_width=62.75,
            cell_width=52.5,
            layout_index=1,
        ),
    ]

    bp_offset = set_pad_positions(pad_group, pads)

    # Verify calculations work with fractional values
    expected_bp_offset = calculate_expected_bp_offset(
        side_length=1500,
        bp_widths=[55.5, 62.75],
        bp_spacing=22.75,
        edge_to_bp=30.25,
    )
    assert bp_offset == pytest.approx(expected_bp_offset)
    # bp_space = 55.5 + 62.75 + 22.75 = 141.0
    # extra = 1500 - 141.0 - 2*30.25 = 1298.5
    # offset = 1298.5 / 2 = 649.25
    assert bp_offset == pytest.approx(649.25)

    expected_pad_offset = calculate_expected_pad_offset(
        bp_offset=649.25,
        edge_to_pad=75.5,
        edge_to_bp=30.25,
        bp_width=55.5,
        pad_width=45.25,
    )
    assert pads[0].layout.offset == pytest.approx(expected_pad_offset)
    # offset = 649.25 - (75.5-30.25) + (55.5/2) - (45.25/2) = 649.25 - 45.25 + 27.75 - 22.625 = 609.125
    assert pads[0].layout.offset == pytest.approx(609.125)

    expected_skip = calculate_expected_skip(
        last_bp_width=55.5,
        bp_width=62.75,
        bp_spacing=22.75,
        last_pad_width=45.25,
        pad_width=52.5,
    )
    assert pads[1].layout.skip == pytest.approx(expected_skip)
    # skip = (55.5+62.75)/2 + 22.75 - (45.25+52.5)/2 = 59.125 + 22.75 - 48.875 = 33.0
    assert pads[1].layout.skip == pytest.approx(33.0)


# =============================================================================
# Per-Side Edge Offset Tests
# =============================================================================


def test_per_side_edge_offsets_override_global():
    """Test that per-side edge offsets override global values."""
    fp_dim = Dimension(width=1000, length=1500)
    pad_group = PadGroup(
        name="per_side_test",
        pad_edge_offset=50,  # Global default
        bondpad_edge_offset=20,  # Global default
        pad_edge_offsets={
            "top": 50,
            "bottom": 100,  # Override
            "left": 75,  # Override
            "right": 60,  # Override
        },
        bondpad_edge_offsets={
            "top": 20,
            "bottom": 40,  # Override
            "left": 30,  # Override
            "right": 25,  # Override
        },
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Test each side gets its specific offset
    assert pad_group.get_pad_edge_offset(PadMapping.TOP) == pytest.approx(50.0)
    assert pad_group.get_pad_edge_offset(PadMapping.BOTTOM) == pytest.approx(100.0)
    assert pad_group.get_pad_edge_offset(PadMapping.LEFT) == pytest.approx(75.0)
    assert pad_group.get_pad_edge_offset(PadMapping.RIGHT) == pytest.approx(60.0)

    assert pad_group.get_bondpad_edge_offset(PadMapping.TOP) == pytest.approx(20.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.BOTTOM) == pytest.approx(40.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.LEFT) == pytest.approx(30.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.RIGHT) == pytest.approx(25.0)


def test_per_side_edge_offsets_fallback_to_global():
    """Test that missing per-side offsets fall back to global values."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="fallback_test",
        pad_edge_offset=90,  # Global
        bondpad_edge_offset=20,  # Global
        pad_edge_offsets={
            "bottom": 100,  # Only override bottom
        },
        bondpad_edge_offsets={
            "bottom": 30,  # Only override bottom
        },
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Top, left, right should use global values
    assert pad_group.get_pad_edge_offset(PadMapping.TOP) == pytest.approx(90.0)
    assert pad_group.get_pad_edge_offset(PadMapping.LEFT) == pytest.approx(90.0)
    assert pad_group.get_pad_edge_offset(PadMapping.RIGHT) == pytest.approx(90.0)

    # Bottom should use override
    assert pad_group.get_pad_edge_offset(PadMapping.BOTTOM) == pytest.approx(100.0)

    assert pad_group.get_bondpad_edge_offset(PadMapping.TOP) == pytest.approx(20.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.LEFT) == pytest.approx(20.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.RIGHT) == pytest.approx(20.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.BOTTOM) == pytest.approx(30.0)


def test_per_side_edge_offsets_in_positioning():
    """Test that per-side offsets are used in actual pad positioning."""
    fp_dim = Dimension(width=1000, length=1500)
    pad_group = PadGroup(
        name="positioning_test",
        pad_edge_offset=50,  # Global
        bondpad_edge_offset=20,  # Global
        pad_edge_offsets={
            "top": 50,
            "bottom": 100,  # Different!
        },
        bondpad_edge_offsets={
            "top": 20,
            "bottom": 40,  # Different!
        },
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Create pads on TOP side
    top_pads = [
        create_test_pad_with_layout(
            "top_pad", PadMapping.TOP, bondpad_width=60, cell_width=50, layout_index=0
        )
    ]

    bp_offset_top = set_pad_positions(pad_group, top_pads)

    # Calculate expected with TOP's edge offsets (20, 50)
    expected_bp_offset_top = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60], bp_spacing=25, edge_to_bp=20
    )
    assert bp_offset_top == pytest.approx(expected_bp_offset_top)

    expected_pad_offset_top = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset_top,
        edge_to_pad=50,
        edge_to_bp=20,
        bp_width=60,
        pad_width=50,
    )
    assert top_pads[0].layout.offset == pytest.approx(expected_pad_offset_top)

    # Create pads on BOTTOM side
    bottom_pads = [
        create_test_pad_with_layout(
            "bot_pad",
            PadMapping.BOTTOM,
            bondpad_width=60,
            cell_width=50,
            layout_index=0,
        )
    ]

    bp_offset_bottom = set_pad_positions(pad_group, bottom_pads)

    # Calculate expected with BOTTOM's edge offsets (40, 100)
    expected_bp_offset_bottom = calculate_expected_bp_offset(
        side_length=1000, bp_widths=[60], bp_spacing=25, edge_to_bp=40  # Different!
    )
    assert bp_offset_bottom == pytest.approx(expected_bp_offset_bottom)

    expected_pad_offset_bottom = calculate_expected_pad_offset(
        bp_offset=expected_bp_offset_bottom,
        edge_to_pad=100,  # Different!
        edge_to_bp=40,  # Different!
        bp_width=60,
        pad_width=50,
    )
    assert bottom_pads[0].layout.offset == pytest.approx(expected_pad_offset_bottom)

    # The offsets should be different
    assert top_pads[0].layout.offset != bottom_pads[0].layout.offset


def test_per_side_different_calculations_per_side():
    """Test comprehensive scenario with different edge offsets on all sides."""
    fp_dim = Dimension(width=2000, length=1800)
    pad_group = PadGroup(
        name="comprehensive_per_side",
        pad_edge_offset=90,
        bondpad_edge_offset=20,
        pad_edge_offsets={
            "top": 90,
            "bottom": 110,
            "left": 95,
            "right": 85,
        },
        bondpad_edge_offsets={
            "top": 20,
            "bottom": 35,
            "left": 25,
            "right": 15,
        },
        bp_spacing=30,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Test all four sides
    sides_config = [
        (PadMapping.TOP, 2000, 20, 90),  # side, length, bp_offset, pad_offset
        (PadMapping.BOTTOM, 2000, 35, 110),
        (PadMapping.LEFT, 1800, 25, 95),
        (PadMapping.RIGHT, 1800, 15, 85),
    ]

    for side, side_length, expected_bp_edge, expected_pad_edge in sides_config:
        pads = [
            create_test_pad_with_layout(
                f"pad_{side.value}",
                side,
                bondpad_width=80,
                cell_width=70,
                layout_index=0,
            )
        ]

        bp_offset = set_pad_positions(pad_group, pads)

        # Verify correct edge offsets were used
        expected_bp_offset = calculate_expected_bp_offset(
            side_length=side_length,
            bp_widths=[80],
            bp_spacing=30,
            edge_to_bp=expected_bp_edge,
        )
        assert bp_offset == pytest.approx(expected_bp_offset)

        expected_pad_offset = calculate_expected_pad_offset(
            bp_offset=expected_bp_offset,
            edge_to_pad=expected_pad_edge,
            edge_to_bp=expected_bp_edge,
            bp_width=80,
            pad_width=70,
        )
        assert pads[0].layout.offset == pytest.approx(expected_pad_offset)


def test_per_side_with_string_keys():
    """Test that per-side offsets work with string keys (not just enums)."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="string_key_test",
        pad_edge_offset=50,
        bondpad_edge_offset=20,
        pad_edge_offsets={
            "top": 50,
            "bottom": 100,
        },
        bondpad_edge_offsets={
            "top": 20,
            "bottom": 40,
        },
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Test with string keys
    assert pad_group.get_pad_edge_offset("top") == pytest.approx(50.0)
    assert pad_group.get_pad_edge_offset("bottom") == pytest.approx(100.0)
    assert pad_group.get_bondpad_edge_offset("top") == pytest.approx(20.0)
    assert pad_group.get_bondpad_edge_offset("bottom") == pytest.approx(40.0)


def test_no_global_no_per_side_raises_error():
    """Test that missing both global and per-side offsets raises ValidationError."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="no_offset_test",
        pad_edge_offset=None,  # No global
        bondpad_edge_offset=None,  # No global
        pad_edge_offsets=None,  # No per-side
        bondpad_edge_offsets=None,  # No per-side
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Should raise ValidationError when trying to get offset
    with pytest.raises(ValidationError, match="no pad_edge_offset defined"):
        pad_group.get_pad_edge_offset(PadMapping.TOP)

    with pytest.raises(ValidationError, match="no bondpad_edge_offset defined"):
        pad_group.get_bondpad_edge_offset(PadMapping.TOP)


def test_per_side_only_no_global():
    """Test that per-side offsets work without global fallback."""
    fp_dim = Dimension(width=1000, length=1000)
    pad_group = PadGroup(
        name="per_side_only",
        pad_edge_offset=None,  # No global
        bondpad_edge_offset=None,  # No global
        pad_edge_offsets={
            "top": 90,
            "bottom": 100,
            "left": 95,
            "right": 85,
        },
        bondpad_edge_offsets={
            "top": 20,
            "bottom": 30,
            "left": 25,
            "right": 15,
        },
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # All sides should work without global fallback
    assert pad_group.get_pad_edge_offset(PadMapping.TOP) == pytest.approx(90.0)
    assert pad_group.get_pad_edge_offset(PadMapping.BOTTOM) == pytest.approx(100.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.LEFT) == pytest.approx(25.0)
    assert pad_group.get_bondpad_edge_offset(PadMapping.RIGHT) == pytest.approx(15.0)
