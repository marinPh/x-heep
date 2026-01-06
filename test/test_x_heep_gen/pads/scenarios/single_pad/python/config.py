"""Single pad edge case - absolute minimum configuration.

Purpose: Test the absolute minimum pad configuration (only clock).
Features: Single clock pad on right edge.
Use when: Testing edge cases with minimal pad count.
"""

from x_heep_gen.pads.PadDef import SinglePad, PadGroup, Dimension, Layout, PadType
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """Create single pad configuration with only clock."""

    # Minimal floorplan
    fp_dim = Dimension(width=500, length=500)

    # Single pad type
    pad_dim = Dimension(width=25, length=None, name="SINGLE_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="single_pad",
        pad_edge_offset=30,
        bondpad_edge_offset=10,
        bp_spacing=15,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Clock input (only pad)
    clk = SinglePad(
        name="clk",
        layout_index=0,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(clk)

    return PadRing(pad_group)
