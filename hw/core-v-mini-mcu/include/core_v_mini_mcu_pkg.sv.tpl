/* Copyright 2018 ETH Zurich and University of Bologna.
 * Copyright and related rights are licensed under the Solderpad Hardware
 * License, Version 0.51 (the “License”); you may not use this file except in
 * compliance with the License.  You may obtain a copy of the License at
 * http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
 * or agreed to in writing, software, hardware and materials distributed under
 * this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 *
 *
 * Description: Contains common system definitions.
 *
 */

<%
  user_peripheral_domain = xheep.get_user_peripheral_domain()
  base_peripheral_domain = xheep.get_base_peripheral_domain()
  dma = base_peripheral_domain.get_dma()
  memory_ss = xheep.memory_ss()

  # Get DMA master index map
  dma_master_idx_map = xheep.ports.master_registry.get_dma_master_index_map(dma)
  count = xheep.ports.count()
%>

package core_v_mini_mcu_pkg;

  import addr_map_rule_pkg::*;
  import power_manager_pkg::*;

  typedef enum logic [1:0] {
    cv32e40p,
    cv32e20,
    cv32e40x,
    cv32e40px
  } cpu_type_e;

  localparam cpu_type_e CpuType = ${xheep.cpu().get_name()};

  typedef enum logic {
    NtoM,
    onetoM
  } bus_type_e;

  localparam bus_type_e BusType = ${xheep.bus_type().value};

  // Master port indices (auto-generated)
  localparam SYSTEM_XBAR_NMASTER = ${count['masters']};
% for master in xheep.ports.masters():
  localparam logic [31:0] ${master.name}_IDX = 32'd${master.index};
% endfor

% for port_type, idx_list in dma_master_idx_map.items():
  localparam logic [31:0] DMA_${port_type.upper()}_MASTER_IDXS [DMA_NUM_MASTER_PORTS] = '{
%   for value in idx_list:
    32'd${value}${"," if not loop.last else ""}
%   endfor
  };
% endfor

  // Internal slave memory map and index
  // -----------------------------------
  //must be power of two
  localparam int unsigned MEM_SIZE = 32'h${f'{memory_ss.ram_size_address():08X}'};

  localparam SYSTEM_XBAR_NSLAVE = ${count['slaves']};

  // all slaves ->

  localparam int unsigned LOG_SYSTEM_XBAR_NMASTER = SYSTEM_XBAR_NMASTER > 1 ? $clog2(SYSTEM_XBAR_NMASTER) : 32'd1;
  localparam int unsigned LOG_SYSTEM_XBAR_NSLAVE = SYSTEM_XBAR_NSLAVE > 1 ? $clog2(SYSTEM_XBAR_NSLAVE) : 32'd1;

  localparam int unsigned NUM_BANKS = ${memory_ss.ram_numbanks()};
  localparam int unsigned NUM_BANKS_IL = ${memory_ss.ram_numbanks_il()};
  localparam int unsigned EXTERNAL_DOMAINS = ${external_domains};

% for i, group in enumerate(memory_ss.iter_il_groups()):
  localparam logic [31:0] RAM_IL${i}_START_ADDRESS = 32'h${f'{group.start:08X}'};
  localparam logic [31:0] RAM_IL${i}_SIZE = 32'h${f'{group.size:08X}'};
  localparam logic [31:0] RAM_IL${i}_END_ADDRESS = RAM_IL${i}_START_ADDRESS + RAM_IL${i}_SIZE;
  localparam logic [31:0] RAM_IL${i}_IDX = RAM${group.first_name}_IDX;
% endfor

% for slave in xheep.ports.slaves():
  // Declaration of slave port ${slave.name}
  // --------------------------------------
  localparam logic [31:0] ${slave.name}_IDX = 32'd${slave.index}; 
  localparam logic [31:0] ${slave.name}_START_ADDRESS = 32'h${f'{slave.start_address:08X}'};
  localparam logic [31:0] ${slave.name}_SIZE = 32'h${f'{slave.size:08X}'};
  localparam logic [31:0] ${slave.name}_END_ADDRESS = ${slave.name}_START_ADDRESS + ${slave.name}_SIZE;

% endfor

  localparam addr_map_rule_t [SYSTEM_XBAR_NSLAVE-1:0] XBAR_ADDR_RULES = '{
% for slave in xheep.ports.slaves():
      '{ idx: ${slave.name}_IDX, start_addr: ${slave.name}_START_ADDRESS, end_addr: ${slave.name}_END_ADDRESS }${"," if not loop.last else ""}
% endfor
  };


  // External slave address map
  // --------------------------
  localparam logic [31:0] EXT_SLAVE_START_ADDRESS = 32'h${ext_slave_start_address};
  localparam logic [31:0] EXT_SLAVE_SIZE = 32'h${ext_slave_size_address};
  localparam logic [31:0] EXT_SLAVE_END_ADDRESS = EXT_SLAVE_START_ADDRESS + EXT_SLAVE_SIZE;

  // Forward crossbars address map and index
  // ---------------------------------------
  // These crossbar connect each muster to the internal crossbar and to the
  // corresponding external master port.
  localparam logic [31:0] DEMUX_XBAR_INT_SLAVE_IDX = 32'd0;
  localparam logic[31:0] DEMUX_XBAR_EXT_SLAVE_IDX = 32'd1;

  // Address map
  // NOTE: the internal address space is chosen by default by the system bus,
  // so it is not defined here.
  localparam addr_map_rule_t [0:0] DEMUX_XBAR_ADDR_RULES = '{
    '{
      idx: DEMUX_XBAR_EXT_SLAVE_IDX,
      start_addr: EXT_SLAVE_START_ADDRESS,
      end_addr: EXT_SLAVE_END_ADDRESS
    }
  };

######################################################################
## Automatically add all base peripherals listed
######################################################################
  // base peripherals
  // ---------------------

  localparam AO_PERIPHERALS = ${len(base_peripheral_domain.get_peripherals())};

  localparam int DMA_CH_NUM = ${dma.get_num_channels()};
  localparam DMA_CH_SIZE = 32'h${hex(dma.get_ch_length())[2:]};
  localparam int DMA_NUM_MASTER_PORTS = ${dma.get_num_master_ports()};

% if dma.get_num_master_ports() > 1:
  localparam int DMA_XBAR_MASTERS [DMA_NUM_MASTER_PORTS] = '{${dma.get_xbar_array()[::-1]}};
% else:
  localparam int DMA_XBAR_MASTERS [DMA_NUM_MASTER_PORTS] = '{${dma.get_xbar_array()}};
% endif

  localparam int DMA_FIFO_DEPTH = ${dma.get_fifo_depth()};

% for peripheral in base_peripheral_domain.get_peripherals():
  localparam logic [31:0] ${peripheral.get_name().upper()}_START_ADDRESS = AO_PERIPHERAL_START_ADDRESS + 32'h${hex(peripheral.get_address())[2:]};
  localparam logic [31:0] ${peripheral.get_name().upper()}_SIZE = 32'h${hex(peripheral.get_length())[2:]};
  localparam logic [31:0] ${peripheral.get_name().upper()}_END_ADDRESS = ${peripheral.get_name().upper()}_START_ADDRESS + ${peripheral.get_name().upper()}_SIZE;
  localparam logic [31:0] ${peripheral.get_name().upper()}_IDX = 32'd${loop.index};
% endfor

  localparam addr_map_rule_t [AO_PERIPHERALS-1:0] AO_PERIPHERALS_ADDR_RULES = '{
% for peripheral in base_peripheral_domain.get_peripherals():
      '{ idx: ${peripheral.get_name().upper()}_IDX, start_addr: ${peripheral.get_name().upper()}_START_ADDRESS, end_addr: ${peripheral.get_name().upper()}_END_ADDRESS }${"," if not loop.last else ""}
% endfor
  };

  localparam int unsigned AO_PERIPHERALS_PORT_SEL_WIDTH = AO_PERIPHERALS > 1 ? $clog2(AO_PERIPHERALS) : 32'd1;

  // Relative DMA channels addresses
% for i in range(dma.get_num_channels()):
  localparam logic [7:0] DMA_CH${i}_START_ADDRESS = 8'h${hex((dma.get_ch_length() * i) >> 8)[2:]};
  localparam logic [7:0] DMA_CH${i}_SIZE = 8'h${hex((dma.get_ch_length()) >> 8)[2:]};
  localparam logic [7:0] DMA_CH${i}_END_ADDRESS = DMA_CH${i}_START_ADDRESS + DMA_CH${i}_SIZE;
  localparam logic [7:0] DMA_CH${i}_IDX = 8'd${i};
% endfor

  localparam addr_map_rule_8bit_t [DMA_CH_NUM-1:0] DMA_ADDR_RULES = '{
% for i in range(dma.get_num_channels()):
      '{ idx: DMA_CH${i}_IDX, start_addr: DMA_CH${i}_START_ADDRESS, end_addr: DMA_CH${i}_END_ADDRESS }${"," if not loop.last else ""}
% endfor
  };
  
  localparam int unsigned DMA_CH_PORT_SEL_WIDTH = DMA_CH_NUM > 1 ? $clog2(DMA_CH_NUM) : 32'd1;

######################################################################
## Automatically add all user peripherals listed
######################################################################
  // user peripherals
  // -------------------------
  localparam int unsigned PERIPHERALS = ${len(user_peripheral_domain.get_peripherals())};
  localparam int unsigned PERIPHERALS_RND = (PERIPHERALS > 0) ? PERIPHERALS : 32'd1;

% for peripheral in user_peripheral_domain.get_peripherals():
  localparam logic [31:0] ${peripheral.get_name().upper()}_START_ADDRESS = PERIPHERAL_START_ADDRESS + 32'h${hex(peripheral.get_address())[2:]};
  localparam logic [31:0] ${peripheral.get_name().upper()}_SIZE = 32'h${hex(peripheral.get_length())[2:]};
  localparam logic [31:0] ${peripheral.get_name().upper()}_END_ADDRESS = ${peripheral.get_name().upper()}_START_ADDRESS + ${peripheral.get_name().upper()}_SIZE;
  localparam logic [31:0] ${peripheral.get_name().upper()}_IDX = 32'd${loop.index};
% endfor

% if len(user_peripheral_domain.get_peripherals()) == 0:
  localparam addr_map_rule_t [PERIPHERALS_RND-1:0] PERIPHERALS_ADDR_RULES = '0;
% else:
  localparam addr_map_rule_t [PERIPHERALS_RND-1:0] PERIPHERALS_ADDR_RULES = '{
% for peripheral in user_peripheral_domain.get_peripherals():
      '{ idx: ${peripheral.get_name().upper()}_IDX, start_addr: ${peripheral.get_name().upper()}_START_ADDRESS, end_addr: ${peripheral.get_name().upper()}_END_ADDRESS }${"," if not loop.last else ""}
% endfor
  };
% endif

  localparam int unsigned PERIPHERALS_PORT_SEL_WIDTH = PERIPHERALS > 1 ? $clog2(PERIPHERALS) : 32'd1;

  // Interrupts
  // ----------
  localparam PLIC_NINT = ${plit_n_interrupts};
  localparam PLIC_USED_NINT = ${plic_used_n_interrupts};
  localparam NEXT_INT = PLIC_NINT - PLIC_USED_NINT;

% for pad in xheep.get_padring().total_pad_list:
  localparam ${pad.localparam} = ${pad.index};
% endfor

  localparam NUM_PAD = ${xheep.get_padring().total_pad};
  localparam NUM_PAD_MUXED = ${xheep.get_padring().total_pad_muxed};

  localparam int unsigned NUM_PAD_PORT_SEL_WIDTH = NUM_PAD > 1 ? $clog2(NUM_PAD) : 32'd1;

  typedef enum logic [1:0] {
    TOP,
    RIGHT,
    BOTTOM,
    LEFT
  } pad_side_e;

endpackage
