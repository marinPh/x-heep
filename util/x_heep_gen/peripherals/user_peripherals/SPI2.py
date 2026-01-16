from ..abstractions import UserPeripheral


class SPI2(UserPeripheral):
    """
    Secondary Serial Peripheral Interface.
    """

    _name = "spi2"
    _pins = [
        "spi2_sck",
        "spi2_cs_0", "spi2_cs_1",
        "spi2_sd_0", "spi2_sd_1", "spi2_sd_2", "spi2_sd_3",
    ]
