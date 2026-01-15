// Copyright 2022 EPFL
// Solderpad Hardware License, Version 2.1, see LICENSE.md for details.
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
<%
    # Pad type configuration for signal generation
    # Maps pad types to their control interface generators and connection patterns
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
                ("pad_out_o", ""),
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

    # Mapping for pad side parameters
    MAPPING_DICT = {
        "top": "core_v_mini_mcu_pkg::TOP",
        "right": "core_v_mini_mcu_pkg::RIGHT",
        "bottom": "core_v_mini_mcu_pkg::BOTTOM",
        "left": "core_v_mini_mcu_pkg::LEFT",
    }
%>\
<%def name="gen_pad_io_interface(pad)">\
    inout wire ${pad.io_interface},</%def>\
<%def name="gen_pad_ctrl_interface(pad)">\
<%
    sig = pad.signal_name
    pad_type_key = pad.pad_type.split("_")[-1]
    if pad_type_key in PAD_TYPE_CONFIG:
        result = PAD_TYPE_CONFIG[pad_type_key]["ctrl_interface"](sig)
    else:
        result = ""
%>\
${result}</%def>\
<%def name="gen_pad_instance(pad)">\
<%
    sig = pad.signal_name
    pad_type_key = pad.pad_type.split("_")[-1]

    # Build mapping string
    if pad.pad_mapping:
        mapping_key = pad.pad_mapping.value if hasattr(pad.pad_mapping, 'value') else str(pad.pad_mapping).lower()
        mapping = f", .SIDE({MAPPING_DICT.get(mapping_key, '')})"
    else:
        mapping = ""

    # Parameter string
    param_str = f"#(.PADATTR({pad.attribute_bits}){mapping})"

    if pad_type_key in PAD_TYPE_CONFIG:
        config = PAD_TYPE_CONFIG[pad_type_key]
        cell = config["cell"]
        connections = config["connections"](sig)

        # Build connection lines
        conn_lines = []
        for port, signal in connections:
            if signal:
                conn_lines.append(f"   .{port}({signal}),")
            else:
                conn_lines.append(f"   .{port}(),")
        conns = "\n".join(conn_lines) + "\n"

        # Build attribute line
        if pad.has_attribute:
            attr_line = f"   .pad_attributes_i(pad_attributes_i[core_v_mini_mcu_pkg::{pad.localparam}])\n);\n"
        else:
            attr_line = "   .pad_attributes_i('0));\n"

        instance = f"{cell} {param_str} {pad.cell_name} ( \n{conns}{attr_line}"
    else:
        instance = ""
%>\
${instance}</%def>\

module pad_ring (
% for pad in xheep.get_padring().pad_list:
${gen_pad_io_interface(pad)}
${gen_pad_ctrl_interface(pad)}
% endfor

% for external_pad in xheep.get_padring().external_pad_list:
${gen_pad_io_interface(external_pad)}
${gen_pad_ctrl_interface(external_pad)}
% endfor

% if xheep.get_padring().pads_attributes != None:
    input logic [core_v_mini_mcu_pkg::NUM_PAD-1:0][${xheep.get_padring().pads_attributes['bits']}] pad_attributes_i
% else:
    // here just for simplicity
    /* verilator lint_off UNUSED */
    input logic [core_v_mini_mcu_pkg::NUM_PAD-1:0][0:0] pad_attributes_i
% endif

);

% for pad in xheep.get_padring().pad_list:
${gen_pad_instance(pad)}
% endfor

% for external_pad in xheep.get_padring().external_pad_list:
${gen_pad_instance(external_pad)}
% endfor

endmodule  // pad_ring
