from ..abstractions import UserPeripheral


class I2S(UserPeripheral):
    """
    Inter-IC Sound interface.

    """

    _name = "i2s"
    _pins = ["i2s_sck", "i2s_ws", "i2s_sd"]
