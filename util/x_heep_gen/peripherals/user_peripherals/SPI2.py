from ..abstractions import UserPeripheral, Interrupt


class SPI2(UserPeripheral):
    """
    Secondary Serial Peripheral Interface.
    """

    _name = "spi2"

    _interrupts = {
        "spi2_intr_event": Interrupt(49, peripheral="SPI2"),
    }
