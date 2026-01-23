import re
import numpy as np
from copy import deepcopy
from typing import Dict, List, Tuple
from ..peripherals.abstractions import Interrupt, PeripheralDomain

DEFAULT_MAX_INTERRUPTS = 64


class InterruptManager:
    """Manages interrupt allocation and assignment for X-HEEP peripherals."""

    def __init__(self):
        self._interrupts: Dict[str, List[Interrupt]] = {}
        self._max_interrupts = DEFAULT_MAX_INTERRUPTS

    def assign_from_peripheral_domains(self, base_domain, user_domain):

        # Collect all interrupt IDs from both domains (from nested structure)
        all_ids = []
        for periph_intrs in self._interrupts.values():
            for irq in periph_intrs:
                all_ids.append(irq.id)

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

        # Sort each peripheral's interrupts by ID for consistent ordering
        for peripheral in self._interrupts:
            self._interrupts[peripheral].sort(key=lambda irq: irq.id)

    def add_interrupt(self, name: str, irq: Interrupt):
        """Add an interrupt to the manager."""
        if not isinstance(name, str):
            raise TypeError(f"interrupt name must be str, not {type(name)}")
        if irq is not None and not isinstance(irq, Interrupt):
            raise TypeError(f"irq must be Interrupt, not {type(irq)}")

        if irq.name is None:
            irq.name = name

        peripheral = irq.peripheral.lower() if irq and irq.peripheral else "unknown"

        if peripheral not in self._interrupts:
            self._interrupts[peripheral] = []

        if any(i.name == name for i in self._interrupts[peripheral]):
            return

        if irq is not None:
            for periph_intrs in self._interrupts.values():
                if irq in periph_intrs:
                    raise ValueError(f"Interrupt {irq} already exists")

        self._interrupts[peripheral].append(irq)

    def extend_interrupts(self, interrupts):
        """Add multiple interrupts (accepts flat or nested dict)."""
        for key, value in interrupts.items():
            if isinstance(value, list):
                for irq in value:
                    name = irq.name if irq.name else f"{key}_unnamed"
                    self.add_interrupt(name, irq)
            elif isinstance(value, Interrupt):
                self.add_interrupt(key, value)
            else:
                raise TypeError(
                    f"Expected Interrupt or List[Interrupt], got {type(value)}"
                )

    def get_max_interrupts(self) -> int:
        return self._max_interrupts

    def get_interrupts(self) -> Dict[str, List[Interrupt]]:
        """Get all interrupts grouped by peripheral."""
        return deepcopy(self._interrupts)

    def get_num_interrupts(self) -> int:
        """Get total number of interrupts (excluding external)."""
        total = 0
        for peripheral, periph_intrs in self._interrupts.items():
            if peripheral == "external":
                continue
            for irq in periph_intrs:
                if not irq.name.startswith("EXT_"):
                    total += irq.num
        return total

    def get_external_interrupts(self) -> List[Interrupt]:
        """Get available external interrupt slots."""
        possible_ids = list(
            set(range(0, self._max_interrupts)).difference(
                set(self.get_unpacked_interrupts().values())
            )
        )
        return [
            Interrupt(id=id, num=1, peripheral="external", name=f"EXT_INTR_{i}")
            for i, id in enumerate(possible_ids)
        ]

    def get_interrupts_for_peripheral(self, peripheral_name: str) -> List[Interrupt]:
        """Get all interrupts for a specific peripheral."""
        if peripheral_name in self._interrupts:
            return deepcopy(self._interrupts[peripheral_name])
        return []

    def get_unpacked_interrupts(self) -> Dict[str, int]:
        """Get all interrupts with multi-interrupts expanded to individual IDs."""
        temp = dict()
        for _, periph_intrs in self._interrupts.items():
            for irq in periph_intrs:
                if irq.num > 1:
                    cnt = irq.id
                    for i in range(irq.start_seq, irq.start_seq + irq.num):
                        temp[f"{irq.name}_{i}"] = cnt
                        cnt += 1
                else:
                    temp[irq.name] = irq.id
        return temp

    def set_interrupts(self, interrupts: Dict[str, List[Interrupt]]):
        """Replace all interrupts (WARNING: clears existing)."""
        if not isinstance(interrupts, dict):
            raise TypeError(f"interrupts must be dict, not {type(interrupts)}")
        self._interrupts = deepcopy(interrupts)

    def _collect_predefined_interrupts_map(self, *domains) -> Dict[int, str]:
        """Collect predefined interrupt IDs from peripheral domains."""
        result = {}
        for domain in domains:
            for peri in domain.get_peripherals():
                interrupts = peri.get_interrupts()
                if isinstance(interrupts, list):
                    for irq in interrupts:
                        if irq and irq.id is not None:
                            result[irq.id] = irq.name
        return result

    def _assign_interrupts_from_domain(
        self,
        domain: PeripheralDomain,
        possible_ids,
        validate=False,
        predefined_map=None,
    ):
        """Assign interrupts from a peripheral domain."""
        for peri in domain.get_peripherals():
            interrupts = peri.get_interrupts()

            # Process each interrupt from the list
            for irq in interrupts:
                name = irq.name if irq.name else f"{peri._name}_unnamed"
                if irq is None:
                    # No predefined ID: allocate from available pool
                    assigned_id = possible_ids.pop(0)
                    new_irq = Interrupt(assigned_id, peripheral=peri._name, name=name)
                    self.add_interrupt(name, new_irq)
                else:
                    # Set name if not already set
                    if irq.name is None:
                        irq.name = name

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
                        try:
                            possible_ids.remove(irq.id + i)
                        except ValueError:
                            pass

                    self.add_interrupt(name, irq)

    def __repr__(self) -> str:
        return f"InterruptManager({len(self._interrupts)} peripherals, max={self._max_interrupts})"
