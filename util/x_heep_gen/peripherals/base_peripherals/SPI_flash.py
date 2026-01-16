from ..abstractions import BasePeripheral


class SPI_flash(BasePeripheral):
    """
    Interface for external SPI flash memory access.

    Default length : 32KB
    """

    _name = "spi_flash"
    _length: int = 0x00008000
    _pins = [
        "spi_flash_sck",
        "spi_flash_cs_0", "spi_flash_cs_1",
        "spi_flash_sd_0", "spi_flash_sd_1", "spi_flash_sd_2", "spi_flash_sd_3",
    ]
