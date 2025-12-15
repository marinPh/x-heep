"""
Central registry for all master ports on the X-HEEP system bus.

Inherits common registry functionality from PortRegistry.
"""

from typing import List, Optional
from .master_port import MasterPort
from .port_registry import PortRegistry


class MasterRegistry(PortRegistry):
    """
    Central registry for all master ports on the system bus.

    Inherits from PortRegistry for common functionality.
    Adds master-specific methods like get_dma_master_index_map().

    Two-phase lifecycle:
    1. Configuration: Masters are registered via register()
    2. Build: Registry finalizes via build() - assigns indices, validates

    Example usage:
        # Configuration time
        registry = MasterRegistry()
        registry.register_fixed_masters()
        registry.register(MasterPort("DMA_READ_P0", dma, "read", 0))

        # Build time
        registry.build()

        # Query time
        total = registry.get_total_count()
        all_masters = registry.get_all()
    """

    def __init__(self):
        """Initialize an empty master registry."""
        super().__init__()
        self._fixed_masters_registered: bool = False

    # ===================================================================
    # CONFIGURATION TIME API
    # ===================================================================

    def register_fixed_masters(self):
        """
        Register CPU and debug masters.

        Called once during XHeep.__init__().
        These are the fixed master ports that always exist.
        """
        if self._fixed_masters_registered:
            return  # Already registered

        self.register(MasterPort("CORE_INSTR", None, "cpu"))
        self.register(MasterPort("CORE_DATA", None, "cpu"))
        self.register(MasterPort("DEBUG_MASTER", None, "debug"))

        self._fixed_masters_registered = True

    def register_from_spec(self, spec, owner=None):
        """
        Create and register a master port from a specification dict.

        Factory method that creates MasterPort objects from simple dict specs.

        :param dict spec: Master port specification with keys:
            - "name" (required): Master port name
            - "type" (optional): Port type, default "custom"
            - "index" (optional): Port index, default 0
        :param owner: Owner peripheral instance, or None for global masters
        :return: The created and registered MasterPort
        :rtype: MasterPort
        :raises RuntimeError: If called after build()
        :raises KeyError: If spec missing required "name" field
        """
        name = spec["name"]
        port_type = spec.get("type", "custom")
        port_index = spec.get("index", 0)

        master = MasterPort(name, owner, port_type, port_index)
        return self.register(master)

    def register_peripheral_masters(self, peripheral):
        """
        Register all master ports from a peripheral's master_specs.

        Called automatically when a peripheral is added to a domain.
        Uses the factory pattern: peripheral has specs (dicts), registry creates objects.

        :param peripheral: Peripheral instance with master_specs attribute
        :return: List of created MasterPort objects
        :rtype: List[MasterPort]
        """
        if not hasattr(peripheral, "master_specs"):
            return []

        created_masters = []
        for spec in peripheral.master_specs:
            master = self.register_from_spec(spec, owner=peripheral)
            created_masters.append(master)

        return created_masters

    # ===================================================================
    # QUERY API (after build)
    # ===================================================================

    def get_peripheral_masters(self) -> List[MasterPort]:
        """
        Get peripheral-owned masters in index order.

        :return: List of peripheral MasterPort objects
        :rtype: List[MasterPort]
        """
        # Use base class method
        return self.get_component_ports()

    def get_fixed_masters(self) -> List[MasterPort]:
        """
        Get fixed masters (CPU, debug) in index order.

        :return: List of fixed MasterPort objects
        :rtype: List[MasterPort]
        """
        # Use base class method
        return self.get_fixed_ports()

    def get_by_owner(self, peripheral) -> List[MasterPort]:
        """
        Get all masters for a specific peripheral instance.

        :param peripheral: Peripheral instance
        :return: List of MasterPort objects owned by this peripheral
        :rtype: List[MasterPort]
        """
        self._ensure_built()
        return [m for m in self._ports if m.owner == peripheral]

    def get_dma_master_index_map(self, dma_peripheral) -> dict:
        """
        Get DMA master port index map organized by port type.

        Returns a dictionary mapping port types (read/write/addr) to lists of indices.
        Used by templates to generate DMA_READ_MASTER_IDXS, DMA_WRITE_MASTER_IDXS, etc.

        :param dma_peripheral: DMA peripheral instance
        :return: Dict mapping port type to list of master indices
        :rtype: dict
        :raises RuntimeError: If any expected DMA master port is missing

        Example output for num_master_ports=2:
        {
            "read": [5, 6],
            "write": [7, 8],
            "addr": [3, 4]
        }
        """
        self._ensure_built()

        num_ports = dma_peripheral.get_num_master_ports()
        if num_ports == 0:
            return {"read": [], "write": [], "addr": []}

        # Initialize map with None values
        idx_map = {
            "read": [None] * num_ports,
            "write": [None] * num_ports,
            "addr": [None] * num_ports,
        }

        # Get all DMA masters and populate map
        dma_masters = self.get_by_owner(dma_peripheral)

        for master in dma_masters:
            if master.port_type in idx_map:
                idx_map[master.port_type][master.owner_port_index] = master.index

        # Validate no missing indices
        for port_type, idx_list in idx_map.items():
            if any(idx is None for idx in idx_list):
                missing = [str(i) for i, idx in enumerate(idx_list) if idx is None]
                raise RuntimeError(
                    f"Missing DMA {port_type} master indices for ports: {', '.join(missing)}"
                )

        return idx_map

    def dump(self):
        """Print registry contents for debugging."""
        super().dump(port_type_name="Master")

    # ===================================================================
    # TEMPLATE METHOD IMPLEMENTATIONS (from PortRegistry)
    # ===================================================================

    def _sort_key(self, master: MasterPort):
        """
        Define sorting order for master ports.

        Sorting order:
        1. Fixed masters (CPU, debug) - alphabetically
        2. Peripheral masters - by owner name, then port type, then name

        :param MasterPort master: Master port to generate sort key for
        :return: Sort key tuple
        """
        if master.is_fixed():
            # Fixed masters: sort alphabetically
            return (0, master.name)
        else:
            # Peripheral masters: sort by owner, type, name
            owner_name = master.owner.get_name() if master.owner else ""
            return (1, owner_name, master.port_type, master.name)

    def _validate(self):
        """
        Validate master registry state.

        Checks:
        - Required masters exist (CORE_INSTR, CORE_DATA, DEBUG_MASTER)
        - Sequential indices (no gaps)

        :raises ValueError: If validation fails
        """
        # Check required masters exist
        required = ["CORE_INSTR", "CORE_DATA", "DEBUG_MASTER"]
        for name in required:
            found = any(m.name == name for m in self._ports)
            if not found:
                raise ValueError(f"Required master '{name}' not found in registry")

        # Validate sequential indices using base class helper
        self._validate_sequential_indices()
