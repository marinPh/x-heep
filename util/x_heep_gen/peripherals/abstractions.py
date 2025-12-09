# Peripheral abstract classes

from dataclasses import dataclass
import os.path as path
from abc import (
    ABC,
    abstractmethod,
)  # Used to define abstract classes that cannot be instantiated, only well defined subclasses can be instantiated.
from enum import Enum
from copy import deepcopy
from typing import List, Dict, Optional


@dataclass
class Interrupt:
    id: int
    num: Optional[int] = 1
    start_seq: Optional[int] = id
    peripheral: Optional[str] = None  # Name of peripheral this interrupt belongs to
    port_names: Optional[List[str]] = None  # Port names for the peripheral instance

    def __post_init__(self):
        if self.num < 1:
            raise ValueError("num should be above 1 cannot be less")
        if self.id < 0:
            raise ValueError("ID cannot be negative")


class Peripheral(ABC):
    """
    Basic description of a peripheral. These peripherals are not linked to a hjson file, they only have a memory range. This class cannot be instantiated.

    :param int address: The virtual (in peripheral domain) memory address of the peripheral, the start address should be known by the creator of the class.
    :param int length: The size taken in memory by the peripheral
    """

    _length: int = int("0x00010000", 16)  # default length of 64KB
    _name: str
    _address: int = None

    _interrupts: Dict[str, Interrupt] = {}

    def __init__(self, offset=None, length=None):
        """
        Initialize the peripheral with a given address.

        :param int offset: The virtual (in peripheral domain) memory address of the peripheral. If None, the offset will be automatically compute during build function.
        :param int length: The size taken in memory by the peripheral. If None, the length will be automatically set to 64KB.
        """
        if type(offset) == int and offset >= 0x00000000:
            self._address = offset
        else:
            self._address = None

        if length is not None:
            self._length = length

    def get_address(self):
        """
        :return: The virtual (in peripheral domain) memory address of the peripheral. If not set, return None.
        :rtype: int
        """
        return self._address

    def get_interrupts(self):
        """
        :return: The interrupts of the peripheral.
        :rtype: Dict[str,int]
        """
        return self._interrupts.copy()

    def set_address(self, address):
        """
        Set the virtual (in peripheral domain) memory address of the peripheral.
        """
        self._address = address

    def get_length(self):
        """
        :return: The length of the peripheral.
        :rtype: int
        """
        return self._length

    def get_name(self):
        """
        :return: The name of the peripheral.
        :rtype: str
        """
        return self._name


class BasePeripheral(Peripheral, ABC):
    """
    Abstract class representing always-on peripherals. This class cannot be instantiated.
    """


class UserPeripheral(Peripheral, ABC):
    """
    Abstract class representing user-configurable peripherals. This class cannot be instantiated.
    """


class PeripheralDomain(ABC):
    """
    Abstract class representing a peripheral domain. This class cannot be instantiated.

    :param str name: The name of the peripheral domain. Convention : starts with a capital letter and is in singular form (no "peripheral domain" at the end)
    :param int start_address: The start address of the peripheral domain.
    :param int length: The length of the peripheral domain.
    :param list[Peripheral] peripherals: The list of peripherals in the domain. There can be more than one instance of the same peripheral.
    """

    _name: str
    _start_address: int
    _length: int
    _peripherals: List[
        Peripheral
    ]  # type has to be precised for filtering in validation
    _interrupts: Dict[str, Interrupt] = {}

    def get_interrupts(self):
        """
        :return: The interrupts of the peripheral domain.
        :rtype: Dict[str,int]
        """
        return self._interrupts.copy()

    @abstractmethod
    def __init__(
        self,
        name: str,
        start_address: int,
        length: int,
        interrupts: Dict[str, int] = {},
    ):
        """
        Initialize the peripheral domain. Is abstract because each peripheral domain has its own way of initializing without letting the user define start address and length.

        :param str name: The name of the peripheral domain. Convention : starts with a capital letter and is in singular form (no "peripheral domain" at the end)
        :param int start_address: The start address of the peripheral domain.
        :param int length: The length of the peripheral domain.
        """
        self._name = f"{name} Peripheral Domain"
        self._start_address = start_address
        self._length = length
        self._peripherals = []
        self._interrupts = interrupts.copy()

    @abstractmethod
    def _get_peripheral_type(self):
        """
        Get the expected peripheral type for this domain (used for validation).
        Must be implemented by subclasses to return the appropriate type (e.g., BasePeripheral, UserPeripheral).

        :return: The peripheral type class for validation.
        :rtype: type
        """
        ...

    def extend_interrupt(self, interrupts: Dict[str, Interrupt]):
        """
        Extend the system interrupts with new interrupts from a domain.

        :param Dict[str, Interrupt] interrupts: The interrupts to add.
        """
        for name, irq in interrupts.items():
            if name not in self._interrupts:
                self._interrupts[name] = irq

    def add_peripheral(self, peripheral: Peripheral):
        """
        Add a peripheral to the domain. The peripheral should be fully configured when added. If the peripheral has no offset, it will be automatically computed during build.

        :param Peripheral peripheral: The peripheral to add.
        """
        if not isinstance(peripheral, self._get_peripheral_type()):
            raise ValueError(
                f"Peripheral is not a {self._get_peripheral_type().__name__}"
            )
        self._peripherals.append(peripheral)
        self.extend_interrupt(peripheral.get_interrupts())

    def remove_peripheral(self, peripheral: Peripheral):
        """
        Remove a peripheral from the domain.

        :param Peripheral peripheral: The peripheral to remove.
        """
        if peripheral not in self._peripherals:
            print(
                f"Warning : Peripheral {peripheral.get_name()} is not in the domain {self._name}"
            )
        self._peripherals.remove(peripheral)

    def get_start_address(self):
        """
        :return: The start address of the peripheral domain.
        :rtype: int
        """
        return self._start_address

    def get_length(self):
        """
        :return: The length of the peripheral domain.
        :rtype: int
        """
        return self._length

    def get_peripherals(self):
        """
        :return: A copy of the list of peripherals in the domain.
        :rtype: list[Peripheral]
        """
        return (
            []
            if self._peripherals is None or len(self._peripherals) == 0
            else [deepcopy(p) for p in self._peripherals]
        )

    def contains_peripheral(self, peripheral_name: str):
        """
        Check if the peripheral domain contains a peripheral with the given name.

        :param str peripheral_name: The name of the peripheral to check (case sensitive).
        :return: True if the peripheral domain contains a peripheral with the given name, False otherwise.
        :rtype: bool
        """
        return any(p.get_name() == peripheral_name for p in self._peripherals)

    # Build function

    def build(self):
        """
        Build the peripheral domain. This function will compute the offset of the peripherals that have no offset.
        """

        if self._peripherals is None or len(self._peripherals) == 0:
            print(f"Warning : No peripherals in {self._name}")
            return

        # Setup

        # List of peripherals without address, sorted by length in descending order. Original index is kept to update the peripheral with the offset after placement.
        peripherals_without_address = [
            (i, p) for i, p in enumerate(self._peripherals) if p.get_address() is None
        ]
        peripherals_without_address.sort(
            key=lambda tuple: tuple[1].get_length(), reverse=True
        )

        # List of peripherals with address, sorted by address. Original index is kept to update the peripheral with the offset after placement.
        peripherals_with_address = [
            (i, p)
            for i, p in enumerate(self._peripherals)
            if p is not None and p.get_address() is not None
        ]
        peripherals_with_address.sort(key=lambda tuple: tuple[1].get_address())

        # List of free spaces of intervals of free memory space in the domain. In the beggining, there is only one free space, the whole domain.
        free_space = [[0, self._length]]

        # Number of peripherals with address
        num_peripherals_with_address = (
            0 if peripherals_with_address == None else len(peripherals_with_address)
        )

        # Number of peripherals without address
        num_peripherals_without_address = (
            0
            if peripherals_without_address == None
            else len(peripherals_without_address)
        )

        # Creating the list of intervals of free space

        # Works because peripherals_with_address is sorted by address
        # Splits the last free space into two new lists, one before the peripheral and one after
        for i in range(num_peripherals_with_address):
            # Removes last free space to split it
            last_free_space = free_space[-1]
            free_space.pop()
            current_peripheral = peripherals_with_address[i][1]

            # Checks if the peripheral domain is in free space
            if current_peripheral.get_address() < last_free_space[0]:
                if i == 0:
                    raise ValueError(
                        f"Peripheral {current_peripheral.get_name()} has an address that starts before the first free space ({current_peripheral.get_name()} starts at {hex(current_peripheral.get_address())} but first free space starts at {hex(last_free_space[0])})"
                    )
                else:
                    raise ValueError(
                        f"Peripheral {current_peripheral.get_name()} has an address that starts in {peripherals_with_address[i-1].get_name()} domain ({current_peripheral.get_name()} starts at {hex(current_peripheral.get_address())} but {peripherals_with_address[i-1].get_name()} ends at {hex(last_free_space[0])}"
                    )

            if (
                current_peripheral.get_address() + current_peripheral.get_length()
            ) > last_free_space[1]:
                raise ValueError(
                    f"Peripheral {current_peripheral.get_name()} has an address that ends after the last free space ({current_peripheral.get_name()} ends at {hex(current_peripheral.get_address() + current_peripheral.get_length())} but last free space ends at {hex(last_free_space[1])})"
                )

            # If the peripheral starts after the last free space, add it to the free space before the peripheral
            if last_free_space[0] > current_peripheral.get_address():
                free_space.append(
                    [last_free_space[0], current_peripheral.get_address()]
                )

            # If the peripheral ends before the last free space, add it to the free space after the peripheral
            if (
                current_peripheral.get_address() + current_peripheral.get_length()
            ) < last_free_space[1]:
                free_space.append(
                    [
                        current_peripheral.get_address()
                        + current_peripheral.get_length(),
                        last_free_space[1],
                    ]
                )

        # Placing peripherals in free spaces

        # Place peripherals where in the first free space where they fit, works because peripherals_without_address is sorted by length in descending order
        offsets = (
            {}
        )  # Will contain the offsets of the peripherals, and then update the peripherals with the offsets if they all fit

        for i in range(num_peripherals_without_address):
            fit = False  # Check if the peripheral fits in the free space
            current_peripheral = peripherals_without_address[i][1]
            for j in range(len(free_space)):
                if (
                    current_peripheral.get_length()
                    <= free_space[j][1] - free_space[j][0]
                ):
                    offsets[peripherals_without_address[i][0]] = free_space[j][
                        0
                    ]  # Since there can be multiple instances of the same peripheral, we must map indexes from self._peripherals instead of peripheral names (two peripherals can have the same name)

                    # Either remove space if the peripheral exactly fits the space, or shrinks the space
                    if (
                        free_space[j][0] + current_peripheral.get_length()
                        == free_space[j][1]
                    ):
                        free_space.pop(j)
                    else:
                        free_space[j][0] += current_peripheral.get_length()

                    # Ends search for free space
                    fit = True
                    break
            if not fit:
                raise ValueError(
                    f"Could not find a free space large enough for peripheral {current_peripheral.get_name()} with length {hex(current_peripheral.get_length())}"
                )

        # Setting peripherals addresses if there is enough space
        for idx, _ in peripherals_without_address:
            self._peripherals[idx].set_address(offsets[idx])

    # Validate functions
    def __check_peripheral_non_overlap(self):
        """
        Check if the peripherals do not overlap.

        :return: True if the peripherals do not overlap, False otherwise.
        :rtype: bool
        """

        if self._peripherals is None or len(self._peripherals) == 0:
            print(f"Warning : No peripherals in {self._name}")
            return True

        peripherals_sorted = sorted(
            filter(lambda x: x != None, self._peripherals),
            key=lambda x: x.get_address(),
        )  # Filter out None values and sort by offset in growing order
        return_bool = True

        if len(peripherals_sorted) == 0:
            print(f"Warning : No peripherals in {self._name}")
            return return_bool

        # Check if every peripheral does not overlap with the next one (works because peripherals_sorted is sorted by address)
        for i in range(len(peripherals_sorted) - 1):
            if (
                peripherals_sorted[i].get_address() + peripherals_sorted[i].get_length()
                > peripherals_sorted[i + 1].get_address()
            ):
                print(
                    f"The peripheral {peripherals_sorted[i].get_name()} overflows over the domain (starts at {peripherals_sorted[i].get_address():#08X} and ends at {peripherals_sorted[i].get_address() + peripherals_sorted[i].get_length():#08X}, peripheral {peripherals_sorted[i+1].get_name()} starts at {peripherals_sorted[i+1].get_address():#08X})."
                )
                return_bool = False
            if peripherals_sorted[i].get_address() >= self._length:
                print(
                    f"The peripheral {peripherals_sorted[i].get_name()} is out of the domain (starts at {peripherals_sorted[i].get_address():#08X}, domain ends at {self._length:#08X})."
                )
                return_bool = False

        # Check if the last peripheral is out of the domain
        if (
            peripherals_sorted[-1].get_address() + peripherals_sorted[-1].get_length()
            > self._length
        ):
            print(
                f"The peripheral {peripherals_sorted[-1].get_name()} is out of the domain (starts at {peripherals_sorted[-1].get_address():#08X}, domain ends at {self._length:#08X})."
            )
            return_bool = False
        if peripherals_sorted[-1].get_address() >= self._length:
            print(
                f"The peripheral {peripherals_sorted[-1].get_name()} is out of the domain (starts at {peripherals_sorted[-1].get_address():#08X}, domain ends at {self._length:#08X})."
            )
            return_bool = False

        return return_bool

    def __check_peripheral_domain_bounds(self):
        """
        Check if the peripheral domain is within the bounds it can use (being above 0x10000).

        :return: True if the peripheral domain is within the bounds of the memory, False otherwise.
        :rtype: bool
        """

        if self.get_start_address() < int("10000", 16):
            print(
                f"Peripheral domain {self._name} start address must be greater than 0x10000"
            )
            return False

        return True

    def validate(self):
        """
        Validate the peripheral domain. Checks if the peripherals do not overlap and if the peripheral domain is within the bounds.

        :return: True if the peripheral domain is valid, False otherwise.
        :rtype: bool
        """

        return (
            self.__check_peripheral_non_overlap()
            and self.__check_peripheral_domain_bounds()
        )
