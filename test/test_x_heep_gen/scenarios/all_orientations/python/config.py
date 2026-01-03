"""All pad orientations test - r0, r90, mx, mx90.

Purpose: Test all possible pad orientations on all edges.
Features: 2 pads of each orientation (r0, r90, mx, mx90).
Use when: Validating orientation transformation logic.
"""

from x_heep_gen.pads.PadDef import SinglePad, PadGroup, Dimension, Layout, PadType
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """Create configuration testing all pad orientations."""

    # Standard floorplan
    fp_dim = Dimension(width=1400, length=1400)

    # Standard pad dimensions
    pad_dim = Dimension(width=45, length=None, name="ORIENT_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="all_orientations",
        pad_edge_offset=70,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Clock and reset on right edge (r90)
    clk = SinglePad(
        name="clk",
        layout_index=0,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(clk)

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

    # r0 orientation (0 degrees) - on top edge
    pad_r0_0 = SinglePad(
        name="pad_r0_0",
        layout_index=2,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(pad_r0_0)

    pad_r0_1 = SinglePad(
        name="pad_r0_1",
        layout_index=3,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(pad_r0_1)

    # r90 orientation (90 degrees) - on right edge
    pad_r90_0 = SinglePad(
        name="pad_r90_0",
        layout_index=4,
        type=PadType.INOUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(pad_r90_0)

    pad_r90_1 = SinglePad(
        name="pad_r90_1",
        layout_index=5,
        type=PadType.INOUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(pad_r90_1)

    # mx orientation (mirrored X) - on bottom edge
    pad_mx_0 = SinglePad(
        name="pad_mx_0",
        layout_index=6,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pad_mx_0)

    pad_mx_1 = SinglePad(
        name="pad_mx_1",
        layout_index=7,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pad_mx_1)

    # mx90 orientation (mirrored X + 90 degrees) - on left edge
    pad_mx90_0 = SinglePad(
        name="pad_mx90_0",
        layout_index=8,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(pad_mx90_0)

    pad_mx90_1 = SinglePad(
        name="pad_mx90_1",
        layout_index=9,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(pad_mx90_1)

    return PadRing(pad_group)
