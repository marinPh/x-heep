"""Standard ASIC configuration with common peripherals.

Purpose: Representative production ASIC pad configuration.
Features: Full JTAG, UART, 16 GPIOs, I2C, SPI - typical ASIC peripherals.
Use when: Testing standard ASIC tape-out configurations.
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
    """Create standard ASIC pad configuration."""

    # Standard ASIC floorplan
    fp_dim = Dimension(width=2500, length=2500)

    # Standard ASIC pad dimensions
    pad_dim = Dimension(width=60, length=None, name="ASIC_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="asic_standard",
        pad_edge_offset=100,
        bondpad_edge_offset=30,
        bp_spacing=35,
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

    # JTAG interface
    jtag_tck = SinglePad(
        name="jtag_tck",
        layout_index=2,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(jtag_tck)

    jtag_tms = SinglePad(
        name="jtag_tms",
        layout_index=3,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(jtag_tms)

    jtag_tdi = SinglePad(
        name="jtag_tdi",
        layout_index=4,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(jtag_tdi)

    jtag_tdo = SinglePad(
        name="jtag_tdo",
        layout_index=5,
        type=PadType.OUTPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
    )
    pad_group.add_pad(jtag_tdo)

    jtag_trst = SinglePad(
        name="jtag_trst",
        layout_index=6,
        type=PadType.INPUT,
        mapping=PadMapping.RIGHT,
        layout=layout,
        orient=Orientation.R90,
        active="low",
    )
    pad_group.add_pad(jtag_trst)

    # UART interface
    uart_rx = SinglePad(
        name="uart_rx",
        layout_index=7,
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_rx)

    uart_tx = SinglePad(
        name="uart_tx",
        layout_index=8,
        type=PadType.OUTPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_tx)

    # GPIO bank (16 pads)
    gpio_range = RangePad(
        name="gpio",
        layout_index=9,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        num=16,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(gpio_range)

    # I2C interface
    i2c_scl = SinglePad(
        name="i2c_scl",
        layout_index=10,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(i2c_scl)

    i2c_sda = SinglePad(
        name="i2c_sda",
        layout_index=11,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(i2c_sda)

    # SPI interface
    spi_sck = SinglePad(
        name="spi_sck",
        layout_index=12,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_sck)

    spi_mosi = SinglePad(
        name="spi_mosi",
        layout_index=13,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_mosi)

    spi_miso = SinglePad(
        name="spi_miso",
        layout_index=14,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_miso)

    spi_cs = SinglePad(
        name="spi_cs",
        layout_index=15,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(spi_cs)

    return PadRing(pad_group)
