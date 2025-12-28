# Copyright 2025 EPFL.
# Solderpad Hardware License, Version 0.51, see LICENSE for details.
# SPDX-License-Identifier: SHL-0.51
#
# Pad configuration for core-v-mini-mcu. Python version of pad_cfg.hjson.
#
# For detailed documentation and usage instructions, please refer to docs/source/Configuration/PadConfiguration.md

from x_heep_gen.pads.PadDef import (
    SinglePad,
    MultiplexedPad,
    RangePad,
    PadGroup,
    PadType,
)
from x_heep_gen.pads.PadRing import PadRing


def config() -> PadRing:
    """
    Returns the pad configuration as a PadRing object.
    This is the Python class-based equivalent of configs/pad_cfg.hjson.

    Note: This version contains only logical pad definitions as done in the hjson.
    Physical layout attributes (mapping, orient, layout_index, dimensions) are not included.
    """

    # Create pad group
    pad_group = PadGroup(name="x_heep_system")

    # -------------------------------------------------------------------------
    # Single input pads
    # -------------------------------------------------------------------------

    clk = SinglePad(
        name="clk",
        type=PadType.INPUT,
    )
    pad_group.add_pad(clk)

    rst = SinglePad(
        name="rst",
        type=PadType.INPUT,
        active="low",
        driven_manually=True,
    )
    pad_group.add_pad(rst)

    boot_select = SinglePad(
        name="boot_select",
        type=PadType.INPUT,
    )
    pad_group.add_pad(boot_select)

    execute_from_flash = SinglePad(
        name="execute_from_flash",
        type=PadType.INPUT,
    )
    pad_group.add_pad(execute_from_flash)

    jtag_tck = SinglePad(
        name="jtag_tck",
        type=PadType.INPUT,
    )
    pad_group.add_pad(jtag_tck)

    jtag_tms = SinglePad(
        name="jtag_tms",
        type=PadType.INPUT,
    )
    pad_group.add_pad(jtag_tms)

    jtag_trst = SinglePad(
        name="jtag_trst",
        type=PadType.INPUT,
        active="low",
    )
    pad_group.add_pad(jtag_trst)

    jtag_tdi = SinglePad(
        name="jtag_tdi",
        type=PadType.INPUT,
    )
    pad_group.add_pad(jtag_tdi)

    uart_rx = SinglePad(
        name="uart_rx",
        type=PadType.INPUT,
    )
    pad_group.add_pad(uart_rx)

    # -------------------------------------------------------------------------
    # Single output pads
    # -------------------------------------------------------------------------

    jtag_tdo = SinglePad(
        name="jtag_tdo",
        type=PadType.OUTPUT,
    )
    pad_group.add_pad(jtag_tdo)

    uart_tx = SinglePad(
        name="uart_tx",
        type=PadType.OUTPUT,
    )
    pad_group.add_pad(uart_tx)

    exit_valid = SinglePad(
        name="exit_valid",
        type=PadType.OUTPUT,
    )
    pad_group.add_pad(exit_valid)

    # -------------------------------------------------------------------------
    # Range pad for gpio (num: 14, offset: 0 -> gpio_0 .. gpio_13)
    # -------------------------------------------------------------------------

    gpio_range = RangePad(
        name="gpio",
        type=PadType.INOUT,
        num=14,
        offset=0,
    )
    pad_group.add_pad(gpio_range)

    # -------------------------------------------------------------------------
    # Single inout pads (no mux)
    # -------------------------------------------------------------------------

    spi_flash_sck = SinglePad(
        name="spi_flash_sck",
        type=PadType.INOUT,
    )
    pad_group.add_pad(spi_flash_sck)

    # -------------------------------------------------------------------------
    # Range pads for multi-signal interfaces
    # -------------------------------------------------------------------------

    spi_flash_cs = RangePad(
        name="spi_flash_cs",
        type=PadType.INOUT,
        num=2,
    )
    pad_group.add_pad(spi_flash_cs)

    spi_flash_sd = RangePad(
        name="spi_flash_sd",
        type=PadType.INOUT,
        num=4,
    )
    pad_group.add_pad(spi_flash_sd)

    spi_sck = SinglePad(
        name="spi_sck",
        type=PadType.INOUT,
    )
    pad_group.add_pad(spi_sck)

    spi_cs = RangePad(
        name="spi_cs",
        type=PadType.INOUT,
        num=2,
    )
    pad_group.add_pad(spi_cs)

    spi_sd = RangePad(
        name="spi_sd",
        type=PadType.INOUT,
        num=4,
    )
    pad_group.add_pad(spi_sd)

    # -------------------------------------------------------------------------
    # Multiplexed pads (with mux definitions)
    # -------------------------------------------------------------------------

    # spi_slave_sck: mux with gpio_14
    alt_spi_slave_sck = SinglePad(
        name="spi_slave_sck",
        type=PadType.INPUT,
    )
    alt_gpio_14 = SinglePad(
        name="gpio_14",
        type=PadType.INOUT,
    )
    spi_slave_sck = MultiplexedPad(
        name="spi_slave_sck",
        type=PadType.INOUT,
        alts=[("spi_slave_sck", alt_spi_slave_sck), ("gpio_14", alt_gpio_14)],
    )
    pad_group.add_pad(spi_slave_sck)

    # spi_slave_cs: mux with gpio_15
    alt_spi_slave_cs = SinglePad(
        name="spi_slave_cs",
        type=PadType.INPUT,
    )
    alt_gpio_15 = SinglePad(
        name="gpio_15",
        type=PadType.INOUT,
    )
    spi_slave_cs = MultiplexedPad(
        name="spi_slave_cs",
        type=PadType.INOUT,
        alts=[("spi_slave_cs", alt_spi_slave_cs), ("gpio_15", alt_gpio_15)],
    )
    pad_group.add_pad(spi_slave_cs)

    # spi_slave_miso: mux with gpio_16
    alt_spi_slave_miso = SinglePad(
        name="spi_slave_miso",
        type=PadType.INOUT,
    )
    alt_gpio_16 = SinglePad(
        name="gpio_16",
        type=PadType.INOUT,
    )
    spi_slave_miso = MultiplexedPad(
        name="spi_slave_miso",
        type=PadType.INOUT,
        alts=[("spi_slave_miso", alt_spi_slave_miso), ("gpio_16", alt_gpio_16)],
    )
    pad_group.add_pad(spi_slave_miso)

    # spi_slave_mosi: mux with gpio_17
    alt_spi_slave_mosi = SinglePad(
        name="spi_slave_mosi",
        type=PadType.INPUT,
    )
    alt_gpio_17 = SinglePad(
        name="gpio_17",
        type=PadType.INOUT,
    )
    spi_slave_mosi = MultiplexedPad(
        name="spi_slave_mosi",
        type=PadType.INOUT,
        alts=[("spi_slave_mosi", alt_spi_slave_mosi), ("gpio_17", alt_gpio_17)],
    )
    pad_group.add_pad(spi_slave_mosi)

    # pdm2pcm_pdm: mux with gpio_18
    alt_pdm2pcm_pdm = SinglePad(
        name="pdm2pcm_pdm",
        type=PadType.INOUT,
    )
    alt_gpio_18 = SinglePad(
        name="gpio_18",
        type=PadType.INOUT,
    )
    pdm2pcm_pdm = MultiplexedPad(
        name="pdm2pcm_pdm",
        type=PadType.INOUT,
        alts=[("pdm2pcm_pdm", alt_pdm2pcm_pdm), ("gpio_18", alt_gpio_18)],
    )
    pad_group.add_pad(pdm2pcm_pdm)

    # pdm2pcm_clk: mux with gpio_19
    alt_pdm2pcm_clk = SinglePad(
        name="pdm2pcm_clk",
        type=PadType.INOUT,
    )
    alt_gpio_19 = SinglePad(
        name="gpio_19",
        type=PadType.INOUT,
    )
    pdm2pcm_clk = MultiplexedPad(
        name="pdm2pcm_clk",
        type=PadType.INOUT,
        alts=[("pdm2pcm_clk", alt_pdm2pcm_clk), ("gpio_19", alt_gpio_19)],
    )
    pad_group.add_pad(pdm2pcm_clk)

    # i2s_sck: mux with gpio_20
    alt_i2s_sck = SinglePad(
        name="i2s_sck",
        type=PadType.INOUT,
    )
    alt_gpio_20 = SinglePad(
        name="gpio_20",
        type=PadType.INOUT,
    )
    i2s_sck = MultiplexedPad(
        name="i2s_sck",
        type=PadType.INOUT,
        alts=[("i2s_sck", alt_i2s_sck), ("gpio_20", alt_gpio_20)],
    )
    pad_group.add_pad(i2s_sck)

    # i2s_ws: mux with gpio_21
    alt_i2s_ws = SinglePad(
        name="i2s_ws",
        type=PadType.INOUT,
    )
    alt_gpio_21 = SinglePad(
        name="gpio_21",
        type=PadType.INOUT,
    )
    i2s_ws = MultiplexedPad(
        name="i2s_ws",
        type=PadType.INOUT,
        alts=[("i2s_ws", alt_i2s_ws), ("gpio_21", alt_gpio_21)],
    )
    pad_group.add_pad(i2s_ws)

    # i2s_sd: mux with gpio_22
    alt_i2s_sd = SinglePad(
        name="i2s_sd",
        type=PadType.INOUT,
    )
    alt_gpio_22 = SinglePad(
        name="gpio_22",
        type=PadType.INOUT,
    )
    i2s_sd = MultiplexedPad(
        name="i2s_sd",
        type=PadType.INOUT,
        alts=[("i2s_sd", alt_i2s_sd), ("gpio_22", alt_gpio_22)],
    )
    pad_group.add_pad(i2s_sd)

    # spi2_cs_0: mux with gpio_23
    alt_spi2_cs_0 = SinglePad(
        name="spi2_cs_0",
        type=PadType.INOUT,
    )
    alt_gpio_23 = SinglePad(
        name="gpio_23",
        type=PadType.INOUT,
    )
    spi2_cs_0 = MultiplexedPad(
        name="spi2_cs_0",
        type=PadType.INOUT,
        alts=[("spi2_cs_0", alt_spi2_cs_0), ("gpio_23", alt_gpio_23)],
    )
    pad_group.add_pad(spi2_cs_0)

    # spi2_cs_1: mux with gpio_24
    alt_spi2_cs_1 = SinglePad(
        name="spi2_cs_1",
        type=PadType.INOUT,
    )
    alt_gpio_24 = SinglePad(
        name="gpio_24",
        type=PadType.INOUT,
    )
    spi2_cs_1 = MultiplexedPad(
        name="spi2_cs_1",
        type=PadType.INOUT,
        alts=[("spi2_cs_1", alt_spi2_cs_1), ("gpio_24", alt_gpio_24)],
    )
    pad_group.add_pad(spi2_cs_1)

    # spi2_sck: mux with gpio_25
    alt_spi2_sck = SinglePad(
        name="spi2_sck",
        type=PadType.INOUT,
    )
    alt_gpio_25 = SinglePad(
        name="gpio_25",
        type=PadType.INOUT,
    )
    spi2_sck = MultiplexedPad(
        name="spi2_sck",
        type=PadType.INOUT,
        alts=[("spi2_sck", alt_spi2_sck), ("gpio_25", alt_gpio_25)],
    )
    pad_group.add_pad(spi2_sck)

    # spi2_sd_0: mux with gpio_26
    alt_spi2_sd_0 = SinglePad(
        name="spi2_sd_0",
        type=PadType.INOUT,
    )
    alt_gpio_26 = SinglePad(
        name="gpio_26",
        type=PadType.INOUT,
    )
    spi2_sd_0 = MultiplexedPad(
        name="spi2_sd_0",
        type=PadType.INOUT,
        alts=[("spi2_sd_0", alt_spi2_sd_0), ("gpio_26", alt_gpio_26)],
    )
    pad_group.add_pad(spi2_sd_0)

    # spi2_sd_1: mux with gpio_27
    alt_spi2_sd_1 = SinglePad(
        name="spi2_sd_1",
        type=PadType.INOUT,
    )
    alt_gpio_27 = SinglePad(
        name="gpio_27",
        type=PadType.INOUT,
    )
    spi2_sd_1 = MultiplexedPad(
        name="spi2_sd_1",
        type=PadType.INOUT,
        alts=[("spi2_sd_1", alt_spi2_sd_1), ("gpio_27", alt_gpio_27)],
    )
    pad_group.add_pad(spi2_sd_1)

    # spi2_sd_2: mux with gpio_28
    alt_spi2_sd_2 = SinglePad(
        name="spi2_sd_2",
        type=PadType.INOUT,
    )
    alt_gpio_28 = SinglePad(
        name="gpio_28",
        type=PadType.INOUT,
    )
    spi2_sd_2 = MultiplexedPad(
        name="spi2_sd_2",
        type=PadType.INOUT,
        alts=[("spi2_sd_2", alt_spi2_sd_2), ("gpio_28", alt_gpio_28)],
    )
    pad_group.add_pad(spi2_sd_2)

    # spi2_sd_3: mux with gpio_29
    alt_spi2_sd_3 = SinglePad(
        name="spi2_sd_3",
        type=PadType.INOUT,
    )
    alt_gpio_29 = SinglePad(
        name="gpio_29",
        type=PadType.INOUT,
    )
    spi2_sd_3 = MultiplexedPad(
        name="spi2_sd_3",
        type=PadType.INOUT,
        alts=[("spi2_sd_3", alt_spi2_sd_3), ("gpio_29", alt_gpio_29)],
    )
    pad_group.add_pad(spi2_sd_3)

    # i2c_scl: mux with gpio_31
    alt_i2c_scl = SinglePad(
        name="i2c_scl",
        type=PadType.INOUT,
    )
    alt_gpio_31 = SinglePad(
        name="gpio_31",
        type=PadType.INOUT,
    )
    i2c_scl = MultiplexedPad(
        name="i2c_scl",
        type=PadType.INOUT,
        alts=[("i2c_scl", alt_i2c_scl), ("gpio_31", alt_gpio_31)],
    )
    pad_group.add_pad(i2c_scl)

    # i2c_sda: mux with gpio_30
    alt_i2c_sda = SinglePad(
        name="i2c_sda",
        type=PadType.INOUT,
    )
    alt_gpio_30 = SinglePad(
        name="gpio_30",
        type=PadType.INOUT,
    )
    i2c_sda = MultiplexedPad(
        name="i2c_sda",
        type=PadType.INOUT,
        alts=[("i2c_sda", alt_i2c_sda), ("gpio_30", alt_gpio_30)],
    )
    pad_group.add_pad(i2c_sda)

    # -------------------------------------------------------------------------
    # Wrap everything in a PadRing
    # -------------------------------------------------------------------------
    pad_ring = PadRing(pad_group)
    return pad_ring
