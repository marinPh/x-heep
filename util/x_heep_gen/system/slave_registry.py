"""
Central registry for all slave ports on the X-HEEP system bus.

Inherits common registry functionality from PortRegistry.
"""

from typing import List, Optional
from .slave_port import SlavePort
from .port_registry import PortRegistry


class SlaveRegistry(PortRegistry):
    """
    Central registry for all slave ports on the system bus.

    Inherits from PortRegistry for common functionality.
    Adds slave-specific methods like register_fixed_slaves() and register_ram_banks().

    Two-phase lifecycle:
    1. Configuration: Slaves are registered via register()
    2. Build: Registry finalizes via build() - assigns indices, validates

    Example usage:
        registry = SlaveRegistry()
        registry.register_fixed_slaves(...)
        registry.register_ram_banks(memory_ss)
        registry.build()
        total = registry.get_total_count()
    """

    def __init__(self):
        """Initialize empty slave registry."""
        super().__init__()

    # ===================================================================
    # CONFIGURATION TIME API
    # ===================================================================

    def register_fixed_slaves(
        self,
        memory_ss,
        debug_start: int,
        debug_size: int,
        ao_peripheral_start: int,
        ao_peripheral_size: int,
        peripheral_start: int,
        peripheral_size: int,
        flash_start: int,
        flash_size: int,
    ):
        """
        Register the fixed slaves that always exist.

        Order:
        1. ERROR (always idx 0)
        2. RAM banks (indices 1..numbanks, registered separately)
        3. DEBUG
        4. AO_PERIPHERAL
        5. PERIPHERAL
        6. FLASH_MEM

        :param memory_ss: MemorySS object (for RAM bank count)
        :param int debug_start: Debug module start address
        :param int debug_size: Debug module size
        :param int ao_peripheral_start: AO peripheral domain start
        :param int ao_peripheral_size: AO peripheral domain size
        :param int peripheral_start: User peripheral domain start
        :param int peripheral_size: User peripheral domain size
        :param int flash_start: Flash memory start
        :param int flash_size: Flash memory size
        """
        # ERROR slave (always first)
        self.register(SlavePort("ERROR", 0xBADACCE5, 0x1, owner=None))

        # RAM banks will be registered separately via register_ram_banks()

        # Fixed system slaves
        self.register(SlavePort("DEBUG", debug_start, debug_size, owner=None))
        self.register(
            SlavePort(
                "AO_PERIPHERAL", ao_peripheral_start, ao_peripheral_size, owner=None
            )
        )
        self.register(
            SlavePort("PERIPHERAL", peripheral_start, peripheral_size, owner=None)
        )
        self.register(SlavePort("FLASH_MEM", flash_start, flash_size, owner=None))
        self._is_configured = True

    def register_ram_banks(self, memory_ss):
        """
        Register RAM banks as slave ports.

        Called after register_fixed_slaves() but before build().

        :param memory_ss: MemorySS object with RAM bank information
        """
        for bank in memory_ss.iter_ram_banks():
            slave = SlavePort(
                name=f"RAM{bank.name()}",
                start_address=bank.start_address(),
                size=bank.size(),
                owner=bank,  # Bank object is the owner
            )
            self.register(slave)

    def dump(self):
        """Print registry contents for debugging."""
        self._ensure_built()
        print(f"\nSlave Registry ({len(self._ports)} slaves):")
        print("-" * 80)
        for slave in self._ports:
            owner_str = (
                "fixed" if slave.owner is None else str(type(slave.owner).__name__)
            )
            print(
                f"  [{slave.index:2d}] {slave.name:20s} "
                f"0x{slave.start_address:08X}-0x{slave.end_address:08X} "
                f"owner={owner_str}"
            )

    # ===================================================================
    # TEMPLATE METHOD IMPLEMENTATIONS (from PortRegistry)
    # ===================================================================

    def _sort_key(self, slave: SlavePort):
        """
        Define sorting order for slave ports.

        Sorting order:
        1. ERROR (always first)
        2. RAM banks (by name)
        3. Other fixed slaves (alphabetically)
        4. Component-owned slaves (by owner, then name)

        :param SlavePort slave: Slave port to generate sort key for
        :return: Sort key tuple
        """
        # ERROR always first
        if slave.name == "ERROR":
            return (0, "", slave.name)
        # RAM banks second (sorted by name)
        elif slave.name.startswith("RAM"):
            return (1, "", slave.name)
        # Fixed slaves third
        elif slave.is_fixed():
            return (2, "", slave.name)
        # Component-owned slaves last
        else:
            owner_name = slave.owner.__class__.__name__ if slave.owner else ""
            return (3, owner_name, slave.name)

    def _validate(self):
        """
        Validate slave registry state.

        Checks:
        - ERROR slave exists and is at index 0
        - No duplicate indices
        - No gaps in indices

        :raises ValueError: If validation fails
        """
        # Must have ERROR slave at index 0
        if (
            not self._ports
            or self._ports[0].name != "ERROR"
            or self._ports[0].index != 0
        ):
            raise ValueError("ERROR slave must exist and be at index 0")

        # Validate sequential indices using base class helper
        self._validate_sequential_indices()
