"""All edges populated - tests complete edge coverage.

Purpose: Test pad placement on all four edges simultaneously.
Features: Pads distributed across top, bottom, left, and right edges.
Use when: Validating complete edge population logic.
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
    """Create configuration with pads on all four edges."""

    # Standard floorplan
    fp_dim = Dimension(width=2000, length=2000)

    # Standard pad dimensions
    pad_dim = Dimension(width=48, length=None, name="EDGE_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="all_edges",
        pad_edge_offset=90,
        bondpad_edge_offset=25,
        bp_spacing=30,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Right edge: Clock, reset, UART
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

    # Top edge: SPI interface
    spi_sck = SinglePad(
        name="spi_sck",
        layout_index=4,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_sck)

    spi_mosi = SinglePad(
        name="spi_mosi",
        layout_index=5,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_mosi)

    spi_miso = SinglePad(
        name="spi_miso",
        layout_index=6,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_miso)

    spi_cs = SinglePad(
        name="spi_cs",
        layout_index=7,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_cs)

    # Left edge: GPIO bank
    gpio_range = RangePad(
        name="gpio",
        layout_index=8,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        num=8,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(gpio_range)

    # Bottom edge: I2C + PWM
    i2c_scl = SinglePad(
        name="i2c_scl",
        layout_index=9,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(i2c_scl)

    i2c_sda = SinglePad(
        name="i2c_sda",
        layout_index=10,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(i2c_sda)

    pwm_0 = SinglePad(
        name="pwm_0",
        layout_index=11,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_0)

    pwm_1 = SinglePad(
        name="pwm_1",
        layout_index=12,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_1)

    return PadRing(pad_group)
