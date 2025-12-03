from copy import deepcopy
from typing import Dict
from .bus_type import BusType
from .memory_ss.memory_ss import MemorySS
from .cpu.cpu import CPU
from .peripherals.abstractions import PeripheralDomain, Interrupt
from .peripherals.base_peripherals_domain import BasePeripheralDomain
from .peripherals.user_peripherals_domain import UserPeripheralDomain
from .pads.PadRing import PadRing
import re


class XHeep:
    """
    Represents the whole X-HEEP system.

    An instance of this class is passed to the mako templates.

    :param BusType bus_type: The bus type chosen for this mcu.
    :raise TypeError: when parameters are of incorrect type.
    """

    IL_COMPATIBLE_BUS_TYPES = [BusType.NtoM]
    """Constant set of bus types that support interleaved memory banks"""

    def __init__(
        self,
        bus_type: BusType,
    ):
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

        if pad_ring is None or not isinstance(pad_ring, PadRing):
            raise TypeError(
                f"xheep.get_padring() should be of type PadRing not {type(self._padring)}"
            )
        self._padring = pad_ring

    def get_padring(self):
        return self._padring

    # ------------------------------------------------------------
    # Interrupts
    # ------------------------------------------------------------

    def add_interrupts_from_peripheral_domains(self):
        """
        Adds the interrupts from the peripheral domains to the system interrupts.
        """
        # check no 2 peripherals have the same interrupt id

        all_ids = [
            irq.id
            for irq in self._base_peripheral_domain.get_interrupts().values()
            if irq is not None and irq.id is not None
        ] + [
            irq.id
            for irq in self._user_peripheral_domain.get_interrupts().values()
            if irq is not None and irq.id is not None
        ]

        set_ids = set(all_ids)
        if len(all_ids) != len(set_ids):
            raise ValueError("Two peripherals have the same interrupt id")

        possible_ids = list(set(range(0, 64)).difference(set_ids))

        for name, irq in self._base_peripheral_domain.get_interrupts().items():
            if irq is None:
                assigned_id = possible_ids.pop(0)
                self.add_interrupt(name, assigned_id)
            else:

                required = set(range(irq.id, irq.id + irq.num))
                can_go = required.issubset(set(possible_ids))

                if not can_go:
                    missing = required - set(possible_ids)

                    all_predefined = {
                        irq.id: name
                        for name, irq in self._base_peripheral_domain.get_interrupts().items()
                        if irq is not None and irq.id is not None
                    } + {
                        irq.id: name
                        for name, irq in self._user_peripheral_domain.get_interrupts().items()
                        if irq is not None and irq.id is not None
                    }
                    missing_names = [all_predefined[miss] for miss in missing]

                    raise ValueError(
                        f"You have elements the way {missing} used by {missing_names} "
                    )

                self.add_interrupt(name, irq)

        for name, irq in self._user_peripheral_domain.get_interrupts().items():
            if irq is None:
                assigned_id = possible_ids.pop(0)
                self.add_interrupt(name, assigned_id)
            else:
                self.add_interrupt(name, irq)

        self._interrupts = dict(
            sorted(self._interrupts.items(), key=lambda item: item[1].id)
        )

    def get_interrupts(self) -> Dict[str, Interrupt]:
        """
        :return: The interrupts of the system.
        :rtype: Dict[str,int]
        """
        print(type(list(self._interrupts.values())[0]))
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

    def add_interrupt(self, name: str, irq: int):
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
                f"xheep.add_interrupt() irq should be of type int not {type(irq)}"
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
            (re.match(r"^(.*)_(\d+)$", name).group(1), id)
            for name, id in interrupts.items()
            if re.match(r"^(.*)_(\d+)$", name)
        ]
        set_names = set([name for name, _, in names])
        for name in list(set_names):
            filtered = [x for x in names if x[0] == name]
            filtered.sort(key=lambda x: x[1])
            print(filtered)
            irq = Interrupt(filtered[0][1], len(filtered))
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
        if self.get_padring() is not None:
            self.get_padring().build()

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

        # Check that peripherals domains do not overlap
        ret = True
        if (
            self.are_base_peripherals_configured()
            and self._base_peripheral_domain.get_start_address()
            < self._user_peripheral_domain.get_start_address()
            and self._base_peripheral_domain.get_start_address()
            + self._base_peripheral_domain.get_length()
            > self._user_peripheral_domain.get_start_address()
        ):  # base peripheral domain comes before user peripheral domain
            print(
                f"The base peripheral domain (ends at {self._base_peripheral_domain.get_start_address() + self._base_peripheral_domain.get_length():#08X}) overflows over user peripheral domain (starts at {self._user_peripheral_domain.get_start_address():#08X})."
            )
            ret = False
        if (
            self.are_user_peripherals_configured()
            and self._user_peripheral_domain.get_start_address()
            < self._base_peripheral_domain.get_start_address()
            and self._user_peripheral_domain.get_start_address()
            + self._user_peripheral_domain.get_length()
            > self._base_peripheral_domain.get_start_address()
        ):  # user peripheral domain comes before base peripheral domain
            print(
                f"The user peripheral domain (ends at {self._user_peripheral_domain.get_start_address() + self._user_peripheral_domain.get_length():#08X}) overflows over base peripheral domain (starts at {self._base_peripheral_domain.get_start_address():#08X})."
            )
            ret = False
        if (
            self.are_user_peripherals_configured()
            and self.are_base_peripherals_configured()
            and self._user_peripheral_domain.get_start_address()
            == self._base_peripheral_domain.get_start_address()
        ):  # both domains start at the same address
            print(
                f"The base peripheral domain and the user peripheral domain should not start at the same address (current addresses are {self._base_peripheral_domain.get_start_address():#08X} and {self._user_peripheral_domain.get_start_address():#08X})."
            )
            ret = False
        if (
            self.are_base_peripherals_configured()
            and self._base_peripheral_domain.get_start_address() < 0x10000
        ):  # from mcu_gen.py
            print(
                f"Always on peripheral start address must be greater than 0x10000, current address is {self._base_peripheral_domain.get_start_address():#08X}."
            )
            ret = False
        return ret
