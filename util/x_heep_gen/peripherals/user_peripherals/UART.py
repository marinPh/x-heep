from ..abstractions import UserPeripheral, Interrupt


class UART(UserPeripheral):
    """
    Universal Asynchronous Receiver/Transmitter for serial communication.

    """

    _name = "uart"

    _interrupts = {
        "uart_intr_tx_watermark": Interrupt(1, peripheral="UART"),
        "uart_intr_rx_watermark": Interrupt(2, peripheral="UART"),
        "uart_intr_tx_empty": Interrupt(3, peripheral="UART"),
        "uart_intr_rx_overflow": Interrupt(4, peripheral="UART"),
        "uart_intr_rx_frame_err": Interrupt(5, peripheral="UART"),
        "uart_intr_rx_break_err": Interrupt(6, peripheral="UART"),
        "uart_intr_rx_timeout": Interrupt(7, peripheral="UART"),
        "uart_intr_rx_parity_err": Interrupt(8, peripheral="UART"),
    }
