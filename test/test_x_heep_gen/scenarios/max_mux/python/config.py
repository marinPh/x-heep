"""Maximum multiplexing test - every pad has mux options.

Purpose: Test complex multiplexing with 3-4 alternatives per pad.
Features: 6 multiplexed pads with multiple signal options each.
Use when: Validating multiplexing logic and mux selection.
"""

from x_heep_gen.pads.PadDef import (
    SinglePad,
    MultiplexedPad,
    PadGroup,
    Dimension,
    Layout,
    PadType,
)
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping, Orientation


def config() -> PadRing:
    """Create maximum multiplexing configuration."""

    # Standard floorplan
    fp_dim = Dimension(width=1500, length=1500)

    # MUX pad dimensions
    pad_dim = Dimension(width=55, length=None, name="MUX_PAD")
    layout = Layout(bond_pad=pad_dim, cell_pad=pad_dim)

    # Create pad group
    pad_group = PadGroup(
        name="max_mux",
        pad_edge_offset=80,
        bondpad_edge_offset=20,
        bp_spacing=25,
        cell_spacing=None,
        fp_dim=fp_dim,
    )

    # Clock and reset (non-multiplexed)
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

    # Multiplexed pad 0: uart_rx / spi_miso / gpio_0
    alt_uart_rx = SinglePad(
        name="uart_rx",
        type=PadType.INPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    alt_spi_miso_0 = SinglePad(
        name="spi_miso",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    alt_gpio_0 = SinglePad(
        name="gpio_0",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    mux_pad_0 = MultiplexedPad(
        name="mux_pad_0",
        layout_index=2,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
        alts=[
            ("uart_rx", alt_uart_rx),
            ("spi_miso", alt_spi_miso_0),
            ("gpio_0", alt_gpio_0),
        ],
    )
    pad_group.add_pad(mux_pad_0)

    # Multiplexed pad 1: uart_tx / spi_mosi / gpio_1
    alt_uart_tx = SinglePad(
        name="uart_tx",
        type=PadType.OUTPUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    alt_spi_mosi_1 = SinglePad(
        name="spi_mosi",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    alt_gpio_1 = SinglePad(
        name="gpio_1",
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
    )

    mux_pad_1 = MultiplexedPad(
        name="mux_pad_1",
        layout_index=3,
        type=PadType.INOUT,
        mapping=PadMapping.TOP,
        layout=layout,
        orient=Orientation.R0,
        alts=[
            ("uart_tx", alt_uart_tx),
            ("spi_mosi", alt_spi_mosi_1),
            ("gpio_1", alt_gpio_1),
        ],
    )
    pad_group.add_pad(mux_pad_1)

    # Multiplexed pad 2: i2c_scl / spi_sck / gpio_2 / pwm_0
    alt_i2c_scl_2 = SinglePad(
        name="i2c_scl",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_spi_sck_2 = SinglePad(
        name="spi_sck",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_gpio_2 = SinglePad(
        name="gpio_2",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_pwm_0 = SinglePad(
        name="pwm_0",
        type=PadType.OUTPUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    mux_pad_2 = MultiplexedPad(
        name="mux_pad_2",
        layout_index=4,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
        alts=[
            ("i2c_scl", alt_i2c_scl_2),
            ("spi_sck", alt_spi_sck_2),
            ("gpio_2", alt_gpio_2),
            ("pwm_0", alt_pwm_0),
        ],
    )
    pad_group.add_pad(mux_pad_2)

    # Multiplexed pad 3: i2c_sda / spi_cs / gpio_3 / pwm_1
    alt_i2c_sda_3 = SinglePad(
        name="i2c_sda",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_spi_cs_3 = SinglePad(
        name="spi_cs",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_gpio_3 = SinglePad(
        name="gpio_3",
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    alt_pwm_1 = SinglePad(
        name="pwm_1",
        type=PadType.OUTPUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
    )

    mux_pad_3 = MultiplexedPad(
        name="mux_pad_3",
        layout_index=5,
        type=PadType.INOUT,
        mapping=PadMapping.LEFT,
        layout=layout,
        orient=Orientation.MX90,
        alts=[
            ("i2c_sda", alt_i2c_sda_3),
            ("spi_cs", alt_spi_cs_3),
            ("gpio_3", alt_gpio_3),
            ("pwm_1", alt_pwm_1),
        ],
    )
    pad_group.add_pad(mux_pad_3)

    # Multiplexed pad 4: pdm_clk / gpio_4 / pwm_2
    alt_pdm_clk_4 = SinglePad(
        name="pdm_clk",
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    alt_gpio_4 = SinglePad(
        name="gpio_4",
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    alt_pwm_2 = SinglePad(
        name="pwm_2",
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    mux_pad_4 = MultiplexedPad(
        name="mux_pad_4",
        layout_index=6,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
        alts=[
            ("pdm_clk", alt_pdm_clk_4),
            ("gpio_4", alt_gpio_4),
            ("pwm_2", alt_pwm_2),
        ],
    )
    pad_group.add_pad(mux_pad_4)

    # Multiplexed pad 5: pdm_data / gpio_5 / pwm_3
    alt_pdm_data_5 = SinglePad(
        name="pdm_data",
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    alt_gpio_5 = SinglePad(
        name="gpio_5",
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    alt_pwm_3 = SinglePad(
        name="pwm_3",
        type=PadType.OUTPUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
    )

    mux_pad_5 = MultiplexedPad(
        name="mux_pad_5",
        layout_index=7,
        type=PadType.INOUT,
        mapping=PadMapping.BOTTOM,
        layout=layout,
        orient=Orientation.MX,
        alts=[
            ("pdm_data", alt_pdm_data_5),
            ("gpio_5", alt_gpio_5),
            ("pwm_3", alt_pwm_3),
        ],
    )
    pad_group.add_pad(mux_pad_5)

    return PadRing(pad_group)
