from ..abstractions import UserPeripheral, Interrupt


class I2C(UserPeripheral):
    """
    Inter-Integrated Circuit communication interface.
    """

    _name = "i2c"

    _interrupts = {
        "intr_fmt_watermark": Interrupt(33, "I2C"),
        "intr_rx_watermark": Interrupt(34, "I2C"),
        "intr_fmt_overflow": Interrupt(35, "I2C"),
        "intr_rx_overflow": Interrupt(36, "I2C"),
        "intr_nak": Interrupt(37, "I2C"),
        "intr_scl_interference": Interrupt(38, "I2C"),
        "intr_sda_interference": Interrupt(39, "I2C"),
        "intr_stretch_timeout": Interrupt(40, "I2C"),
        "intr_sda_unstable": Interrupt(41, "I2C"),
        "intr_trans_complete": Interrupt(42, "I2C"),
        "intr_tx_empty": Interrupt(43, "I2C"),
        "intr_tx_nonempty": Interrupt(44, "I2C"),
        "intr_tx_overflow": Interrupt(45, "I2C"),
        "intr_acq_overflow": Interrupt(46, "I2C"),
        "intr_ack_stop": Interrupt(47, "I2C"),
        "intr_host_timeout": Interrupt(48, "I2C"),
    }
