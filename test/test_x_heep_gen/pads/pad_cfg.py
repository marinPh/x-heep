from typing import Dict, List, Tuple
import sys

from util.x_heep_gen.pads.Pad_domain import pad, rng, mux, _mk_cfg
_ALL: List[Tuple[str, Dict]] = [

    # Singles
    pad("clk", "input"),
    pad("rst", "input", active="low", driven_manually=True),
    pad("boot_select", "input"),
    pad("execute_from_flash", "input"),

    pad("jtag_tck", "input"),
    pad("jtag_tms", "input"),
    pad("jtag_trst", "input", active="low"),
    pad("jtag_tdi", "input"),
    pad("jtag_tdo", "output"),

    pad("uart_rx", "input"),
    pad("uart_tx", "output"),

    pad("exit_valid", "output"),

    # Ranges
    rng("gpio", 14, "inout", offset=0),

    # SPI flash
    pad("spi_flash_sck", "inout"),
    rng("spi_flash_cs", 2, "inout"),
    rng("spi_flash_sd", 4, "inout"),

    # SPI host
    pad("spi_sck", "inout"),
    rng("spi_cs", 2, "inout"),
    rng("spi_sd", 4, "inout"),

    # SPI slave (muxed)
    mux("spi_slave_sck",  "inout", [("spi_slave_sck","input"),  ("gpio_14","inout")]),
    mux("spi_slave_cs",   "inout", [("spi_slave_cs","input"),   ("gpio_15","inout")]),
    mux("spi_slave_miso", "inout", [("spi_slave_miso","inout"), ("gpio_16","inout")]),
    mux("spi_slave_mosi", "inout", [("spi_slave_mosi","input"), ("gpio_17","inout")]),

    # PDM2PCM (muxed)
    mux("pdm2pcm_pdm", "inout", [("pdm2pcm_pdm","inout"), ("gpio_18","inout")]),
    mux("pdm2pcm_clk", "inout", [("pdm2pcm_clk","inout"), ("gpio_19","inout")]),

    # I2S (muxed)
    mux("i2s_sck", "inout", [("i2s_sck","inout"), ("gpio_20","inout")]),
    mux("i2s_ws",  "inout", [("i2s_ws","inout"),  ("gpio_21","inout")]),
    mux("i2s_sd",  "inout", [("i2s_sd","inout"),  ("gpio_22","inout")]),

    # SPI2 (muxed)
    mux("spi2_cs_0", "inout", [("spi2_cs_0","inout"), ("gpio_23","inout")]),
    mux("spi2_cs_1", "inout", [("spi2_cs_1","inout"), ("gpio_24","inout")]),
    mux("spi2_sck",  "inout", [("spi2_sck","inout"),  ("gpio_25","inout")]),
    mux("spi2_sd_0", "inout", [("spi2_sd_0","inout"), ("gpio_26","inout")]),
    mux("spi2_sd_1", "inout", [("spi2_sd_1","inout"), ("gpio_27","inout")]),
    mux("spi2_sd_2", "inout", [("spi2_sd_2","inout"), ("gpio_28","inout")]),
    mux("spi2_sd_3", "inout", [("spi2_sd_3","inout"), ("gpio_29","inout")]),

    # I2C (muxed)
    mux("i2c_scl", "inout", [("i2c_scl","inout"), ("gpio_31","inout")]),
    mux("i2c_sda", "inout", [("i2c_sda","inout"), ("gpio_30","inout")]),
]

# Build the canonical PAD_CFG (full set)


def config() -> Dict:
    """
    Return the full pad configuration dictionary.
    Example: config()
    """
    PAD_CFG = _mk_cfg(_ALL)
    return PAD_CFG