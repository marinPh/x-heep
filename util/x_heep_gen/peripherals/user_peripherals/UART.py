from ..abstractions import UserPeripheral,Interrupt


class UART(UserPeripheral):
    """
    Universal Asynchronous Receiver/Transmitter for serial communication.

    """

    _name = "uart"

    _interrupts = {
        "uart_intr_tx_watermark": Interrupt(1, "UART"),
        "uart_intr_rx_watermark": Interrupt(2, "UART"),
        "uart_intr_rx_overflow": Interrupt(3, "UART"),
        "uart_intr_rx_frame_err": Interrupt(4, "UART"),
        "uart_intr_rx_break_err": Interrupt(5, "UART"),
        "uart_intr_rx_timeout": Interrupt(6, "UART"),
        "uart_intr_rx_parity_err": Interrupt(7, "UART"),
    }
