"""Minimal pad configuration example - demonstrates simplest possible setup."""

from x_heep_gen.pads.PadDef import (
    SinglePad,
    PadGroup,
    Dimension,
    Layout,
    PadType,
)
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """
    Create a minimal pad configuration with only essential pads.

    This demonstrates the simplest possible X-HEEP pad setup:
    - Clock and reset inputs
    - UART RX/TX for communication
    - Minimal floorplan (1000x1000)
    - Single pad and bondpad type
    """
    # Floorplan dimensions
    fp_dim = Dimension(width=1000, length=1000)

    # Single pad/bondpad type for simplicity
    bondpad_dim = Dimension(width=40, length=None, name="BONDPAD_DEFAULT")
    pad_dim = Dimension(width=30, length=None, name="PAD_DEFAULT")
    default_layout = Layout(bond_pad=bondpad_dim, cell_pad=pad_dim)

    # Create pad group with physical attributes
    pad_group = PadGroup(
        name="x_heep_minimal",
        pad_edge_offset=50,
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
        layout=default_layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(clk)

    # Reset input (active low)
    rst = SinglePad(
        name="rst",
        layout_index=1,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=default_layout,
        orient=Orientation.R90,
        active="low",
    )
    pad_group.add_pad(rst)

    # UART RX input
    uart_rx = SinglePad(
        name="uart_rx",
        layout_index=2,
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=default_layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_rx)

    # UART TX output
    uart_tx = SinglePad(
        name="uart_tx",
        layout_index=3,
        type=PadType.OUTPUT,
        mapping=PadMapping.TOP,
        layout=default_layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_tx)

    # Wrap in PadRing
    pad_ring = PadRing(pad_group)
    return pad_ring
