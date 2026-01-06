"""Ultra minimal pad configuration - absolute minimum for functionality.

Purpose: Test the absolute minimum viable pad configuration.
Features: Only clock and reset inputs.
Use when: Validating basic pad generation without complexity.
"""

from x_heep_gen.pads.PadDef import SinglePad, PadGroup, Dimension, Layout, PadType
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """Create ultra minimal pad configuration with only clk and rst."""

    # Minimal floorplan
    fp_dim = Dimension(width=800, length=800)

    # Single pad type for everything
    pad_dim = Dimension(width=30, length=None, name="MINIMAL_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="ultra_minimal",
        pad_edge_offset=40,
        bondpad_edge_offset=15,
        bp_spacing=20,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Clock input
    clk = SinglePad(
        name="clk",
        layout_index=0,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(clk)

    # Reset input (active low)
    rst = SinglePad(
        name="rst",
        layout_index=1,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
        active="low",
    )
    pad_group.add_pad(rst)

    return PadRing(pad_group)
