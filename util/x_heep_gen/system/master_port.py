"""
Master port representation for the X-HEEP system bus.

A master port can be:
- Fixed (CPU, debug) - not owned by any peripheral
- Peripheral-owned (DMA, future AXI bridge, etc.)
"""


class MasterPort:
    """
    Represents a single master port on the system bus.

    Master ports are registered during configuration time and assigned
    indices during build time.

    :param str name: Unique name for the master port (e.g., "DMA_READ_P0")
    :param owner: Peripheral instance that owns this port, or None for fixed masters
    :param str port_type: Type of port (e.g., "cpu", "debug", "read", "write", "addr")
    :param int owner_port_index: Index within owner's ports (for peripherals with multiple ports)
    """

    def __init__(
        self,
        name: str,
        owner,  # Peripheral instance or None
        port_type: str,
        owner_port_index: int = None,
    ):
        """
        Initialize a master port.

        :param str name: Unique name for the master port
        :param owner: Peripheral instance or None for fixed masters (CPU, debug)
        :param str port_type: Type identifier for this port
        :param int owner_port_index: Port index within the owner (for array ports)
        """
        self.name = name
        self.owner = owner
        self.port_type = port_type
        self.owner_port_index = owner_port_index if owner_port_index is not None else 0
        self.index = None  # Assigned during registry.build()
        self.attributes = {}  # Extensible metadata

    def is_fixed(self) -> bool:
        """
        Check if this is a fixed master (CPU or debug).

        :return: True if owner is None (fixed master)
        :rtype: bool
        """
        return self.owner is None

    def is_peripheral(self) -> bool:
        """
        Check if this is owned by a peripheral.

        :return: True if owner is a peripheral instance
        :rtype: bool
        """
        return self.owner is not None

    def __repr__(self):
        """String representation for debugging."""
        if self.index is not None:
            return f"MasterPort({self.name}, idx={self.index})"
        else:
            return f"MasterPort({self.name}, idx=unassigned)"

    def __str__(self):
        """Human-readable string representation."""
        owner_str = self.owner.get_name() if self.owner else "fixed"
        idx_str = str(self.index) if self.index is not None else "?"
        return f"[{idx_str:>2}] {self.name:20s} (type={self.port_type:8s}, owner={owner_str})"
