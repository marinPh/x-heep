from x_heep_gen.xheep.pads.PadDef import (
    SinglePad,
    MuxPad,
    RangePad,
    PadConfig,
    PadGroup,
    Dimension,
    Layout,
)
from x_heep_gen.xheep.pads.PadRing import PadRing

pad1_layout = Layout("1", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))

pad2_layout = Layout("2", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))

pad3_layout = Layout("1", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))

pad4_layout = Layout("1", bond_pad=Dimension(50, 50), cell_pad=Dimension(40, 40))
pad_group = PadGroup(name="test", edge_to_bp=20, edge_to_pad=90, bp_spacing=25)

clk = SinglePad("clk", "input", mapping="right", layout=pad1_layout)
pad_group.add_pad(clk)


def config() -> PadRing:
    pad_ring = PadRing(pad_group)
    return pad_ring
