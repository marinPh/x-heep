import re
import numpy as np
from copy import deepcopy
from typing import Dict, List, Tuple
from ..peripherals.abstractions import Interrupt, PeripheralDomain

DEFAULT_MAX_INTERRUPTS = 64


class InterruptManager:

    def __init__(self):
        """
        Initialize the InterruptManager.

        :param int max_interrupts: Maximum number of interrupts supported
        """
        self._interrupts: Dict[str, Interrupt] = {}
        self._max_interrupts = DEFAULT_MAX_INTERRUPTS

    # ================================================================
    # Core Assignment Methods
    # ================================================================

    def assign_from_peripheral_domains(self, base_domain, user_domain):

        # Collect all interrupt IDs from both domains
        all_ids = [i.id for i in self._interrupts.values()]

        # Check no 2 peripherals have the same interrupt ID
        set_ids = set(all_ids)
        if len(all_ids) != len(set_ids):
            raise ValueError("Two peripherals have the same interrupt id")

        possible_ids = list(set(range(0, self._max_interrupts)).difference(set_ids))
        # Get predefined interrupts map for validation error messages
        predefined_map = self._collect_predefined_interrupts_map(
            base_domain, user_domain
        )

        # Assign interrupts from base peripheral domain (with validation)
        self._assign_interrupts_from_domain(
            base_domain,
            possible_ids,
            validate=True,
            predefined_map=predefined_map,
        )

        # Assign interrupts from user peripheral domain (without validation)
        self._assign_interrupts_from_domain(user_domain, possible_ids, validate=False)

        # add external interrupts

        external_interrupts = {
            f"EXT_INTR_{i}": Interrupt(id=id, num=1, peripheral="external")
            for i, id in enumerate(possible_ids)
        }
        for name, irq in external_interrupts.items():
            self.add_interrupt(name, irq)

        # Sort interrupts by ID for consistent ordering
        self._interrupts = dict(
            sorted(self._interrupts.items(), key=lambda item: item[1].id)
        )

    def add_interrupt(self, name: str, irq: Interrupt):
        if not isinstance(name, str):
            raise TypeError(f"interrupt name should be of type str not {type(name)}")

        if irq is not None and not isinstance(irq, Interrupt):
            raise TypeError(f"irq should be of type Interrupt not {type(irq)}")

        if name in self._interrupts:
            return

        if irq is not None and irq in self._interrupts.values():
            raise ValueError(f"Interrupt IRQ {irq} already exists in the system")

        self._interrupts[name] = irq

    def extend_interrupts(self, interrupts: Dict[str, Interrupt]):
        for name, irq in interrupts.items():
            if name not in self._interrupts:
                self._interrupts[name] = irq

    # ================================================================
    # Query Methods
    # ================================================================

    def get_interrupts(self) -> Dict[str, Interrupt]:

        return deepcopy(self._interrupts)

    def get_num_interrupts(self) -> int:
        return int(
            np.array(
                [
                    irq.num
                    for name, irq in self._interrupts.items()
                    if not name.startswith("EXT_")
                ]
            ).sum()
        )

    def get_interrupts_for_peripheral(
        self, peripheral_name: str
    ) -> Dict[str, Interrupt]:

        result = {}

        # I2C interrupt names in hjson (special case - no peripheral prefix)
        # This is a legacy naming convention that needs to be preserved
        i2c_interrupt_names = [
            "fmt_watermark",
            "rx_watermark",
            "fmt_overflow",
            "rx_overflow",
            "nak",
            "scl_interference",
            "sda_interference",
            "stretch_timeout",
            "sda_unstable",
            "trans_complete",
            "tx_empty",
            "tx_nonempty",
            "tx_overflow",
            "acq_overflow",
            "ack_stop",
            "host_timeout",
        ]

        for name, irq in self._interrupts.items():
            # Standard case: peripheral_intr_* pattern
            if name.startswith(f"{peripheral_name}_intr_"):
                result[name] = irq
            # Handle I2C special case (interrupts start with 'intr_' but belong to i2c)
            elif peripheral_name == "i2c" and name.startswith("intr_"):
                # Check if it's one of the known I2C interrupts
                if any(pattern in name for pattern in i2c_interrupt_names):
                    result[name] = irq

        return result

    def get_simple_interrupts(self) -> Dict[str, int]:

        temp = dict()
        for name, irq in self._interrupts.items():
            if irq.num > 1:
                # Multi-interrupt: expand into individual entries
                cnt = irq.id
                for i in range(irq.start_seq, irq.start_seq + irq.num):
                    temp[f"{name}_{i}"] = cnt
                    cnt += 1
            else:
                # Single interrupt: direct mapping
                temp[name] = irq.id
        return temp

    def get_peripheral_interrupt_connections(
        self, peripheral_name: str
    ) -> List[Tuple[str, str]]:

        interrupts = self.get_interrupts_for_peripheral(peripheral_name)
        connections = []

        for intr_name, irq in interrupts.items():
            # Extract the interrupt-specific part (after peripheral prefix)
            if intr_name.startswith(f"{peripheral_name}_intr_"):
                # Standard case: uart_intr_tx_watermark -> intr_tx_watermark_o
                intr_suffix = intr_name.replace(f"{peripheral_name}_intr_", "")
                port_name = f"intr_{intr_suffix}_o"
                signal_name = intr_name
            # Handle I2C special case: intr_fmt_watermark -> intr_fmt_watermark_o, i2c_intr_fmt_watermark
            elif peripheral_name == "i2c" and intr_name.startswith("intr_"):
                port_name = f"{intr_name}_o"
                signal_name = f"i2c_{intr_name}"
            else:
                continue

            connections.append((port_name, signal_name))

        # Sort by port name for consistent output
        connections.sort(key=lambda x: x[0])

        return connections

    # ================================================================
    # Configuration Methods
    # ================================================================

    def set_max_intrs(self, max_interrupts: int):
        """
        Set the maximum number of interrupts supported.

        :param int max_interrupts: Maximum number of interrupts
        """
        self._max_interrupts = max_interrupts

    def set_interrupts(self, interrupts: Dict[str, int]):
        """
        Replace all interrupts with a new set.

        WARNING: This clears all existing interrupts.

        :param Dict[str,int] interrupts: New interrupt dictionary
        :raises TypeError: If interrupts is not a dictionary

        Example:
            >>> manager.set_interrupts({"uart_tx": 5, "uart_rx": 6})
        """
        if not isinstance(interrupts, dict):
            raise TypeError(
                f"interrupts should be of type Dict[str,int] not {type(interrupts)}"
            )
        self._interrupts = interrupts.copy()

    # ================================================================
    # Internal Helper Methods (Private)
    # ================================================================

    def _collect_interrupt_ids_from_domains(self, *domains) -> List[int]:
        """
        Collect all predefined interrupt IDs from multiple peripheral domains.

        Only collects IDs from interrupts that have been explicitly assigned
        (i.e., irq is not None and irq.id is not None).

        :param domains: Variable number of peripheral domains
        :return: List of all predefined interrupt IDs
        :rtype: List[int]
        """
        all_ids = []
        for domain in domains:
            all_ids.extend(
                [
                    irq.id
                    for peri in domain.get_peripherals()
                    for irq in peri.get_interrupts().values()
                    if irq is not None and irq.id is not None
                ]
            )
        return all_ids

    def _collect_predefined_interrupts_map(self, *domains) -> Dict[int, str]:
        result = {}
        for domain in domains:
            for peri in domain.get_peripherals():
                for name, irq in peri.get_interrupts().items():
                    if irq is not None and irq.id is not None:
                        result[irq.id] = name
        return result

    def _assign_interrupts_from_domain(
        self,
        domain: PeripheralDomain,
        possible_ids,
        validate=False,
        predefined_map=None,
    ):
        for peri in domain.get_peripherals():
            for name, irq in peri.get_interrupts().items():
                if irq is None:
                    # No predefined ID: allocate from available pool
                    assigned_id = possible_ids.pop(0)
                    self.add_interrupt(
                        name, Interrupt(assigned_id, peripheral=peri._name)
                    )
                else:
                    # Predefined ID: validate if required
                    if validate:
                        # Check that all required IDs (id to id+num-1) are available
                        required = set(range(irq.id, irq.id + irq.num))
                        can_go = required.issubset(set(possible_ids))

                        if not can_go:
                            # Generate helpful error message
                            missing = required - set(possible_ids)
                            missing_names = [predefined_map[miss] for miss in missing]
                            raise ValueError(
                                f"Interrupt conflict: IDs {missing} required but already "
                                f"used by {missing_names}"
                            )
                    # remove assigned IDs from available pool
                    for i in range(irq.num):
                        possible_ids.remove(irq.id + i)

                    self.add_interrupt(name, irq)

    # ================================================================
    # String Representation
    # ================================================================

    def __repr__(self) -> str:
        """String representation of the InterruptManager."""
        return f"InterruptManager(interrupts={len(self._interrupts)}, max={self._max_interrupts})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [f"InterruptManager: {len(self._interrupts)} interrupts"]
        for name, irq in sorted(self._interrupts.items(), key=lambda x: x[1].id):
            if irq.num > 1:
                lines.append(
                    f"  {name}: IDs {irq.id}-{irq.id + irq.num - 1} (num={irq.num})"
                )
            else:
                lines.append(f"  {name}: ID {irq.id}")
        return "\n".join(lines)
