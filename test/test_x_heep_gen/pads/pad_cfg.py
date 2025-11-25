from x_heep_gen.pads.PadDef import (
    SinglePad,
    MultiplexedPad,
    RangePad,
    PadDef,
    PadGroup,
    Dimension,
    Layout,
)
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping

# define all the layouts
pad1_layout = Layout("1", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))
pad2_layout = Layout("2", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))
pad3_layout = Layout("3", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))
pad4_layout = Layout("4", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))

# define all the pads
clk = SinglePad("clk", "input", mapping=PadMapping("right"), layout=pad1_layout)

# define PadGroup
pad_group = PadGroup(name="test", edge_to_bp=20, edge_to_pad=90, bp_spacing=25, fp_dim=Dimension(400, 400))

# add the pads into the padGroup
pad_group.add_pad(clk)


def config() -> PadRing:
    print("Creating PadRing configuration...")
    print("type of pad_group before creating PadRing:", type(pad_group))
    pad_ring = PadRing(pad_group)
    return pad_ring
