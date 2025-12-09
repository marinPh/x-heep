from ..abstractions import UserPeripheral, Interrupt


class I2S(UserPeripheral):
    """
    Inter-IC Sound interface.

    """

    _name = "i2s"

    _interrupts = {
        "i2s_intr_event": Interrupt(50, "I2S"),
    }
