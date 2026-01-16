from ..abstractions import UserPeripheral


class I2C(UserPeripheral):
    """
    Inter-Integrated Circuit communication interface.
    """

    _name = "i2c"
    _pins = ["i2c_scl", "i2c_sda"]
