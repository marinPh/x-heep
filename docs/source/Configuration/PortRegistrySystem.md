# Port Registry System

## Introduction

The **Port Registry System** provides centralized management of all master and slave ports on the X-HEEP system bus. The system automatically assigns sequential indices to all ports and provides a clean API for querying port information in templates and Python code.

**What it provides:**
- **Custom master ports** - Declare additional master ports in hjson or Python
- **Automatic indexing** - Sequential indices (0, 1, 2, ...) assigned at build time
- **Type-safe queries** - Get port information by name or iterate over all ports
- **Validation** - Ensures no duplicates, gaps, or missing required ports

**Use cases:**
- Adding custom master-capable peripherals (e.g., AXI bridges, stream processors)
- Template code that needs port counts and indices
- Debugging bus connections with registry dumps

## Architecture

### Two-Phase Lifecycle

The registry operates in two distinct phases:

**Phase 1: Configuration Time** - Ports are registered as the system is configured
```python
XHeep.__init__()
  → master_registry.register_fixed_masters()     # CPU, debug masters
  → slave_registry (created empty)

domain.add_peripheral(peripheral)
  → master_registry.register_peripheral_masters(peripheral)  # Auto-discovers masters

xheep.register_template_slaves(...)              # Fixed system slaves
```

**Phase 2: Build Time** - Registries finalize all registrations
```python
xheep.build()
  → master_registry.build()
      → Sort masters (fixed first, then by owner/type/name)
      → Assign sequential indices (0, 1, 2, ...)
      → Validate (no duplicates, all required masters present)
  → slave_registry.build()
      → Sort slaves (ERROR, RAM banks, fixed slaves, custom)
      → Assign sequential indices
      → Validate
```

### Class Hierarchy

```
PortRegistry (abstract base)
    ├── MasterRegistry
    └── SlaveRegistry

MasterPort (data class)
SlavePort (data class)
```

The system uses the **Template Method pattern**: `PortRegistry` provides common registration and query logic, while subclasses define sorting order and validation rules via `_sort_key()` and `_validate()`.

## Master Port System

### Three Declaration Methods

#### 1. Implicit Declaration (Built-in Support)

The DMA peripheral has built-in master port support via `num_master_ports`:

```hjson
dma: {
  num_master_ports: 0x2  // Creates 6 OBI masters (2 read, 2 write, 2 addr)
}
```

This automatically creates master ports: `DMA_READ_P0`, `DMA_READ_P1`, `DMA_WRITE_P0`, `DMA_WRITE_P1`, `DMA_ADDR_P0`, `DMA_ADDR_P1`.

#### 2. Explicit Declaration in HJSON

Declare custom master ports at global or peripheral level:

```hjson
// Global master ports
master_ports: [
  { name: "EXT_AXI_MASTER", type: "axi" },
  { name: "CUSTOM_INTERFACE", type: "custom" }
]

// Peripheral-level master ports
peripherals: {
  gpio_ao: {
    master_ports: [
      { name: "GPIO_STREAM_OUT", type: "stream", index: 0 }
    ]
  }
}
```

#### 3. Programmatic Declaration (Python API)

Add master ports dynamically in Python:

```python
# Global masters
xheep.add_global_master_port("DEBUG_TRACE", "trace")

# Peripheral masters
peripheral.add_master_port_spec("ACCEL_OUTPUT", "stream", 0)
```

### Master Port Ordering

Masters are sorted before index assignment:

1. **Fixed masters** (CPU, debug) - alphabetically
   - Index 0: `CORE_DATA`
   - Index 1: `CORE_INSTR`
   - Index 2: `DEBUG_MASTER`

2. **Custom/Global masters** - by name

3. **Peripheral masters** - by owner name, then port type, then name
   - DMA masters: `DMA_ADDR_P0`, `DMA_ADDR_P1`, `DMA_READ_P0`, etc.

### Template Usage

Templates access master registry data:

```systemverilog
// Total master count
localparam int unsigned SYSTEM_XBAR_NMASTER = ${xheep.master_registry.get_total_count()};

// Iterate over all masters
% for master in xheep.master_registry.get_all():
  // Master ${master.index}: ${master.name}
% endfor

// DMA-specific index map
<%
  dma_idx_map = xheep.master_registry.get_dma_master_index_map(dma)
%>
localparam int unsigned DMA_READ_MASTER_IDXS [${len(dma_idx_map["read"])}] = '{${", ".join(map(str, dma_idx_map["read"]))}};
```

## Slave Port System

### Overview

The slave registry manages all slave ports on the system bus, including ERROR handlers, RAM banks, and fixed system slaves. It eliminates the hardcoded `+ 5` magic number by providing a centralized registry with automatic index assignment.

### Slave Port Structure

Each `SlavePort` contains:
- **name**: Unique identifier (e.g., "DEBUG", "RAM0", "PERIPHERAL")
- **start_address**: Start address in memory map
- **size**: Size of address space in bytes
- **end_address**: Calculated as start_address + size
- **owner**: Owner object (None for fixed slaves, Bank object for RAM)
- **index**: Auto-assigned during build (sequential: 0, 1, 2, ...)

### Fixed Slave Ports

The slave registry manages all slave ports with automatic index assignment:

**Ordering:**
1. **ERROR** (always index 0) - Invalid access target at `0xBADACCE5`
2. **RAM banks** (indices 1..N) - Sorted by bank name (RAM0, RAM1, ...)
3. **Fixed system slaves** - Alphabetically
   - `AO_PERIPHERAL` - Always-on peripheral domain
   - `DEBUG` - Debug module
   - `FLASH_MEM` - Flash memory
   - `PERIPHERAL` - User peripheral domain

**Example with 2 RAM banks:**

```
Index  Name            Address Range
  0    ERROR           0xBADACCE5 - 0xBADACCE6
  1    RAM0            0x00000000 - 0x00008000  (32KB)
  2    RAM1            0x00008000 - 0x00010000  (32KB)
  3    AO_PERIPHERAL   0x20000000 - 0x20100000
  4    DEBUG           0x1A110000 - 0x1A118000
  5    FLASH_MEM       0x40000000 - 0x40400000
  6    PERIPHERAL      0x30000000 - 0x30100000
```

Total slaves: 7

### Registration

Slaves are registered during system build through `xheep.register_template_slaves()`:

```python
# Called from mcu_gen.py before xheep.build()
xheep.register_template_slaves(
    debug_start=0x1A110000,
    debug_size=0x00008000,
    flash_start=0x40000000,
    flash_size=0x00400000,
)
```

Internally this calls:

```python
# Step 1: Register fixed slaves (ERROR, DEBUG, AO_PERIPHERAL, PERIPHERAL, FLASH_MEM)
slave_registry.register_fixed_slaves(
    memory_ss=memory_ss,
    debug_start=debug_start,
    debug_size=debug_size,
    ao_peripheral_start=base_peripheral_domain.start_address,
    ao_peripheral_size=base_peripheral_domain.length,
    peripheral_start=user_peripheral_domain.start_address,
    peripheral_size=user_peripheral_domain.length,
    flash_start=flash_start,
    flash_size=flash_size,
)

# Step 2: Register RAM banks from memory subsystem
slave_registry.register_ram_banks(memory_ss)  # RAM0, RAM1, RAM2, ...
```

### Template Usage

**Getting the total number of slaves:**

```systemverilog
localparam int unsigned SYSTEM_XBAR_NSLAVE = ${xheep.slave_registry.get_total_count()};
```

**Querying slaves by name:**

```systemverilog
<%
  # Get slave objects by name
  debug_slave = xheep.slave_registry.get_by_name("DEBUG")
  ao_periph_slave = xheep.slave_registry.get_by_name("AO_PERIPHERAL")
  periph_slave = xheep.slave_registry.get_by_name("PERIPHERAL")
  flash_slave = xheep.slave_registry.get_by_name("FLASH_MEM")
%>

// Access slave properties
assign master_start_addr[${debug_slave.index}] = 32'h${format(debug_slave.start_address, '08X')};
assign master_end_addr[${debug_slave.index}] = 32'h${format(debug_slave.end_address, '08X')};

assign master_start_addr[${ao_periph_slave.index}] = 32'h${format(ao_periph_slave.start_address, '08X')};
assign master_end_addr[${ao_periph_slave.index}] = 32'h${format(ao_periph_slave.end_address, '08X')};
```

### Iterating Over All Slaves

Templates can iterate over slaves for array generation:

```systemverilog
// Generate start address array
% for slave in xheep.slave_registry.get_all():
assign master_start_addr[${slave.index}] = 32'h${format(slave.start_address, '08X')};  // ${slave.name}
% endfor

// Or build arrays directly
localparam logic [31:0] SLAVE_START_ADDRS[SYSTEM_XBAR_NSLAVE] = '{
% for slave in xheep.slave_registry.get_all():
  32'h${format(slave.start_address, '08X')}${"," if not loop.last else ""}  // [${slave.index}] ${slave.name}
% endfor
};
```

### Validation

The slave registry validates at build time:

1. **ERROR slave exists** and is at index 0
2. **Sequential indices** - No gaps (0, 1, 2, ..., N-1)
3. **No duplicate names** - Each slave has unique identifier
4. **Address consistency** - Each slave has valid start_address and size

If validation fails, `xheep.build()` raises a `ValueError` with a clear error message.

## Adding Master Ports to Custom Peripherals

To add master port support to a custom peripheral:

```python
class MyPeripheral(Peripheral):
    def __init__(self, ...):
        super().__init__(...)
        self.master_specs = []  # Initialize empty list

        # Add master port specifications
        self.add_master_port_spec("MY_PERIPH_READ", "read", 0)
        self.add_master_port_spec("MY_PERIPH_WRITE", "write", 0)
```

The registry will automatically create `MasterPort` objects when the peripheral is added to a domain.

**In templates:**

```systemverilog
<%
  my_periph_masters = xheep.master_registry.get_by_owner(my_peripheral)
%>
// Connect peripheral master ports
% for master in my_periph_masters:
assign xbar_master_req[${master.index}] = ${master.owner.get_name()}_${master.port_type}_req;
% endfor
```

## Python API Reference

### MasterRegistry

```python
# Configuration time
master_registry.register_fixed_masters()
master_registry.register_from_spec(spec, owner=None)
master_registry.register_peripheral_masters(peripheral)

# Build time
master_registry.build()

# Query time (after build)
master_registry.get_total_count() -> int
master_registry.get_all() -> List[MasterPort]
master_registry.get_by_name(name) -> Optional[MasterPort]
master_registry.get_fixed_masters() -> List[MasterPort]
master_registry.get_peripheral_masters() -> List[MasterPort]
master_registry.get_by_owner(peripheral) -> List[MasterPort]
master_registry.get_dma_master_index_map(dma) -> dict
```

### SlaveRegistry

**Configuration Time API:**

```python
# Register fixed system slaves
slave_registry.register_fixed_slaves(
    memory_ss,                  # MemorySS object (for RAM bank count)
    debug_start: int,           # Debug module start address
    debug_size: int,            # Debug module size
    ao_peripheral_start: int,   # AO peripheral domain start
    ao_peripheral_size: int,    # AO peripheral domain size
    peripheral_start: int,      # User peripheral domain start
    peripheral_size: int,       # User peripheral domain size
    flash_start: int,           # Flash memory start
    flash_size: int             # Flash memory size
)

# Register RAM banks from memory subsystem
slave_registry.register_ram_banks(memory_ss)

# Manually register a slave (advanced usage)
slave_registry.register(SlavePort(name, start_addr, size, owner))
```

**Build Time:**

```python
slave_registry.build()  # Sort, assign indices, validate
```

**Query Time API (after build):**

```python
# Get total slave count
total: int = slave_registry.get_total_count()

# Get all slaves in index order
all_slaves: List[SlavePort] = slave_registry.get_all()

# Get specific slave by name
debug: Optional[SlavePort] = slave_registry.get_by_name("DEBUG")
ram0: Optional[SlavePort] = slave_registry.get_by_name("RAM0")

# Get only fixed slaves (no owner)
fixed: List[SlavePort] = slave_registry.get_fixed_ports()

# Debug output
slave_registry.dump()  # Print registry contents
```

**SlavePort Properties:**

```python
slave = slave_registry.get_by_name("DEBUG")

slave.name            # "DEBUG"
slave.index           # Auto-assigned (e.g., 4)
slave.start_address   # e.g., 0x1A110000
slave.size            # e.g., 0x00008000
slave.end_address     # Calculated: start_address + size
slave.owner           # None for fixed slaves, Bank object for RAM
slave.is_fixed()      # True if owner is None
slave.is_peripheral() # True if owner is not None
```

### XHeep Methods

```python
# Add global master port
xheep.add_global_master_port(name: str, port_type: str = "custom")

# Register template slaves (called once during build)
xheep.register_template_slaves(
    debug_start: int,
    debug_size: int,
    flash_start: int,
    flash_size: int
)
```

## Key Features

### Automatic Index Assignment

All ports receive sequential indices (0, 1, 2, ...) during the build phase. You never need to manually calculate or track indices.

### Type-Safe Queries

Access ports by name with full type information:
- `get_by_name("DEBUG")` returns SlavePort with address, size, index
- `get_by_owner(peripheral)` returns all MasterPorts for a peripheral
- `get_all()` returns all ports in index order

### Validation

The system validates at build time:
- No duplicate port names
- Sequential indices (no gaps)
- Required ports present (ERROR slave at index 0, CPU masters, etc.)
- Valid address ranges for slaves

### Extensibility

- Add custom master ports via hjson configuration
- Peripherals can declare master ports in their `__init__`
- Clean factory pattern: specs (dicts) separate from objects (MasterPort/SlavePort)

### Debugging

Both registries provide `dump()` methods to print all registered ports:

```python
xheep.master_registry.dump()  # Print all masters
xheep.slave_registry.dump()   # Print all slaves
```

## Example Configuration

```hjson
{
  bus_type: "NtoM",

  master_ports: [
    { name: "EXT_AXI_MASTER", type: "axi" },
    { name: "TRACE_PORT", type: "trace" }
  ],

  peripherals: {
    dma: {
      num_master_ports: 0x2,  // Built-in: 6 masters (read/write/addr × 2)
    },

    gpio_ao: {
      master_ports: [
        { name: "GPIO_STREAM", type: "stream", index: 0 }
      ]
    }
  }
}
```

This configuration creates:
- 3 fixed masters (CORE_DATA, CORE_INSTR, DEBUG_MASTER)
- 2 global masters (EXT_AXI_MASTER, TRACE_PORT)
- 6 DMA masters (DMA_ADDR_P0/P1, DMA_READ_P0/P1, DMA_WRITE_P0/P1)
- 1 GPIO master (GPIO_STREAM)

**Total: 12 masters** with indices automatically assigned 0-11.
