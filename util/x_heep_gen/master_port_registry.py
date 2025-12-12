"""
Master Port Registry
====================

Automatically assigns and tracks crossbar indices for all master ports in the system.
This eliminates manual index calculations and ensures consistency across templates.

"""


class MasterPort:
    """
    Represents a single master port in the system crossbar.
    
    Attributes:
        name (str): Unique name for the master port
        index (int): Assigned crossbar index
        metadata (dict): Additional metadata for the port
    """
    
    def __init__(self, name, index, metadata=None):
        """
        Initialize a MasterPort.
        
        Args:
            name (str): Unique name for the master port
            index (int): Assigned crossbar index
            metadata (dict, optional): Additional metadata for the port
        """
        self.name = name
        self.index = index
        self.metadata = metadata or {}
    
    def get_name(self):
        """Return the port name."""
        return self.name
    
    def get_index(self):
        """Return the crossbar index."""
        return self.index
    
    def get_metadata(self):
        """Return the port metadata."""
        return self.metadata
    
    def get_type(self):
        """Return the port type from metadata."""
        return self.metadata.get("type", "unknown")
    
    def get_description(self):
        """Return the port description from metadata."""
        return self.metadata.get("description", "")
    
    def __repr__(self):
        """String representation for debugging."""
        return f"MasterPort(name='{self.name}', index={self.index}, type='{self.get_type()}')"


class MasterPortRegistry:
    """
    Registry for managing master port indices in the system crossbar.

    Automatically assigns sequential indices to master ports and provides
    lookup functionality for templates.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self.ports = {}  # Dictionary: port_name -> MasterPort
        self.next_idx = 0  # Running counter for sequential index assignment
        self.port_order = []  # Preserve registration order
        self.prev_added_ports = []

    def register_port(self, name, metadata=None):
        """
        Register a single master port and assign it a sequential index.

        Args:
            name (str): Unique name for the master port (e.g., 'dma_read_p0')
            metadata (dict, optional): Additional metadata for the port

        Returns:
            int: The assigned index for this port

        Raises:
            ValueError: If port name already exists
        """
        if name in self.ports:
            raise ValueError(
                f"Port '{name}' is already registered with index {self.ports[name].get_index()}"
            )

        port = MasterPort(name, self.next_idx, metadata)

        self.ports[name] = port
        self.port_order.append(name)
        assigned_idx = self.next_idx
        self.next_idx += 1

        return assigned_idx

    def get_index(self, port_name):
        """
        Get the crossbar index for a named port.

        Args:
            port_name (str): Name of the port to look up

        Returns:
            int: The crossbar index assigned to this port

        Raises:
            ValueError: If port_name is not registered
        """
        if port_name not in self.ports:
            raise ValueError(
                f"Port '{port_name}' not registered! Available ports: {list(self.ports.keys())}"
            )
        return self.ports[port_name].get_index()

    def get_port(self, port_name):
        """
        Get the MasterPort object for a named port.

        Args:
            port_name (str): Name of the port

        Returns:
            MasterPort: The master port object

        Raises:
            ValueError: If port_name is not registered
        """
        if port_name not in self.ports:
            raise ValueError(f"Port '{port_name}' not registered!")
        return self.ports[port_name]

    def get_port_info(self, port_name):
        """
        Get complete information for a named port.

        Args:
            port_name (str): Name of the port

        Returns:
            dict: Port information including index and metadata
        """
        if port_name not in self.ports:
            raise ValueError(f"Port '{port_name}' not registered!")
        port = self.ports[port_name]
        return {"index": port.get_index(), "name": port.get_name(), "metadata": port.get_metadata()}

    def get_total_masters(self):
        return self.next_idx

    def get_all_ports(self):
        """Return all MasterPort objects as a dictionary."""
        return self.ports

    def get_ports_in_order(self):
        """Return list of (name, MasterPort) tuples in registration order."""
        return [(name, self.ports[name]) for name in self.port_order]

    def has_port(self, port_name):
        return port_name in self.ports

    def __repr__(self):
        """String representation for debugging."""
        ports_str = "\n".join(
            f"  [{port.get_index()}] {name}" for name, port in self.get_ports_in_order()
        )
        return f"MasterPortRegistry (total={self.next_idx} masters):\n{ports_str}"
    
    
    
### should be able to add master ports without building the registry
    def add_port(self, name, metadata=None):
        """
        Add a master port to the registry.

        Args:
            name (str): Unique name for the master port
            metadata (dict, optional): Additional metadata for the port
        """
        self.register_port(name, metadata)    


#TODO: should be a build step and use self
    def build_master_registry(self, xheep):
        """
        Build the complete master port registry for the X-HEEP system.

        This function is called during template generation and creates a registry
        containing all system master ports with their assigned indices.

        The registration order determines the crossbar indices:
          - Index 0-2: Static masters (CPU instruction, CPU data, Debug)
          - Index 3+: DMA masters (read/write/addr channels per port)
          - Future: Additional master peripherals can be added here

        Args:
            xheep: The XHeep system object containing peripheral configuration

        Returns:
            MasterPortRegistry: Fully populated registry with all master ports
        """

        # ========================================================================
        # Static Masters (Always Present)
        # ========================================================================
        self.register_port(
            "core_instr"
        )

        self.register_port(
            "core_data"
        )

        self.register_port(
            "debug_master"
        )

        # ========================================================================
        # DMA Masters (Dynamic based on configuration)
        # ========================================================================
        dma = xheep.get_base_peripheral_domain().get_dma()

        if dma.get_is_included():
            num_master_ports = dma.get_num_master_ports()

            # Register each DMA master port with its three channels
            for port_idx in range(num_master_ports):
                # Read channel
                self.register_port(
                    f"dma_read_p{port_idx}",
                    metadata={
                        "type": "dma",
                        "port": port_idx,
                        "channel": "read",
                        "description": f"DMA port {port_idx} read channel",
                    },
                )

                # Write channel
                self.register_port(
                    f"dma_write_p{port_idx}",
                    metadata={
                        "type": "dma",
                        "port": port_idx,
                        "channel": "write",
                        "description": f"DMA port {port_idx} write channel",
                    },
                )

                # Address channel
                self.register_port(
                    f"dma_addr_p{port_idx}",
                    metadata={
                        "type": "dma",
                        "port": port_idx,
                        "channel": "addr",
                        "description": f"DMA port {port_idx} address channel",
                    },
                )



def get_dma_port_indices(registry, port_num):
    """
    Helper function to get all three channel indices for a DMA port.

    Args:
        registry (MasterPortRegistry): The master port registry
        port_num (int): DMA port number (0, 1, 2, ...)

    Returns:
        dict: Dictionary with keys 'read', 'write', 'addr' mapping to indices
    """
    return {
        "read": registry.get_index(f"dma_read_p{port_num}"),
        "write": registry.get_index(f"dma_write_p{port_num}"),
        "addr": registry.get_index(f"dma_addr_p{port_num}"),
    }
