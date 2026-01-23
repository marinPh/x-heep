from ..abstractions import UserPeripheral, Interrupt


class I2S(UserPeripheral):
    """
    Inter-IC Sound interface.

    """

    _name = "i2s"

    _interrupts = [
        Interrupt(50, peripheral="I2S", name="i2s_intr_event"),
    ]
