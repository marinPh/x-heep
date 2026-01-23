from ..abstractions import UserPeripheral, Interrupt


class SPI2(UserPeripheral):
    """
    Secondary Serial Peripheral Interface.
    """

    _name = "spi2"

    _interrupts = [
        Interrupt(49, peripheral="SPI2", name="spi2_intr_event"),
    ]
