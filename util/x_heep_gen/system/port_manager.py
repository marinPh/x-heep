"""
PortManager - User-friendly facade for master and slave registries.

Provides a simplified API for working with bus ports while delegating
to the underlying MasterRegistry and SlaveRegistry implementations.

This is a Facade pattern implementation that hides internal complexity.
"""

from typing import Union, Optional, List
from .master_port import MasterPort
from .slave_port import SlavePort
from .master_registry import MasterRegistry
from .slave_registry import SlaveRegistry


class PortManager:
    """
    Unified facade for managing master and slave ports.

    Simplifies port management by providing a single, intuitive API
    while delegating to specialized registries internally.
    """

    def __init__(self, master_registry: MasterRegistry, slave_registry: SlaveRegistry):
        """
        Initialize port manager with existing registries.

        :param MasterRegistry master_registry: Master port registry
        :param SlaveRegistry slave_registry: Slave port registry
        """
        self._master_registry = master_registry
        self._slave_registry = slave_registry

    # ================================================================
    # REGISTRATION API
    # ================================================================

    def add_master(
        self,
        name: str,
        port_type: str = "custom",
        owner=None,
        owner_port_index: int = 0
    ) -> MasterPort:
        """
        Add a master port with minimal parameters.

        :param str name: Unique name for the master port
        :param str port_type: Port type (default: "custom")
        :param owner: Owner peripheral, or None for global master
        :param int owner_port_index: Index within owner's port array
        :return: The created MasterPort
        :rtype: MasterPort
        """
        spec = {"name": name, "type": port_type, "index": owner_port_index}
        return self._master_registry.register_from_spec(spec, owner=owner)

    def add_slave(
        self,
        name: str,
        start: int,
        size: int,
        owner=None
    ) -> SlavePort:
        """
        Add a slave port with minimal parameters.

        :param str name: Unique name for the slave port
        :param int start: Start address in memory map
        :param int size: Size of address space in bytes
        :param owner: Owner object (None for fixed slaves)
        :return: The created SlavePort
        :rtype: SlavePort

        """
        slave = SlavePort(name, start, size, owner)
        return self._slave_registry.register(slave)

    # ================================================================
    # UNIFIED QUERY API
    # ================================================================

    def get(self, name: str) -> Union[MasterPort, SlavePort, None]:
        """
        Get a port by name (automatically searches both masters and slaves).

        :param str name: Port name
        :return: MasterPort, SlavePort, or None if not found
        :rtype: Union[MasterPort, SlavePort, None]
        """
        # Try master first
        master = self._master_registry.get_by_name(name)
        if master is not None:
            return master

        # Try slave
        return self._slave_registry.get_by_name(name)


    # ================================================================
    # COLLECTION ACCESS
    # ================================================================

    def masters(self) -> List[MasterPort]:
        """
        Get all master ports in index order.

        :return: List of all MasterPort objects
        :rtype: List[MasterPort]
        """
        return self._master_registry.get_all()

    def slaves(self) -> List[SlavePort]:
        """
        Get all slave ports in index order.

        :return: List of all SlavePort objects
        :rtype: List[SlavePort]
        """
        return self._slave_registry.get_all()

    def all(self) -> dict:
        """
        Get all ports organized by type.

        :return: Dictionary with 'masters' and 'slaves' keys
        :rtype: dict

        Example:
            ports = xheep.ports.all()
            for master in ports['masters']:
                print(f"Master: {master.name}")
            for slave in ports['slaves']:
                print(f"Slave: {slave.name}")
        """
        return {
            'masters': self.masters(),
            'slaves': self.slaves()
        }

    def count(self) -> dict:
        """
        Get port counts.

        :return: Dictionary with 'masters', 'slaves', and 'total' counts
        :rtype: dict
        """
        return {
            'masters': self._master_registry.get_total_count(),
            'slaves': self._slave_registry.get_total_count(),
            'total': self._master_registry.get_total_count() + self._slave_registry.get_total_count()
        }

    # ================================================================
    # SPECIALIZED QUERIES
    # ================================================================

    def masters_by_owner(self, peripheral) -> List[MasterPort]:
        """
        Get all master ports owned by a specific peripheral.

        :param peripheral: Peripheral instance
        :return: List of MasterPort objects
        :rtype: List[MasterPort]
        """
        return self._master_registry.get_by_owner(peripheral)

    def peripheral_masters(self) -> List[MasterPort]:
        """Get peripheral-owned masters."""
        return self._master_registry.get_peripheral_masters()

    def peripheral_slaves(self) -> List[SlavePort]:
        """Get peripheral-owned slaves."""
        return self._slave_registry.get_component_ports()

    # ================================================================
    # DIRECT REGISTRY ACCESS 
    # ================================================================

    @property
    def master_registry(self) -> MasterRegistry:
        """
        Access underlying master registry directly (advanced usage).

        :return: MasterRegistry instance
        :rtype: MasterRegistry
        """
        return self._master_registry

    @property
    def slave_registry(self) -> SlaveRegistry:
        """
        Access underlying slave registry directly (advanced usage).

        :return: SlaveRegistry instance
        :rtype: SlaveRegistry
        """
        return self._slave_registry
