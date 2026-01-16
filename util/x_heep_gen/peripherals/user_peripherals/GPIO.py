from ..abstractions import UserPeripheral


class GPIO(UserPeripheral):
    """
    General Purpose Input/Output controller.

    """

    _name = "gpio"
    _pins = [f"gpio_{i}" for i in range(32)]  # gpio_0 through gpio_31
