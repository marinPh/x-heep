"""
Base class for port registries (masters and slaves).

Uses Template Method pattern to share common registry logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar

# Generic type for port objects (MasterPort or SlavePort)
PortType = TypeVar("PortType")


class PortRegistry(ABC):
    """
    Abstract base class for managing ports on the system bus.

    Provides common functionality for both master and slave registries:
    - Two-phase lifecycle (register → build)
    - Sequential index assignment
    - Validation
    - Query methods

    Subclasses must implement:
    - _sort_key(): Define sorting order
    - _validate(): Define validation rules
    """

    def __init__(self):
        """Initialize empty registry."""
        self._ports: List[PortType] = []
        self._is_built = False
        self._is_configured = False

    def register(self, port: PortType) -> PortType:
        """
        Register a port (master or slave).

        Template method - common registration logic.

        :param port: Port object to register
        :return: The registered port
        :raises RuntimeError: If registry already built
        :raises ValueError: If duplicate port name
        """
        if self._is_built:

            return

        # Check for duplicate names
        if self._port_exists(port.name):
            raise ValueError(f"Port '{port.name}' already exists in registry")

        self._ports.append(port)
        return port

    def build(self):
        """
        Finalize registry: sort ports and assign sequential indices.

        Template method - common build logic.
        Subclasses define sorting via _sort_key() and validation via _validate().
        """
        if self._is_built:
            return  # Already built

        # Sort using subclass-defined key
        self._ports.sort(key=self._sort_key)

        # Assign sequential indices
        for idx, port in enumerate(self._ports):
            port.index = idx

        # Validate using subclass-defined rules
        self._validate()

        self._is_built = True

    @abstractmethod
    def _sort_key(self, port: PortType):
        """
        Define sorting order for ports.

        Subclasses must implement this to specify how ports should be sorted
        before index assignment.

        :param port: Port to generate sort key for
        :return: Sort key (tuple, string, etc.)
        """
        pass

    @abstractmethod
    def _validate(self):
        """
        Validate registry state after sorting and index assignment.

        Subclasses must implement this to perform validation checks
        specific to master or slave ports.

        :raises ValueError: If validation fails
        """
        pass

    def get_all(self) -> List[PortType]:
        """
        Get all ports in index order.

        :return: List of all port objects
        """
        self._ensure_built()
        return self._ports.copy()

    def get_by_name(self, name: str) -> Optional[PortType]:
        """
        Get a port by name.

        :param str name: Port name
        :return: Port object or None if not found
        """
        self._ensure_built()
        for port in self._ports:
            if port.name == name:
                return port
        return None

    def get_total_count(self) -> int:
        """
        Get total number of ports.

        Used for SYSTEM_XBAR_NMASTER or SYSTEM_XBAR_NSLAVE.

        :return: Number of ports
        """
        self._ensure_built()
        return len(self._ports)

    def get_fixed_ports(self) -> List[PortType]:
        """
        Get fixed ports (no owner) in index order.

        :return: List of fixed port objects
        """
        self._ensure_built()
        return [p for p in self._ports if p.is_fixed()]

    def get_component_ports(self) -> List[PortType]:
        """
        Get component-owned ports in index order.

        :return: List of component port objects
        """
        self._ensure_built()
        return [p for p in self._ports if not p.is_fixed()]

    def dump(self, port_type_name: str = "Port"):
        """
        Print registry contents for debugging.

        :param str port_type_name: Name to use in output (e.g., "Master", "Slave")
        """
        self._ensure_built()
        print(f"\n{port_type_name} Registry ({len(self._ports)} ports):")
        print("-" * 80)
        for port in self._ports:
            owner_str = (
                "fixed"
                if hasattr(port, "is_fixed") and port.is_fixed()
                else str(port.owner)
            )
            print(f"  [{port.index:2d}] {port.name:25s} owner={owner_str}")

    def _port_exists(self, name: str) -> bool:
        """
        Check if a port with given name already exists.

        :param str name: Port name to check
        :return: True if port exists
        """
        for port in self._ports:
            if port.name == name:
                return True
        return False

    def _ensure_built(self):
        """
        Ensure registry has been built before querying.

        :raises RuntimeError: If not yet built
        """
        if not self._is_built:
            raise RuntimeError(
                f"{self.__class__.__name__} must be built before querying. Call build() first."
            )

    def _validate_sequential_indices(self):
        """
        Helper: Validate that indices are sequential (0, 1, 2, ...).

        Can be called by subclass _validate() methods.

        :raises ValueError: If indices are not sequential
        """
        expected_indices = list(range(len(self._ports)))
        actual_indices = [p.index for p in self._ports]
        if actual_indices != expected_indices:
            raise ValueError(
                f"Port indices must be sequential. Expected {expected_indices}, got {actual_indices}"
            )
