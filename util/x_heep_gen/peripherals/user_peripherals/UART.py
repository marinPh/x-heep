from ..abstractions import UserPeripheral, Interrupt


class UART(UserPeripheral):
    """
    Universal Asynchronous Receiver/Transmitter for serial communication.

    """

    _name = "uart"

    _interrupts = [
        Interrupt(1, peripheral="UART", name="uart_intr_tx_watermark"),
        Interrupt(2, peripheral="UART", name="uart_intr_rx_watermark"),
        Interrupt(3, peripheral="UART", name="uart_intr_tx_empty"),
        Interrupt(4, peripheral="UART", name="uart_intr_rx_overflow"),
        Interrupt(5, peripheral="UART", name="uart_intr_rx_frame_err"),
        Interrupt(6, peripheral="UART", name="uart_intr_rx_break_err"),
        Interrupt(7, peripheral="UART", name="uart_intr_rx_timeout"),
        Interrupt(8, peripheral="UART", name="uart_intr_rx_parity_err"),
    ]
