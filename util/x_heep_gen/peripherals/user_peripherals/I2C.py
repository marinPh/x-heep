from ..abstractions import UserPeripheral, Interrupt


class I2C(UserPeripheral):
    """
    Inter-Integrated Circuit communication interface.
    """

    _name = "i2c"

    _interrupts = {
        "intr_fmt_watermark": Interrupt(33, peripheral="I2C"),
        "intr_rx_watermark": Interrupt(34, peripheral="I2C"),
        "intr_fmt_overflow": Interrupt(35, peripheral="I2C"),
        "intr_rx_overflow": Interrupt(36, peripheral="I2C"),
        "intr_nak": Interrupt(37, peripheral="I2C"),
        "intr_scl_interference": Interrupt(38, peripheral="I2C"),
        "intr_sda_interference": Interrupt(39, peripheral="I2C"),
        "intr_stretch_timeout": Interrupt(40, peripheral="I2C"),
        "intr_sda_unstable": Interrupt(41, peripheral="I2C"),
        "intr_trans_complete": Interrupt(42, peripheral="I2C"),
        "intr_tx_empty": Interrupt(43, peripheral="I2C"),
        "intr_tx_nonempty": Interrupt(44, peripheral="I2C"),
        "intr_tx_overflow": Interrupt(45, peripheral="I2C"),
        "intr_acq_overflow": Interrupt(46, peripheral="I2C"),
        "intr_ack_stop": Interrupt(47, peripheral="I2C"),
        "intr_host_timeout": Interrupt(48, peripheral="I2C"),
    }
