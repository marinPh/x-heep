from ..abstractions import UserPeripheral, Interrupt


class I2C(UserPeripheral):
    """
    Inter-Integrated Circuit communication interface.
    """

    _name = "i2c"

    _interrupts = [
        Interrupt(33, peripheral="I2C", name="i2c_intr_fmt_watermark"),
        Interrupt(34, peripheral="I2C", name="i2c_intr_rx_watermark"),
        Interrupt(35, peripheral="I2C", name="i2c_intr_fmt_overflow"),
        Interrupt(36, peripheral="I2C", name="i2c_intr_rx_overflow"),
        Interrupt(37, peripheral="I2C", name="i2c_intr_nak"),
        Interrupt(38, peripheral="I2C", name="i2c_intr_scl_interference"),
        Interrupt(39, peripheral="I2C", name="i2c_intr_sda_interference"),
        Interrupt(40, peripheral="I2C", name="i2c_intr_stretch_timeout"),
        Interrupt(41, peripheral="I2C", name="i2c_intr_sda_unstable"),
        Interrupt(42, peripheral="I2C", name="i2c_intr_trans_complete"),
        Interrupt(43, peripheral="I2C", name="i2c_intr_tx_empty"),
        Interrupt(44, peripheral="I2C", name="i2c_intr_tx_nonempty"),
        Interrupt(45, peripheral="I2C", name="i2c_intr_tx_overflow"),
        Interrupt(46, peripheral="I2C", name="i2c_intr_acq_overflow"),
        Interrupt(47, peripheral="I2C", name="i2c_intr_ack_stop"),
        Interrupt(48, peripheral="I2C", name="i2c_intr_host_timeout"),
    ]
