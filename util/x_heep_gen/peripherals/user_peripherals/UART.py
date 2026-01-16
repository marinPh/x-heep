from ..abstractions import UserPeripheral


class UART(UserPeripheral):
    """
    Universal Asynchronous Receiver/Transmitter for serial communication.

    """

    _name = "uart"
    _pins = ["uart_rx", "uart_tx"]
