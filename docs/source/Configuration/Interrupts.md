# X-HEEP Interrupts Guide

Manage up to **64 interrupts** (IDs 0-63) connecting peripherals to the RISC-V PLIC.

## Interrupt Class Reference

```python
Interrupt(
    id,              # Interrupt ID (0-63) - REQUIRED
    num=1,           # Number of sequential interrupts (default: 1)
    start_seq=None,  # Starting sequence number (auto-set for single interrupts)
    peripheral=None, # Peripheral name (e.g., "uart")
    name=None,       # Interrupt name (e.g., "gpio_intr")
)
```

### Fields

### Fields

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Interrupt ID | `1` |
| `num` | Count (for multi-interrupt peripherals) | `1` or `24` |
| `start_seq` | Sequence start (multi-interrupts only) | `8` |
| `peripheral` | Peripheral name | `"uart"` |
| `name` | Interrupt name | `"gpio_intr"` |

---

## Adding Interrupts

### Single Interrupt Peripheral

```python
# File: util/x_heep_gen/peripherals/user_peripherals/MY_PERIPH.py
from ..abstractions import UserPeripheral, Interrupt

class MY_PERIPH(UserPeripheral):
    _name = "my_periph"
    _interrupts = [
        Interrupt(51, peripheral="MY_PERIPH", name="myperiph_intr_event1"),
        Interrupt(52, peripheral="MY_PERIPH", name="myperiph_intr_event2"),
    ]
```

### Multi-Interrupt Peripheral (e.g., GPIO)

```python
class GPIO(UserPeripheral):
    _name = "gpio"
    _interrupts = [
        Interrupt(
            id=9,          # Starting ID
            num=24,        # 24 interrupts
            start_seq=8,   # Pins 8-31
            peripheral="GPIO",
            name="gpio_intr"
        )
    ]
```

Expands to: `gpio_intr_8` (ID 9), `gpio_intr_9` (ID 10), ..., `gpio_intr_31` (ID 32)

### Register & Configure

1. **Add to config:**
   ```python
   # File: configs/general.py
   from x_heep_gen.peripherals.user_peripherals import MY_PERIPH

   user_domain.add_peripheral(MY_PERIPH(0x00090000))
   ```

---

## Using in Software

### Generated Header

```c
// sw/device/lib/runtime/core_v_mini_mcu.h
#define QTY_INTR 64

#define UART_INTR_TX_WATERMARK 1
#define GPIO_INTR_8 9
#define I2C_INTR_FMT_WATERMARK 33
```
---

## Notes

- **Max 64 interrupts** system-wide
- **ID 0** reserved for `null_intr` (always tied to zero)
- **External interrupts** use remaining IDs after peripheral allocation
- **HJSON format** unchanged - parsing converts to nested structure internally
