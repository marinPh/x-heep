# Masters and Slaves - Quick Guide

## How Masters Work

### Automatic Registration from Peripherals

When you create a peripheral with master ports, define them in `__init__`:

```python
from util.x_heep_gen.peripherals.abstractions import BasePeripheral

class MyAccelerator(BasePeripheral):
    _name = "my_accelerator"

    def __init__(self, address=None, length=None):
        super().__init__(address, length)

        # Add master port specification
        self.add_master_port_spec(
            name="ACCEL_MASTER",
            port_type="axi",
            port_index=0
        )
```

When you add the peripheral to a domain, the master is automatically registered:

```python
base_domain.add_peripheral(MyAccelerator())
# The ACCEL_MASTER is now registered in the bus system
```

### Manual Registration

For masters not tied to a peripheral:

```python
xheep.ports.add_master("CUSTOM_MASTER", port_type="axi")
```

## How Slaves Work

### Automatic Registration

Peripheral domains are automatically registered as slaves during `build()`:

- `ERROR` - Error slave (always at index 0)
- `RAM_BANK_0`, `RAM_BANK_1`, ... - Memory banks
- `AO_PERIPHERAL` - Base peripheral domain
- `PERIPHERAL` - User peripheral domain

### Manual Registration

For custom memory regions:

```python
xheep.ports.add_slave("DEBUG", start=0x1A110000, size=0x00008000)
xheep.ports.add_slave("FLASH_MEM", start=0x40000000, size=0x00400000)
```

## Understanding port_index

The `port_index` groups masters belonging to the same physical port. This is needed for peripherals with multiple ports.

**Example: DMA with 2 ports, each having read/write masters**

```python
class MyDMA(BasePeripheral):
    def __init__(self, num_ports=2):
        super().__init__()

        for i in range(num_ports):
            self.add_master_port_spec(f"DMA_READ_P{i}", "read", port_index=i)
            self.add_master_port_spec(f"DMA_WRITE_P{i}", "write", port_index=i)
```

This creates:
- `DMA_READ_P0` (port_index=0) and `DMA_WRITE_P0` (port_index=0) - belong to port 0
- `DMA_READ_P1` (port_index=1) and `DMA_WRITE_P1` (port_index=1) - belong to port 1

The system generates arrays for easy wiring:
```systemverilog
localparam DMA_READ_MASTER_IDXS[2] = '{5, 6};   // read[0]=5, read[1]=6
localparam DMA_WRITE_MASTER_IDXS[2] = '{7, 8};  // write[0]=7, write[1]=8

// Map peripheral arrays to bus
for (genvar i = 0; i < 2; i++) begin
    assign int_master_req[DMA_READ_MASTER_IDXS[i]] = dma_read_req_i[i];
    assign int_master_req[DMA_WRITE_MASTER_IDXS[i]] = dma_write_req_i[i];
end
```

**Two different indices:**
- `port_index` - Peripheral's local port number (0, 1, 2, ...)
- `master.index` - Global bus master ID (assigned during build)

**When to use port_index:**
- ✅ Multiple physical ports: `for i in range(num_ports): add_master_port_spec(..., port_index=i)`
- ❌ Single port: just use `port_index=0`

## Common Patterns

### Single Master Peripheral

```python
class SimpleAccelerator(BasePeripheral):
    _name = "accelerator"

    def __init__(self):
        super().__init__()
        self.add_master_port_spec("ACCEL_MASTER", "axi", port_index=0)
```

### Multi-Port Peripheral

```python
class MultiPortDMA(BasePeripheral):
    _name = "multi_dma"

    def __init__(self, num_ports=2):
        super().__init__()
        for i in range(num_ports):
            self.add_master_port_spec(f"DMA_READ_P{i}", "read", i)
            self.add_master_port_spec(f"DMA_WRITE_P{i}", "write", i)
```

## Complete Example

```python
from x_heep_gen.xheep import XHeep
from x_heep_gen.bus_type import BusType
from x_heep_gen.peripherals.base_peripherals_domain import BasePeripheralDomain

# Create system
xheep = XHeep(BusType.NtoM)

# Create domain and add peripheral
base_domain = BasePeripheralDomain(master_registry=xheep.master_registry)
base_domain.add_peripheral(MyAccelerator())  # Masters auto-registered
xheep.add_peripheral_domain(base_domain)

# Add custom slave
xheep.ports.add_slave("FLASH_MEM", start=0x40000000, size=0x00400000)

# Build system
xheep.build()

# Query
master = xheep.ports.master("ACCEL_MASTER")
slave = xheep.ports.slave("FLASH_MEM")
print(f"Master at bus index: {master.index}")
print(f"Slave at: 0x{slave.start_address:08X}")
```

## Querying

```python
# Get single port
master = xheep.ports.master("DMA_READ_P0")
slave = xheep.ports.slave("FLASH_MEM")

# Get all ports
for master in xheep.ports.masters():
    print(f"{master.name}: index={master.index}")

for slave in xheep.ports.slaves():
    print(f"{slave.name}: 0x{slave.start_address:08X}")

# Get masters from specific peripheral
accel_masters = xheep.ports.masters_by_owner(my_peripheral)
```

## Key Differences

| Aspect | Masters | Slaves |
|--------|---------|--------|
| **Automatic parsing** | Via `master_specs` in peripheral | No automatic parsing from peripherals |
| **How to add** | `add_master_port_spec()` in `__init__` | `add_slave()` for custom regions |
| **Peripheral level** | Each peripheral can have multiple | Peripherals share domain's address space |
| **When registered** | When peripheral added to domain | During `build()` for domains |

## Troubleshooting

**Masters not showing up?**
1. Check peripheral was added: `base_domain.add_peripheral(my_periph)`
2. Check domain has registry: `BasePeripheralDomain(master_registry=xheep.master_registry)`
3. Verify specs populated: `print(my_periph.master_specs)`

**Slave address conflicts?**
- Use `xheep.ports.slaves()` to see all registered slaves and check for overlaps

**Query masters from a peripheral?**
```python
dma = base_domain.get_peripherals()[0]
dma_masters = xheep.ports.masters_by_owner(dma)
```
