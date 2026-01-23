from ..abstractions import UserPeripheral, Interrupt


class GPIO(UserPeripheral):
    """
    General Purpose Input/Output controller.

    """

    _name = "gpio"

    _interrupts = [Interrupt(9, 24, 8, "GPIO", name="gpio_intr")]
