"""Tight spacing edge case - minimum allowable spacing.

Purpose: Test minimum spacing constraints for bondpad placement.
Features: Small pads (35um) with minimum spacing (15um) on all edges.
Use when: Validating spacing calculation edge cases.
"""

from x_heep_gen.pads.PadDef import (
    SinglePad,
    RangePad,
    PadGroup,
    Dimension,
    Layout,
    PadType,
)
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """Create tight spacing configuration with minimum allowable spacing."""

    # Compact floorplan
    fp_dim = Dimension(width=1200, length=1200)

    # Tight pad dimensions
    pad_dim = Dimension(width=35, length=None, name="TIGHT_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group with minimum spacing
    pad_group = PadGroup(
        name="tight_spacing",
        pad_edge_offset=50,
        bondpad_edge_offset=10,
        bp_spacing=15,  # Minimum spacing
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

    # UART interface
    uart_rx = SinglePad(
        name="uart_rx",
        layout_index=2,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(uart_rx)

    uart_tx = SinglePad(
        name="uart_tx",
        layout_index=3,
        type=PadType.OUTPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(uart_tx)

    # GPIO bank (12 pads) - tight spacing test
    gpio_range = RangePad(
        name="gpio",
        layout_index=4,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        num=12,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(gpio_range)

    # SPI interface on top edge
    spi_sck = SinglePad(
        name="spi_sck",
        layout_index=5,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_sck)

    spi_mosi = SinglePad(
        name="spi_mosi",
        layout_index=6,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_mosi)

    # SPI interface on bottom edge
    spi_miso = SinglePad(
        name="spi_miso",
        layout_index=7,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_miso)

    spi_cs = SinglePad(
        name="spi_cs",
        layout_index=8,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_cs)

    return PadRing(pad_group)
