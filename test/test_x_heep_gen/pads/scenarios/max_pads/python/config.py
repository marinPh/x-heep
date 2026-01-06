"""Maximum pad count stress test.

Purpose: Test system with maximum realistic pad count.
Features: 32 GPIOs + full peripheral set (JTAG, UART, SPI, I2C, PWM).
Use when: Validating high pad count placement algorithms.
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
    """Create maximum pad count configuration."""

    # Large floorplan for many pads
    fp_dim = Dimension(width=3000, length=3000)

    # Standard pad dimensions
    pad_dim = Dimension(width=50, length=None, name="MAX_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="max_pads",
        pad_edge_offset=150,
        bondpad_edge_offset=35,
        bp_spacing=40,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Clock and reset on right edge
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

    # 32 GPIO pads on left edge
    gpio_range = RangePad(
        name="gpio",
        layout_index=2,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        num=32,
        orient=Orientation.MX90,
    )
    pad_group.add_pad(gpio_range)

    # Additional peripherals on top edge
    uart_rx = SinglePad(
        name="uart_rx",
        layout_index=3,
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_rx)

    uart_tx = SinglePad(
        name="uart_tx",
        layout_index=4,
        type=PadType.OUTPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(uart_tx)

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

    spi_miso = SinglePad(
        name="spi_miso",
        layout_index=7,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_miso)

    spi_cs = SinglePad(
        name="spi_cs",
        layout_index=8,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(spi_cs)

    i2c_scl = SinglePad(
        name="i2c_scl",
        layout_index=9,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(i2c_scl)

    i2c_sda = SinglePad(
        name="i2c_sda",
        layout_index=10,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )
    pad_group.add_pad(i2c_sda)

    # JTAG on bottom edge
    jtag_tck = SinglePad(
        name="jtag_tck",
        layout_index=11,
        type=PadType.INPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(jtag_tck)

    jtag_tms = SinglePad(
        name="jtag_tms",
        layout_index=12,
        type=PadType.INPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(jtag_tms)

    jtag_tdi = SinglePad(
        name="jtag_tdi",
        layout_index=13,
        type=PadType.INPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(jtag_tdi)

    jtag_tdo = SinglePad(
        name="jtag_tdo",
        layout_index=14,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(jtag_tdo)

    jtag_trst = SinglePad(
        name="jtag_trst",
        layout_index=15,
        type=PadType.INPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
        active="low",
    )
    pad_group.add_pad(jtag_trst)

    # PWM outputs
    pwm_0 = SinglePad(
        name="pwm_0",
        layout_index=16,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_0)

    pwm_1 = SinglePad(
        name="pwm_1",
        layout_index=17,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_1)

    pwm_2 = SinglePad(
        name="pwm_2",
        layout_index=18,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_2)

    pwm_3 = SinglePad(
        name="pwm_3",
        layout_index=19,
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )
    pad_group.add_pad(pwm_3)

    return PadRing(pad_group)
