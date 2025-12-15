"""
SlavePort class for representing slave ports on the system bus.

Similar to MasterPort, but for the slave side of the crossbar.
"""


class SlavePort:
    """
    Represents a single slave port on the system bus.

    Attributes:
        name: Unique identifier (e.g., "DEBUG", "AO_PERIPHERAL", "RAM0")
        start_address: Start address in memory map
        size: Size of address space
        owner: Owner object (None for fixed slaves like ERROR/DEBUG)
        index: Assigned during registry.build() (sequential: 0, 1, 2, ...)
    """

    def __init__(self, name: str, start_address: int, size: int, owner=None):
        """
        Create a slave port.

        :param str name: Unique slave port name
        :param int start_address: Start address in memory map
        :param int size: Size of address space in bytes
        :param owner: Owning object (None for fixed slaves)
        """
        self.name = name
        self.start_address = start_address
        self.size = size
        self.owner = owner
        self.index = None  # Assigned during build()

    @property
    def end_address(self) -> int:
        """Get end address (start + size)."""
        return self.start_address + self.size

    def is_fixed(self) -> bool:
        """Check if this is a fixed slave (no owner)."""
        return self.owner is None

    def is_peripheral(self) -> bool:
        """Check if this slave is owned by a peripheral/component."""
        return self.owner is not None

    def __repr__(self):
        owner_str = "fixed" if self.owner is None else f"{self.owner}"
        return (
            f"SlavePort(name={self.name}, "
            f"addr=0x{self.start_address:08X}-0x{self.end_address:08X}, "
            f"index={self.index}, owner={owner_str})"
        )
