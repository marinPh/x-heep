from copy import deepcopy
from typing import Dict
from .bus_type import BusType
from .memory_ss.memory_ss import MemorySS
from .cpu.cpu import CPU
from .peripherals.abstractions import PeripheralDomain, Interrupt
from .peripherals.base_peripherals_domain import BasePeripheralDomain
from .peripherals.user_peripherals_domain import UserPeripheralDomain
from .pads.PadRing import PadRing
import numpy as np
import re

MAX_INTERRUPTS = 64


class XHeep:
    """
    Represents the whole X-HEEP system.

    An instance of this class is passed to the mako templates.

    :param BusType bus_type: The bus type chosen for this mcu.
    :raise TypeError: when parameters are of incorrect type.
    """

    IL_COMPATIBLE_BUS_TYPES = [BusType.NtoM]
    """Constant set of bus types that support interleaved memory banks"""

    def __init__(self, bus_type: BusType, max_intrs: int = MAX_INTERRUPTS):
        if not type(bus_type) is BusType:
            raise TypeError(
                f"XHeep.bus_type should be of type BusType not {type(self._bus_type)}"
            )

        self._cpu = None

        self._bus_type: BusType = bus_type

        self._memory_ss = None

        self._base_peripheral_domain = None
        self._user_peripheral_domain = None
        self._padring: PadRing = None
        self._interrupts: Dict[str, Interrupt] = {}

        self._extensions = {}

        self.max_intrs = max_intrs

    # ------------------------------------------------------------
    # CPU
    # ------------------------------------------------------------

    def set_cpu(self, cpu: CPU):
        """
        Sets the CPU of the system.

        :param CPU cpu: The CPU to set.
        :raise TypeError: when cpu is of incorrect type.
        """
        if not isinstance(cpu, CPU):
            raise TypeError(f"XHeep.cpu should be of type CPU not {type(self._cpu)}")
        self._cpu = cpu

    def cpu(self) -> CPU:
        """
        :return: the configured CPU
        :rtype: CPU
        """
        return self._cpu

    # ------------------------------------------------------------
    # Bus
    # ------------------------------------------------------------

    def set_bus_type(self, bus_type: BusType):
        """
        Sets the bus type of the system.

        :param BusType bus_type: The bus type to set.
        :raise TypeError: when bus_type is of incorrect type.
        """
        if not type(bus_type) is BusType:
            raise TypeError(
                f"XHeep.bus_type should be of type BusType not {type(self._bus_type)}"
            )
        self._bus_type = bus_type

    def bus_type(self) -> BusType:
        """
        :return: the configured bus type
        :rtype: BusType
        """
        return self._bus_type

    # ------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------

    def set_memory_ss(self, memory_ss: MemorySS):
        """
        Sets the memory subsystem of the system.

        :param MemorySS memory_ss: The memory subsystem to set.
        :raise TypeError: when memory_ss is of incorrect type.
        """
        if not isinstance(memory_ss, MemorySS):
            raise TypeError(
                f"XHeep.memory_ss should be of type MemorySS not {type(self._memory_ss)}"
            )
        self._memory_ss = memory_ss

    def memory_ss(self) -> MemorySS:
        """
        :return: the configured memory subsystem
        :rtype: MemorySS
        """
        return self._memory_ss

    # ------------------------------------------------------------
    # Peripherals
    # ------------------------------------------------------------

    def are_base_peripherals_configured(self) -> bool:
        """
        :return: `True` if the base peripherals are configured, `False` otherwise.
        :rtype: bool
        """
        return self._base_peripheral_domain is not None

    def are_user_peripherals_configured(self) -> bool:
        """
        :return: `True` if the user peripherals are configured, `False` otherwise.
        :rtype: bool
        """
        return self._user_peripheral_domain is not None

    def are_peripherals_configured(self) -> bool:
        """
        :return: `True` if both base and user peripherals are configured, `False` otherwise.
        :rtype: bool
        """
        return (
            self.are_base_peripherals_configured()
            and self.are_user_peripherals_configured()
        )

    def extend_interrupt(self, interrupts: Dict[str, Interrupt]):
        """
        Extend the system interrupts with new interrupts from a domain.

        :param Dict[str, Interrupt] interrupts: The interrupts to add.
        """
        for name, irq in interrupts.items():
            if name not in self._interrupts:
                self._interrupts[name] = irq

    def get_num_intr(self):
        return np.array(
            [
                irq.num
                for name, irq in self._interrupts.items()
                if not name.startswith("EXT_")
            ]
        ).sum()

    def add_peripheral_domain(self, domain: PeripheralDomain):
        """
        Add a peripheral domain to the system. The domain should already contain all peripherals well configured. When adding a domain, a deepcopy is made to avoid side effects.

        :param PeripheralDomain domain: The domain to add.
        """
        if isinstance(domain, BasePeripheralDomain):
            self._base_peripheral_domain = deepcopy(domain)
        elif isinstance(domain, UserPeripheralDomain):
            self._user_peripheral_domain = deepcopy(domain)
        else:
            raise ValueError(
                "Domain is neither a BasePeripheralDomain nor a UserPeripheralDomain"
            )
        # self.extend_interrupt(domain.get_interrupts())

    def get_user_peripheral_domain(self):
        """
        Returns a deepcopy of the user peripheral domain.

        :return: The user peripheral domain.
        :rtype: UserPeripheralDomain
        """
        return deepcopy(self._user_peripheral_domain)

    def get_base_peripheral_domain(self):
        """
        Returns a deepcopy of the base peripheral domain.

        :return: The base peripheral domain.
        :rtype: BasePeripheralDomain
        """
        return deepcopy(self._base_peripheral_domain)

    # ------------------------------------------------------------
    # Pad Ring
    # ------------------------------------------------------------

    def set_padring(self, pad_ring: PadRing):
        """
        Sets the pad ring of the system.

        :param PadRing pad_ring: The pad ring to set.
        :raise TypeError: when pad_ring is of incorrect type.
        """
        if not isinstance(pad_ring, PadRing):
            raise TypeError(
                f"xheep.get_padring() should be of type PadRing not {type(self._padring)}"
            )
        self._padring = pad_ring

    def get_padring(self):
        return self._padring

    # ------------------------------------------------------------
    # Interrupts
    # ------------------------------------------------------------

    def _collect_interrupt_ids_from_domains(self, *domains):
        """
        Collect all interrupt IDs from multiple peripheral domains.

        :param domains: Variable number of peripheral domains
        :return: List of all interrupt IDs
        :rtype: list[int]
        """
        all_ids = []
        for domain in domains:
            all_ids.extend(
                [
                    irq.id
                    for irq in domain.get_interrupts().values()
                    if irq is not None and irq.id is not None
                ]
            )
        return all_ids

    def _collect_predefined_interrupts_map(self, *domains):
        """
        Create a mapping of interrupt ID to peripheral name for all predefined interrupts.

        :param domains: Variable number of peripheral domains
        :return: Dictionary mapping interrupt ID to peripheral name
        :rtype: dict[int, str]
        """
        result = {}
        for domain in domains:
            for name, irq in domain.get_interrupts().items():
                if irq is not None and irq.id is not None:
                    result[irq.id] = name
        return result

    def _assign_interrupts_from_domain(
        self, domain, possible_ids, validate=False, predefined_map=None
    ):
        """
        Assign interrupts from a peripheral domain.

        :param domain: The peripheral domain to process
        :param list possible_ids: List of available interrupt IDs (will be modified)
        :param bool validate: Whether to validate interrupt ID conflicts
        :param dict predefined_map: Mapping of predefined interrupt IDs to names (for error messages)
        """
        for name, irq in domain.get_interrupts().items():
            if irq is None:
                assigned_id = possible_ids.pop(0)
                self.add_interrupt(name, Interrupt(assigned_id))
            else:
                if validate:
                    required = set(range(irq.id, irq.id + irq.num))
                    can_go = required.issubset(set(possible_ids))

                    if not can_go:
                        missing = required - set(possible_ids)
                        missing_names = [predefined_map[miss] for miss in missing]
                        raise ValueError(
                            f"You have elements the way {missing} used by {missing_names} "
                        )

                self.add_interrupt(name, irq)

    def add_interrupts_from_peripheral_domains(self):
        """
        Adds the interrupts from the peripheral domains to the system interrupts.
        """
        # Collect all interrupt IDs from both domains
        all_ids = self._collect_interrupt_ids_from_domains(
            self._base_peripheral_domain, self._user_peripheral_domain
        )

        # Check no 2 peripherals have the same interrupt ID
        set_ids = set(all_ids)
        if len(all_ids) != len(set_ids):
            raise ValueError("Two peripherals have the same interrupt id")

        possible_ids = list(set(range(0, 64)).difference(set_ids))

        # Get predefined interrupts map for validation
        predefined_map = self._collect_predefined_interrupts_map(
            self._base_peripheral_domain, self._user_peripheral_domain
        )

        # Assign interrupts from base peripheral domain (with validation)
        self._assign_interrupts_from_domain(
            self._base_peripheral_domain,
            possible_ids,
            validate=True,
            predefined_map=predefined_map,
        )

        # Assign interrupts from user peripheral domain (without validation)
        self._assign_interrupts_from_domain(
            self._user_peripheral_domain, possible_ids, validate=False
        )

        # Sort interrupts by ID
        self._interrupts = dict(
            sorted(self._interrupts.items(), key=lambda item: item[1].id)
        )

    def get_interrupts(self) -> Dict[str, Interrupt]:
        """
        :return: The interrupts of the system.
        :rtype: Dict[str,int]
        """
        return deepcopy(self._interrupts)

    def set_interrupts(self, interrupts: Dict[str, int]):
        """
        Sets the interrupts of the system.

        :param Dict[str,int] interrupts: The interrupts to set.
        :raise TypeError: when interrupts is of incorrect type.
        """

        if not isinstance(interrupts, dict):
            raise TypeError(
                f"xheep.get_interrupts() should be of type Dict[str,int] not {type(self._interrupts)}"
            )
        self._interrupts = interrupts.copy()

    def add_interrupt(self, name: str, irq: Interrupt):
        """
        Add an interrupt to the system.

        :param str name: The name of the interrupt.
        :param int irq: The IRQ number of the interrupt.
        :raise TypeError: when name is of incorrect type.
        """

        if not isinstance(name, str):
            raise TypeError(
                f"xheep.add_interrupt() name should be of type str not {type(name)}"
            )

        if irq is not None and not isinstance(irq, Interrupt):
            raise TypeError(
                f"xheep.add_interrupt() irq should be of type Interrupt not {type(irq)}"
            )

        if name in self._interrupts:
            raise ValueError(f"Interrupt {name} already exists in the system")

        if irq is not None and irq in self._interrupts.values():
            raise ValueError(f"Interrupt IRQ {irq} already exists in the system")

        self._interrupts[name] = irq

    def add_interrupts_from_config_dict(self, interrupts: Dict[str, int]):
        """
        Adds interrupts from a configuration dictionary.

        :param Dict[str,int] interrupts: The interrupts to add.
        """
        suffix_re = re.compile(r"^(.*)_(\d+)$")
        names = [
            (
                re.match(r"^(.*)_(\d+)$", name).group(1),
                id,
                re.match(r"^(.*)_(\d+)$", name).group(2),
            )
            for name, id in interrupts.items()
            if re.match(r"^(.*)_(\d+)$", name)
        ]
        set_names = set([name for name, _, _ in names])
        for name in list(set_names):
            filtered = [x for x in names if x[0] == name]
            filtered.sort(key=lambda x: x[1])
            start: int = min([int(f[2]) for f in filtered])
            irq = Interrupt(filtered[0][1], len(filtered), start)
            self.add_interrupt(name, irq)
        names = [
            (name, id) for name, id in interrupts.items() if not suffix_re.match(name)
        ]
        for name, id in names:
            irq = Interrupt(id)
            self.add_interrupt(name, irq)

        self._interrupts = dict(
            sorted(self._interrupts.items(), key=lambda item: item[1].id)
        )

    def get_simple_interrupts(self) -> Dict[str, int]:
        temp = dict()
        for name, irq in self._interrupts.items():
            if irq.num > 1:
                cnt = irq.id
                for i in range(irq.start_seq, irq.start_seq + irq.num):
                    temp[f"{name}_{i}"] = cnt
                    cnt += 1
            else:
                temp[name] = irq.id
        return temp

    def get_interrupts_for_peripheral(
        self, peripheral_name: str
    ) -> Dict[str, Interrupt]:
        """
        Get all interrupts belonging to a specific peripheral.

        :param str peripheral_name: Name of the peripheral (e.g., 'i2c', 'uart', 'gpio')
        :return: Dictionary of interrupt_name -> Interrupt for this peripheral
        """
        result = {}

        # I2C interrupt names in hjson (special case - no peripheral prefix)
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

    def get_peripheral_interrupt_connections(self, peripheral_name: str) -> list:
        """
        Generate port connection strings for a peripheral's interrupts.
        Returns list of (port_name, signal_name) tuples.

        Example for i2c: [('intr_fmt_watermark_o', 'i2c_intr_fmt_watermark'), ...]
        Example for uart: [('intr_tx_watermark_o', 'uart_intr_tx_watermark'), ...]

        :param str peripheral_name: Name of the peripheral
        :return: List of (port_name, signal_name) tuples
        """
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

    # ------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------

    def add_extension(self, name, extension):
        """
        Register an external extension or configuration (object, dict, etc.).

        :param str name: Name of the extension.
        :param Any extension: The extension object.
        """
        self._extensions[name] = extension

    def get_extension(self, name):
        """
        Retrieve a previously registered extension.

        :param str name: Name of the extension.
        :return: The extension object.
        :rtype: Any
        """
        return self._extensions.get(name, None)

    # ------------------------------------------------------------
    # Build and Validate
    # ------------------------------------------------------------

    def build(self):
        """
        Makes the system ready to be used.
        """

        if self.memory_ss():
            self.memory_ss().build()
        if self.are_base_peripherals_configured():
            self._base_peripheral_domain.build()
        if self.are_user_peripherals_configured():
            self._user_peripheral_domain.build()

    def _check_domain_overlap(self, domain1, domain2, name1, name2):
        """
        Check if two peripheral domains overlap.

        :param domain1: First domain to check
        :param domain2: Second domain to check
        :param str name1: Name of first domain (for error messages)
        :param str name2: Name of second domain (for error messages)
        :return: True if domains do not overlap, False if they overlap
        :rtype: bool
        """
        # Check if domain1 comes before domain2 and overflows into it
        if (
            domain1.get_start_address() < domain2.get_start_address()
            and domain1.get_start_address() + domain1.get_length()
            > domain2.get_start_address()
        ):
            print(
                f"The {name1} peripheral domain (ends at "
                f"{domain1.get_start_address() + domain1.get_length():#08X}) "
                f"overflows over {name2} peripheral domain (starts at "
                f"{domain2.get_start_address():#08X})."
            )
            return False

        # Check if domains start at the same address
        if domain1.get_start_address() == domain2.get_start_address():
            print(
                f"The {name1} peripheral domain and the {name2} peripheral domain "
                f"should not start at the same address (current address is "
                f"{domain1.get_start_address():#08X})."
            )
            return False

        return True

    def validate(self) -> bool:
        """
        Does some basics checks on the configuration

        This should be called before using the XHeep object to generate the project.

        :return: the validity of the configuration
        :rtype: bool
        """
        if not self.cpu():
            print("A CPU must be configured")
            return False

        if not self.memory_ss():
            print("A memory subsystem must be configured")
            return False
        else:
            if not self.memory_ss().validate():
                return False
            if self.memory_ss().has_il_ram() and (
                self._bus_type not in self.IL_COMPATIBLE_BUS_TYPES
            ):
                raise RuntimeError(
                    f"This system has a {self._bus_type} bus, one of {self.IL_COMPATIBLE_BUS_TYPES} is required for interleaved memory"
                )

        # Check that each peripheral domain is valid
        if self.are_base_peripherals_configured():
            self._base_peripheral_domain.validate()
        if self.are_user_peripherals_configured():
            self._user_peripheral_domain.validate()

        # Check that peripheral domains do not overlap
        ret = True
        if (
            self.are_base_peripherals_configured()
            and self.are_user_peripherals_configured()
        ):
            # Check base -> user overlap
            if not self._check_domain_overlap(
                self._base_peripheral_domain,
                self._user_peripheral_domain,
                "base",
                "user",
            ):
                ret = False
            # Check user -> base overlap
            if not self._check_domain_overlap(
                self._user_peripheral_domain,
                self._base_peripheral_domain,
                "user",
                "base",
            ):
                ret = False

        # Check base peripheral domain start address
        if (
            self.are_base_peripherals_configured()
            and self._base_peripheral_domain.get_start_address() < 0x10000
        ):
            print(
                f"Always on peripheral start address must be greater than 0x10000, "
                f"current address is {self._base_peripheral_domain.get_start_address():#08X}."
            )
            ret = False

        return ret
