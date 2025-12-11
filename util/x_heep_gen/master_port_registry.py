#!/usr/bin/env python3
# Copyright 2024 EPFL
# Solderpad Hardware License, Version 2.1, see LICENSE.md for details.
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

"""
Master Port Registry
====================

Automatically assigns and tracks crossbar indices for all master ports in the system.
This eliminates manual index calculations and ensures consistency across templates.

"""


class MasterPortRegistry:
    """
    Registry for managing master port indices in the system crossbar.

    Automatically assigns sequential indices to master ports and provides
    lookup functionality for templates.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self.ports = {}  # Dictionary: port_name -> port_info
        self.next_idx = 0  # Running counter for sequential index assignment
        self.port_order = []  # Preserve registration order

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
                f"Port '{name}' is already registered with index {self.ports[name]['index']}"
            )

        port_info = {"index": self.next_idx, "name": name, "metadata": metadata or {}}

        self.ports[name] = port_info
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
        return self.ports[port_name]["index"]

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
        return self.ports[port_name]

    def get_total_masters(self):
        return self.next_idx

    def get_all_ports(self):
        return self.ports

    def get_ports_in_order(self):
        return [(name, self.ports[name]) for name in self.port_order]

    def has_port(self, port_name):
        return port_name in self.ports

    def __repr__(self):
        """String representation for debugging."""
        ports_str = "\n".join(
            f"  [{info['index']}] {name}" for name, info in self.get_ports_in_order()
        )
        return f"MasterPortRegistry (total={self.next_idx} masters):\n{ports_str}"


def build_master_registry(xheep):
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
    registry = MasterPortRegistry()

    # ========================================================================
    # Static Masters (Always Present)
    # ========================================================================
    registry.register_port(
        "core_instr",
        metadata={"type": "cpu", "description": "CPU instruction fetch port"},
    )

    registry.register_port(
        "core_data", metadata={"type": "cpu", "description": "CPU data load/store port"}
    )

    registry.register_port(
        "debug_master",
        metadata={"type": "debug", "description": "JTAG debug master port"},
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
            registry.register_port(
                f"dma_read_p{port_idx}",
                metadata={
                    "type": "dma",
                    "port": port_idx,
                    "channel": "read",
                    "description": f"DMA port {port_idx} read channel",
                },
            )

            # Write channel
            registry.register_port(
                f"dma_write_p{port_idx}",
                metadata={
                    "type": "dma",
                    "port": port_idx,
                    "channel": "write",
                    "description": f"DMA port {port_idx} write channel",
                },
            )

            # Address channel
            registry.register_port(
                f"dma_addr_p{port_idx}",
                metadata={
                    "type": "dma",
                    "port": port_idx,
                    "channel": "addr",
                    "description": f"DMA port {port_idx} address channel",
                },
            )

    # ========================================================================
    # Future Extension Point: Add New Master Peripherals Here
    # ========================================================================
    # Example for adding a GPU with master ports:
    # gpu = xheep.get_base_peripheral_domain().get_gpu()
    # if gpu.get_is_included():
    #     registry.register_port('gpu_read', metadata={'type': 'gpu'})
    #     registry.register_port('gpu_write', metadata={'type': 'gpu'})

    return registry


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
