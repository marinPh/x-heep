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


def test_single_pad_is_centered(sample_pad_group):
    """Test that a single pad is centered on the side."""
    # Floorplan is 1000x1000, bondpad edge offset is 20
    # Expected usable space: 1000 - 2*20 = 960
    # Bondpad is 60 wide
    # Extra space = 960 - 60 = 900
    # Offset should be 900/2 = 450

    pad = create_test_pad("test_pad", PadMapping.TOP, bondpad_width=60, cell_width=50)
    pad_list = [pad]

    bp_offset = set_pad_positions(sample_pad_group, pad_list)

    # Bondpad should be centered
    assert bp_offset == pytest.approx(450.0)
    # Pad layout offset should be calculated
    assert pad.layout.offset is not None


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

    assert bp_offset == pytest.approx(365.0)

    # First pad should have offset set
    assert pads[0].layout.offset is not None

    # Second and third pads should have skip set
    assert pads[1].layout.skip is not None
    assert pads[2].layout.skip is not None


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

    assert bp_offset == pytest.approx(365.0)

    # All pads should have their layout parameters set
    assert pads[0].layout.offset is not None
    assert pads[1].layout.skip is not None
    assert pads[2].layout.skip is not None


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
