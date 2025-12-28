"""
Pad Module (Pad.py)

This module defines the generation-time representation of pads used by templates.

The Pad class is the physical, template-facing representation created by PadRing
from PadDef configuration objects. It contains all information needed to generate
SystemVerilog, headers, and other RTL artifacts.

Key distinction:
    - PadDef: Configuration-time (what user writes)
    - Pad: Generation-time (what templates see)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Callable
from .PadDef import PadType, PadMapping, Orientation


# Pad type configuration for signal generation
#
# Configuration for generating pad cell instances by type.
#
# Maps pad types (input/output/inout) to their:
#     - ctrl_interface: Function generating control interface signals
#     - connections: Function generating port connections
#     - cell: Pad cell module name
#
# This configuration-driven approach ensures consistent generation
# across different pad types.
#
PAD_TYPE_CONFIG = {
    "input": {
        "ctrl_interface": lambda sig: f"    output logic {sig}o,",
        "connections": lambda sig: [
            ("pad_in_i", "1'b0"),
            ("pad_oe_i", "1'b0"),
            ("pad_out_o", f"{sig}o"),
            ("pad_io", f"{sig}io"),
        ],
        "cell": "pad_cell_input",
    },
    "output": {
        "ctrl_interface": lambda sig: f"    input logic {sig}i,",
        "connections": lambda sig: [
            ("pad_in_i", f"{sig}i"),
            ("pad_oe_i", "1'b1"),
            ("pad_out_o", ""),  # Empty signal (no connection)
            ("pad_io", f"{sig}io"),
        ],
        "cell": "pad_cell_output",
    },
    "inout": {
        "ctrl_interface": lambda sig: (
            f"    input logic {sig}i,\n"
            f"    output logic {sig}o,\n"
            f"    input logic {sig}oe_i,"
        ),
        "connections": lambda sig: [
            ("pad_in_i", f"{sig}i"),
            ("pad_oe_i", f"{sig}oe_i"),
            ("pad_out_o", f"{sig}o"),
            ("pad_io", f"{sig}io"),
        ],
        "cell": "pad_cell_inout",
    },
}


def _build_pad_connections(connections: List[Tuple[str, str]]) -> str:
    """
    Build connection string from list of (port, signal) tuples.

    :param connections: List of (port_name, signal_name) tuples
    :return: Formatted connection string
    :rtype: str
    """
    conn_lines = []
    for port, signal in connections:
        if signal:  # Only add non-empty signals
            conn_lines.append(f"   .{port}({signal}),")
        else:  # Empty signal gets empty parentheses
            conn_lines.append(f"   .{port}(),")
    return "\n".join(conn_lines) + "\n"


class Pad:
    """
    Generation-time pad representation for template rendering.

    This class holds all information needed by Mako templates to generate
    SystemVerilog, headers, and other RTL artifacts. It is created by PadRing
    from PadDef configuration objects.

    Attributes generated during construction:
        - name: Pad name
        - cell_name: Cell instance name
        - index: Physical pad index
        - localparam: SystemVerilog parameter name
        - pad_type: Pad type (input/output/inout)
        - pad_mapping: Physical location (top/bottom/left/right)
        - signal_name: Base signal name (with active suffix if needed)
        - has_attribute: Whether pad has attributes
        - attribute_bits: Number of attribute bits
        - is_muxed: Whether this is a multiplexed pad
        - layout_*: Physical layout properties (index, orient, cell, bondpad, offset, skip)

    Generated interface strings (populated by create_* methods):
        - pad_ring_io_interface: IO interface for pad ring
        - pad_ring_ctrl_interface: Control interface for pad ring
        - pad_ring_instance: Pad cell instance
        - core_v_mini_mcu_interface: Core interface
        - internal_signals: Internal signal declarations
        - mux_process: Mux selection logic
        - constant_driver_assign: Constant driver assignments
        - core_v_mini_mcu_bonding: Core bonding connections
        - pad_ring_bonding_bonding: Pad ring bonding connections
        - x_heep_system_interface: System-level interface
    """

    def remove_comma_io_interface(self):
        """Remove trailing comma from x_heep_system_interface (for last pad)."""
        s = self.x_heep_system_interface.rstrip()
        if s.endswith(","):
            self.x_heep_system_interface = s[:-1]
        else:
            self.x_heep_system_interface = s

    def create_pad_ring(self):
        """
        Generate pad ring instance and interface strings.

        Populates:
            - interface: Top-level IO interface
            - pad_ring_io_interface: Pad ring IO
            - pad_ring_ctrl_interface: Pad ring control signals
            - pad_ring_instance: Instantiation of pad cell
        """
        # Mapping dictionary (unchanged)
        mapping_dict = {
            PadMapping.TOP: "core_v_mini_mcu_pkg::TOP",
            PadMapping.RIGHT: "core_v_mini_mcu_pkg::RIGHT",
            PadMapping.BOTTOM: "core_v_mini_mcu_pkg::BOTTOM",
            PadMapping.LEFT: "core_v_mini_mcu_pkg::LEFT",
        }

        # Build ", .SIDE(...)" exactly like before
        mapping = (
            f", .SIDE({mapping_dict[self.pad_mapping]})" if self.pad_mapping else ""
        )

        # Top-level interface
        self.interface = f"    inout wire {self.name}_io,\n"

        # Parameter string (keeps same parenthesis position)
        param_str = f"#(.PADATTR({self.attribute_bits}){mapping})"
        sig = self.signal_name

        # --- Pad type logic (configuration-driven) ---
        if self.pad_type.split("_")[-1] in list(PAD_TYPE_CONFIG.keys()):
            config = PAD_TYPE_CONFIG[self.pad_type.split("_")[-1]]

            # Set IO interface (same for all types)
            self.pad_ring_io_interface = f"    inout wire {self.io_interface},"

            # Set control interface from configuration
            self.pad_ring_ctrl_interface += config["ctrl_interface"](sig)

            # Build connections from configuration
            conns = _build_pad_connections(config["connections"](sig))

            # Get cell type from configuration
            cell = config["cell"]

            # --- Instance construction ---
            header = f"{cell} {param_str} {self.cell_name} ( \n{conns}"
            if self.has_attribute:
                attr_line = (
                    f"   .pad_attributes_i(pad_attributes_i[core_v_mini_mcu_pkg::{self.localparam}])\n"
                    ");\n\n"
                )
            else:
                attr_line = "   .pad_attributes_i('0)" + ");\n\n"
            self.pad_ring_instance = header + attr_line

    def create_core_v_mini_mcu_ctrl(self):
        """
        Generate core_v_mini_mcu interface signals.

        Populates core_v_mini_mcu_interface based on pad type and drive signals.
        """

        cnt = len(self.pad_type_drive)

        for i in range(cnt):
            if self.driven_manually[i] == False:
                if (
                    self.pad_type_drive[i] == "input"
                    or self.pad_type_drive[i] == "bypass_input"
                ):
                    self.core_v_mini_mcu_interface += (
                        "    input logic " + self.signal_name_drive[i] + "i,\n"
                    )
                if (
                    self.pad_type_drive[i] == "output"
                    or self.pad_type_drive[i] == "bypass_output"
                ):
                    self.core_v_mini_mcu_interface += (
                        "    output logic " + self.signal_name_drive[i] + "o,\n"
                    )
                if (
                    self.pad_type_drive[i] == "inout"
                    or self.pad_type_drive[i] == "bypass_inout"
                ):
                    self.core_v_mini_mcu_interface += (
                        "    output logic " + self.signal_name_drive[i] + "o,\n"
                    )
                    self.core_v_mini_mcu_interface += (
                        "    input logic " + self.signal_name_drive[i] + "i,\n"
                    )
                    self.core_v_mini_mcu_interface += (
                        "    output logic " + self.signal_name_drive[i] + "oe_o,\n"
                    )

    def create_internal_signals(self):
        """Generate internal signal declarations for pad connections."""
        cnt = len(self.pad_type_drive)

        for i in range(cnt):

            self.in_internal_signals.append(self.signal_name_drive[i] + "in_x")
            self.out_internal_signals.append(self.signal_name_drive[i] + "out_x")
            self.oe_internal_signals.append(self.signal_name_drive[i] + "oe_x")

            if self.skip_declaration[i] == False:
                self.internal_signals += (
                    "  logic "
                    + self.in_internal_signals[i]
                    + ","
                    + self.out_internal_signals[i]
                    + ","
                    + self.oe_internal_signals[i]
                    + ";\n"
                )

    def create_multiplexers(self):
        """
        Generate mux selection logic for multiplexed pads.

        Creates mux_process with case statement for selecting between
        multiple pad functions.
        """
        cnt = len(self.pad_type_drive)

        if cnt > 1:
            ###muxing
            pad_in_internal_signals = self.signal_name + "in_x_muxed"
            pad_out_internal_signals = self.signal_name + "out_x_muxed"
            pad_oe_internal_signals = self.signal_name + "oe_x_muxed"

            self.internal_signals += (
                "  logic "
                + pad_in_internal_signals
                + ","
                + pad_out_internal_signals
                + ","
                + pad_oe_internal_signals
                + ";\n"
            )

            self.mux_process += "  always_comb\n" + "  begin\n"

            for i in range(cnt):
                self.mux_process += "   " + self.in_internal_signals[i] + "=1'b0;\n"

            self.mux_process += (
                "   unique case(pad_muxes[core_v_mini_mcu_pkg::"
                + self.localparam
                + "])\n"
            )

            for i in range(cnt):
                self.mux_process += (
                    "    "
                    + str(i)
                    + ": begin\n"
                    + "      "
                    + pad_out_internal_signals
                    + " = "
                    + self.out_internal_signals[i]
                    + ";\n"
                    + "      "
                    + pad_oe_internal_signals
                    + " = "
                    + self.oe_internal_signals[i]
                    + ";\n"
                    + "      "
                    + self.in_internal_signals[i]
                    + " = "
                    + pad_in_internal_signals
                    + ";\n"
                    + "    end\n"
                )

            self.mux_process += (
                "    default: begin\n"
                + "      "
                + pad_out_internal_signals
                + " = "
                + self.out_internal_signals[0]
                + ";\n"
                + "      "
                + pad_oe_internal_signals
                + " = "
                + self.oe_internal_signals[0]
                + ";\n"
                + "      "
                + self.in_internal_signals[0]
                + " = "
                + pad_in_internal_signals
                + ";\n"
                + "    end\n"
            )

            self.mux_process += "   endcase\n" + "  end\n"

    def create_constant_driver_assign(self):
        cnt = len(self.pad_type_drive)

        for i in range(cnt):

            if self.skip_declaration[i] == False:
                if (
                    self.pad_type_drive[i] == "input"
                    or self.pad_type_drive[i] == "bypass_input"
                ):
                    self.constant_driver_assign += (
                        "  assign " + self.out_internal_signals[i] + " = 1'b0;\n"
                    )
                    self.constant_driver_assign += (
                        "  assign " + self.oe_internal_signals[i] + " = 1'b0;\n"
                    )
                if (
                    self.pad_type_drive[i] == "output"
                    or self.pad_type_drive[i] == "bypass_output"
                ):
                    self.constant_driver_assign += (
                        "  assign " + self.oe_internal_signals[i] + " = 1'b1;\n"
                    )

    def create_core_v_mini_mcu_bonding(self):

        cnt = len(self.pad_type_drive)

        for i in range(cnt):

            if self.driven_manually[i] == False:
                if (
                    self.pad_type_drive[i] == "input"
                    or self.pad_type_drive[i] == "bypass_input"
                ):
                    self.core_v_mini_mcu_bonding += (
                        "    ."
                        + self.signal_name_drive[i]
                        + "i("
                        + self.in_internal_signals[i]
                        + "),\n"
                    )
                if (
                    self.pad_type_drive[i] == "output"
                    or self.pad_type_drive[i] == "bypass_output"
                ):
                    self.core_v_mini_mcu_bonding += (
                        "    ."
                        + self.signal_name_drive[i]
                        + "o("
                        + self.out_internal_signals[i]
                        + "),\n"
                    )
                if (
                    self.pad_type_drive[i] == "inout"
                    or self.pad_type_drive[i] == "bypass_inout"
                ):
                    self.core_v_mini_mcu_bonding += (
                        "    ."
                        + self.signal_name_drive[i]
                        + "i("
                        + self.in_internal_signals[i]
                        + "),\n"
                    )
                    self.core_v_mini_mcu_bonding += (
                        "    ."
                        + self.signal_name_drive[i]
                        + "o("
                        + self.out_internal_signals[i]
                        + "),\n"
                    )
                    self.core_v_mini_mcu_bonding += (
                        "    ."
                        + self.signal_name_drive[i]
                        + "oe_o("
                        + self.oe_internal_signals[i]
                        + "),\n"
                    )

    def create_pad_ring_bonding(self):

        if self.is_muxed:
            append_name = "_muxed"
        else:
            append_name = ""

        if self.pad_type == "input":
            in_internal_signals = self.signal_name + "in_x" + append_name
            self.pad_ring_bonding_bonding = (
                "    ." + self.io_interface + "(" + self.signal_name + "i),\n"
            )
            self.pad_ring_bonding_bonding += (
                "    ." + self.signal_name + "o(" + in_internal_signals + "),"
            )
            self.x_heep_system_interface += "    inout wire " + self.signal_name + "i,"
        if self.pad_type == "output":
            out_internal_signals = self.signal_name + "out_x" + append_name
            self.pad_ring_bonding_bonding = (
                "    ." + self.io_interface + "(" + self.signal_name + "o),\n"
            )
            self.pad_ring_bonding_bonding += (
                "    ." + self.signal_name + "i(" + out_internal_signals + "),"
            )
            self.x_heep_system_interface += "    inout wire " + self.signal_name + "o,"
        if self.pad_type == "inout":
            in_internal_signals = self.signal_name + "in_x" + append_name
            out_internal_signals = self.signal_name + "out_x" + append_name
            oe_internal_signals = self.signal_name + "oe_x" + append_name
            self.pad_ring_bonding_bonding = (
                "    ." + self.io_interface + "(" + self.signal_name + "io),\n"
            )
            self.pad_ring_bonding_bonding += (
                "    ." + self.signal_name + "o(" + in_internal_signals + "),\n"
            )
            self.pad_ring_bonding_bonding += (
                "    ." + self.signal_name + "i(" + out_internal_signals + "),\n"
            )
            self.pad_ring_bonding_bonding += (
                "    ." + self.signal_name + "oe_i(" + oe_internal_signals + "),"
            )
            self.x_heep_system_interface += "    inout wire " + self.signal_name + "io,"

    def __init__(
        self,
        name,
        cell_name,
        pad_type,
        pad_mapping,
        index,
        pad_layout_index,
        pad_active,
        pad_driven_manually,
        pad_skip_declaration,
        pad_mux_list,
        has_attribute,
        attribute_bits,
        constant_attribute,
        pad_layout,
        orient,
    ):
        """
        Initialize a Pad instance for template generation.

        This constructor is called by PadRing.build() to create template-facing
        pad representations from PadDef configuration objects.

        :param name: Pad name
        :param cell_name: Cell instance name
        :param pad_type: PadType enum
        :param pad_mapping: PadMapping enum (location on die)
        :param index: Physical pad index
        :param pad_layout_index: Layout ordering index
        :param pad_active: Active level ("high" or "low")
        :param pad_driven_manually: Whether manually driven
        :param pad_skip_declaration: Whether to skip declaration
        :param pad_mux_list: List of mux alternatives
        :param has_attribute: Whether pad has attributes
        :param attribute_bits: Attribute bit range string
        :param constant_attribute: Whether attributes are constant
        :param pad_layout: Layout object with dimensions
        :param orient: Orientation enum
        """

        self.name = name
        self.cell_name = cell_name
        self.index = index
        self.localparam = "PAD_" + name.upper()
        self.pad_type: str = pad_type.value
        self.pad_mapping = pad_mapping
        self.pad_mux_list = pad_mux_list
        if pad_active == "low":
            name_active = "n"
        else:
            name_active = ""

        self.signal_name = self.name + "_" + name_active

        self.has_attribute = has_attribute

        self.attribute_bits = (
            int(attribute_bits.split(":")[0]) - int(attribute_bits.split(":")[1]) + 1
        )
        self.constant_attribute = constant_attribute

        self.signal_name_drive = []
        self.pad_type_drive = []
        self.driven_manually = []
        self.skip_declaration = []
        self.keep_internal = []

        self.is_muxed = False

        self.is_driven_manually = pad_driven_manually
        self.do_skip_declaration = pad_skip_declaration

        self.layout_index = pad_layout_index
        self.layout_orient = orient.value.lower() if orient else orient
        self.layout_cell = (
            pad_layout.cell_pad.name if (pad_layout and pad_layout.cell_pad) else ""
        )
        self.layout_bondpad = (
            pad_layout.bond_pad.name if (pad_layout and pad_layout.bond_pad) else ""
        )
        self.layout_offset = pad_layout.offset if (pad_layout is not None) else ""
        self.layout_skip = pad_layout.skip if (pad_layout is not None) else ""

        if len(pad_mux_list) == 0:
            self.signal_name_drive.append(self.signal_name)
            self.pad_type_drive.append(pad_type.value)
            self.driven_manually.append(pad_driven_manually)
            self.skip_declaration.append(pad_skip_declaration)
        else:
            for pad_mux in pad_mux_list:
                self.signal_name_drive.append(pad_mux.signal_name)
                self.pad_type_drive.append(pad_mux.pad_type)
                self.driven_manually.append(pad_mux.is_driven_manually)
                self.skip_declaration.append(pad_mux.do_skip_declaration)

            self.is_muxed = True

        self.in_internal_signals = []
        self.out_internal_signals = []
        self.oe_internal_signals = []

        self.io_interface = self.signal_name + "io"

        ### Pad Ring ###
        self.pad_ring_io_interface = ""
        self.pad_ring_ctrl_interface = ""
        self.pad_ring_instance = ""

        ### core v mini mcu ###
        self.core_v_mini_mcu_interface = ""
        self.constant_driver_assign = ""
        self.mux_process = ""

        ### heep systems ###
        self.internal_signals = ""
        self.core_v_mini_mcu_bonding = ""
        self.pad_ring_bonding_bonding = ""
        self.x_heep_system_interface = ""
        if pad_mapping is None:
            self.pad_mapping = None
        elif isinstance(pad_mapping, PadMapping):
            self.pad_mapping = pad_mapping
        elif isinstance(pad_mapping, str):
            # accept "top", "TOP", etc.
            self.pad_mapping = PadMapping(pad_mapping.lower()) if pad_mapping else None
        else:
            raise TypeError(
                f"pad_mapping must be PadMapping | str | None, got {type(pad_mapping)}"
            )

    def __eq__(self, value):
        if not isinstance(value, Pad):
            return NotImplemented
        return vars(self) == vars(value)
