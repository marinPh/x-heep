from ..abstractions import UserPeripheral


class SPI_host(UserPeripheral):
    """
    Serial Peripheral Interface host controller.

    """

    _name = "spi_host"
    _pins = [
        "spi_sck",
        "spi_cs_0", "spi_cs_1",
        "spi_sd_0", "spi_sd_1", "spi_sd_2", "spi_sd_3",
    ]
