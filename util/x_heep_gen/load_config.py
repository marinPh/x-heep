import importlib
from pathlib import PurePath
from typing import List, Union
import hjson
import os
import sys
from .pads.PadRing import PadRing
from jsonref import JsonRef

from .cpu.cpu import CPU
from .cpu.cv32e20 import cv32e20
from .memory_ss.memory_ss import MemorySS
from .memory_ss.linker_section import LinkerSection
from .xheep import BusType, XHeep
from .peripherals.base_peripherals_domain import BasePeripheralDomain
from .peripherals.user_peripherals_domain import UserPeripheralDomain
from .pads.PadDef import PadGroup
from .peripherals.base_peripherals import (
    SOC_ctrl,
    Bootrom,
    SPI_flash,
    SPI_memio,
    DMA,
    Power_manager,
    RV_timer_ao,
    Fast_intr_ctrl,
    Ext_peripheral,
    Pad_control,
    GPIO_ao,
)


from .peripherals.user_peripherals import (
    RV_plic,
    SPI_host,
    GPIO,
    I2C,
    RV_timer,
    SPI2,
    PDM2PCM,
    I2S,
    UART,
)


def to_int(input) -> Union[int, None]:
    if type(input) is int:
        return input

    if type(input) is str:
        base = 10
        if len(input) >= 2:
            if input[0:2].upper() == "0X":
                base = 16
                input = input[2:]
            elif input[0:2] == "0o":
                base = 8
                input = input[2:]
            elif input[0:2].upper() == "0b":
                base = 2
                input = input[2:]

        return int(input, base)
    return None


def ram_list(l: "List[int]", entry):
    """
    Parses the hjson ram bank configuration in continuous mode.

    :param List[int] l: the list where bank sizes in kiB should be added
    :enrtry: the entry to be parsed. It should be a list an integer or an continuous dictionary
    :raise RuntimeError: when an invalid configuration is processed.
    """
    if type(l) is not list:
        raise TypeError("l should be of type list")

    if type(entry) is int:
        l.append(entry)
        return

    if type(entry) is list:
        for i in entry:
            ram_list(l, i)
        return

    if type(entry) is hjson.OrderedDict:
        num = 1
        if "num" in entry:
            if type(entry["num"]) is not int:
                raise RuntimeError(
                    "if the num field is present in ram configuration it should be an integer"
                )
            num = entry["num"]

        if "sizes" in entry:
            for _ in range(num):
                ram_list(l, entry["sizes"])
            return
        else:
            raise RuntimeError(
                "dictionaries in continuous ram configuration sections should at least have a sizes entry"
            )

    raise RuntimeError(
        "entries in ram configuration should either be integer, lists, or dictionaries"
    )


def load_ram_configuration(memory_ss: MemorySS, mem: hjson.OrderedDict):
    """
    Reads the whole ram configuration.

    :param MemorySS memory_ss: the memory_ss object where the ram should be added.
    :param hjson.OrderedDict mem: The configuration part with the ram informations.
    :raise TypeError: when arguments do not have the right type
    :raise RuntimeError: when an invalid configuration is processed.
    """
    if not isinstance(memory_ss, MemorySS):
        raise TypeError("memory_ss should be an instance of MemorySS")
    if type(mem) is not hjson.OrderedDict:
        raise TypeError("mem should be of type hjson.OrderedDict")

    for key, value in mem.items():
        if type(value) is not hjson.OrderedDict:
            raise RuntimeError("Ram configuration entries should be dictionaries")

        section_name = ""
        if "auto_section" in value and value["auto_section"] == "auto":
            section_name = key

        t = "continuous"
        if "type" in value:
            t = value["type"]
            if type(t) is not str:
                raise TypeError("ram type should be a string")
            if t != "continuous" and t != "interleaved":
                raise RuntimeError(
                    f"ram type should be continuous or interleaved not {t}"
                )

        if t == "interleaved":
            if "num" not in value or type(value["num"]) is not int:
                raise RuntimeError(
                    "The num field is required for interleaved ram section and should be an integer"
                )

            if "size" not in value or type(value["size"]) is not int:
                raise RuntimeError(
                    "The size field is required for interleaved ram section and should be an integer"
                )

            memory_ss.add_ram_banks_il(
                int(value["num"]), int(value["size"]), section_name
            )

        elif t == "continuous":
            banks: List[int] = []
            ram_list(banks, value)
            memory_ss.add_ram_banks(banks, section_name)


def load_linker_config(memory_ss: MemorySS, config: list):
    """
    Reads the whole linker section configuration.

    :param MemorySS memory_ss: the memory_ss object where the sections should be added.
    :param hjson.OrderedDict mem: The configuration part with the section informations.
    :raise TypeError: when arguments do not have the right type
    :raise RuntimeError: when an invalid configuration is processed.
    """
    if type(config) is not list:
        raise TypeError("Linker Section configuraiton should be a list.")

    for l in config:
        if type(l) is not hjson.OrderedDict:
            raise TypeError("Sections should be represented as Dictionaries")
        if "name" not in l:
            raise RuntimeError("All sections should have names")

        if "start" not in l:
            raise RuntimeError("All sections should have a start")

        name = l["name"]
        start = to_int(l["start"])

        if type(name) is not str:
            raise TypeError("Section names should be strings")

        if name == "":
            raise RuntimeError("Section names should not be empty")

        if type(start) is not int:
            raise TypeError("The start of a section should be an integer")

        if "size" in l and "end" in l:
            raise RuntimeError("Each section should only specify end or size.")

        end = 0
        if "size" in l:
            size = to_int(l["size"])
            if size is None:
                raise RuntimeError("Section sizes should be an integer")
            if size <= 0:
                raise RuntimeError("Section sizes should be strictly positive")
            end = start + size

        elif "end" in l:
            end = to_int(l["end"])
            if end is None:
                raise RuntimeError("End address should be an integer")
            if end <= start:
                raise RuntimeError("Sections should end after their start")
        else:
            end = None

        memory_ss.add_linker_section(LinkerSection(name, start, end))


def _create_dma_peripheral(peripheral_config, offset, length):
    """
    Create DMA peripheral with its complex configuration.

    :param dict peripheral_config: DMA configuration
    :param int offset: Memory offset
    :param int length: Memory length
    :return: DMA peripheral instance
    """
    try:
        dma_is_included = (
            "yes" if peripheral_config.get("is_included", "yes") == "yes" else "no"
        )
    except (KeyError, AttributeError):
        dma_is_included = "yes"

    if dma_is_included == "yes":
        addr_mode_en = peripheral_config["addr_mode_en"]
        subaddr_mode_en = peripheral_config["subaddr_mode_en"]
        hw_fifo_mode_en = peripheral_config["hw_fifo_mode_en"]
        zero_padding_en = peripheral_config["zero_padding_en"]

        # Validate yes/no values
        for param_name, param_value in [
            ("addr_mode_en", addr_mode_en),
            ("subaddr_mode_en", subaddr_mode_en),
            ("hw_fifo_mode_en", hw_fifo_mode_en),
            ("zero_padding_en", zero_padding_en),
        ]:
            if param_value not in ["no", "yes"]:
                raise ValueError(f"{param_name} should be no or yes")

        ch_length = int(peripheral_config["ch_length"], 16)
        num_channels = int(peripheral_config["num_channels"], 16)
        num_master_ports = int(peripheral_config["num_master_ports"], 16)
        num_channels_per_master_port = int(
            peripheral_config["num_channels_per_master_port"], 16
        )
        fifo_depth = int(peripheral_config["fifo_depth"], 16)
    else:
        addr_mode_en = "no"
        subaddr_mode_en = "no"
        hw_fifo_mode_en = "no"
        zero_padding_en = "no"
        ch_length = int("0x100", 16)
        num_channels = int("0x1", 16)
        num_master_ports = int("0x1", 16)
        num_channels_per_master_port = int("0x1", 16)
        fifo_depth = int("0x4", 16)

    return DMA(
        is_included=dma_is_included,
        address=offset,
        length=length,
        ch_length=ch_length,
        num_channels=num_channels,
        num_master_ports=num_master_ports,
        num_channels_per_master_port=num_channels_per_master_port,
        fifo_depth=fifo_depth,
        addr_mode=addr_mode_en,
        subaddr_mode=subaddr_mode_en,
        hw_fifo_mode=hw_fifo_mode_en,
        zero_padding=zero_padding_en,
    )


def _create_peripheral_from_config(
    peripheral_name, peripheral_config, peripheral_factory_map
):
    """
    Create a peripheral instance from configuration.

    :param str peripheral_name: Name of the peripheral
    :param dict peripheral_config: Configuration dictionary for the peripheral
    :param dict peripheral_factory_map: Mapping of peripheral names to factory functions
    :return: Peripheral instance
    :raises ValueError: If peripheral doesn't exist in factory map
    """
    offset = int(peripheral_config["offset"], 16)
    length = int(peripheral_config["length"], 16)

    if peripheral_name not in peripheral_factory_map:
        raise ValueError(f"Peripheral {peripheral_name} does not exist.")

    factory = peripheral_factory_map[peripheral_name]

    # Special handling for DMA (has complex configuration)
    if peripheral_name == "dma":
        return factory(peripheral_config, offset, length)
    else:
        return factory(offset, length)


def _load_domain_peripherals(
    system,
    fields,
    domain_type,
    peripheral_factory_map,
    domain_constructor,
    are_configured_check,
    get_domain_attr,
):
    """
    Generic function to load peripherals into a domain from configuration.

    :param XHeep system: The system object
    :param dict fields: Configuration fields for the domain
    :param str domain_type: Type of domain ('base' or 'user')
    :param dict peripheral_factory_map: Mapping of peripheral names to factory functions
    :param callable domain_constructor: Constructor for the domain
    :param callable are_configured_check: Function to check if domain is already configured
    :param callable get_domain_attr: Function to get the domain attribute from system
    :return: None
    """
    domain = (
        domain_constructor(int(fields["address"], 16), int(fields["length"], 16))
        if not are_configured_check()
        else None
    )

    if domain is None:
        return

    # Iterate over all peripherals and create corresponding objects
    for peripheral_name, peripheral_config in fields.items():
        if peripheral_name in ["address", "length"]:
            continue

        # Skip if peripheral was already added by python configuration
        if are_configured_check() and get_domain_attr().contains_peripheral(
            peripheral_name
        ):
            continue

        # Check if peripheral should be included
        try:
            is_included = peripheral_config.get("is_included", "yes")
            # Special case for base peripherals: DMA is always included
            if (
                domain_type == "base"
                and peripheral_name != "dma"
                and is_included == "no"
            ):
                continue
            # For user peripherals, skip if not included
            if domain_type == "user" and is_included == "no":
                continue
        except (KeyError, AttributeError):
            pass

        # Create peripheral instance
        peripheral = _create_peripheral_from_config(
            peripheral_name, peripheral_config, peripheral_factory_map
        )

        # Add peripheral to domain
        domain.add_peripheral(peripheral)

    # All peripherals in configuration file have been added
    system.add_peripheral_domain(domain)


def load_peripherals_config(system: XHeep, config_path: str):
    """
    Reads the whole peripherals configuration.

    :param XHeep system: the system object where the peripherals should be added.
    :param str config_path: The path to the configuration file.
    :raise ValueError: If config file does not exist or if peripheral name doesn't match a peripheral class.
    """

    if not os.path.exists(config_path):
        raise ValueError(
            f"Peripherals configuration file {config_path} does not exist."
        )

    with open(config_path, "r") as file:
        try:
            srcfull = file.read()
            config = hjson.loads(srcfull, use_decimal=True)
            config = JsonRef.replace_refs(config)
        except ValueError:
            raise SystemExit(sys.exc_info()[1])

    # Define peripheral factory maps
    base_peripheral_factories = {
        "soc_ctrl": lambda o, l: SOC_ctrl(o, l),
        "bootrom": lambda o, l: Bootrom(o, l),
        "spi_flash": lambda o, l: SPI_flash(o, l),
        "spi_memio": lambda o, l: SPI_memio(o, l),
        "dma": _create_dma_peripheral,
        "power_manager": lambda o, l: Power_manager(o, l),
        "rv_timer_ao": lambda o, l: RV_timer_ao(o, l),
        "fast_intr_ctrl": lambda o, l: Fast_intr_ctrl(o, l),
        "ext_peripheral": lambda o, l: Ext_peripheral(o, l),
        "pad_control": lambda o, l: Pad_control(o, l),
        "gpio_ao": lambda o, l: GPIO_ao(o, l),
    }

    user_peripheral_factories = {
        "rv_plic": lambda o, l: RV_plic(o, l),
        "spi_host": lambda o, l: SPI_host(o, l),
        "gpio": lambda o, l: GPIO(o, l),
        "i2c": lambda o, l: I2C(o, l),
        "rv_timer": lambda o, l: RV_timer(o, l),
        "spi2": lambda o, l: SPI2(o, l),
        "pdm2pcm": lambda o, l: PDM2PCM(o, l),
        "i2s": lambda o, l: I2S(o, l),
        "uart": lambda o, l: UART(o, l),
    }

    for name, fields in config.items():
        # Base Peripherals
        if name == "ao_peripherals":
            _load_domain_peripherals(
                system=system,
                fields=fields,
                domain_type="base",
                peripheral_factory_map=base_peripheral_factories,
                domain_constructor=BasePeripheralDomain,
                are_configured_check=system.are_base_peripherals_configured,
                get_domain_attr=lambda: system._base_peripheral_domain,
            )

        # User Peripherals
        elif name == "peripherals":
            _load_domain_peripherals(
                system=system,
                fields=fields,
                domain_type="user",
                peripheral_factory_map=user_peripheral_factories,
                domain_constructor=UserPeripheralDomain,
                are_configured_check=system.are_user_peripherals_configured,
                get_domain_attr=lambda: system._user_peripheral_domain,
            )


def load_cfg_hjson(src: str) -> XHeep:
    """
    Loads the configuration passed as a hjson string and creates an object representing the mcu.

    :param str src: configuration content
    :return: the object representing the mcu configuration
    :rtype: XHeep
    :raise RuntimeError: when and invalid configuration is passed or when the sanity checks failed
    """
    config = hjson.loads(src, parse_int=int, object_pairs_hook=hjson.OrderedDict)
    mem_config = None
    bus_config = None
    linker_config = None

    cpu_config = None
    cve2_rv32e_config = None
    cve2_rv32m_config = None
    interrupts_config = None

    for key, value in config.items():
        if key == "ram_banks":
            mem_config = value
        elif key == "bus_type":
            bus_config = value
        elif key == "linker_sections":
            linker_config = value
        elif key == "cpu_type":
            cpu_config = value
        elif key == "cve2_rv32e":
            cve2_rv32e_config = value
        elif key == "cve2_rv32m":
            cve2_rv32m_config = value

    plic_used_n_interrupts = len(config["interrupts"]["list"])
    plic_n_interrupts = config["interrupts"]["number"]
    ext_int_list = {
        f"EXT_INTR_{k}": v
        for k, v in enumerate(range(plic_used_n_interrupts, plic_n_interrupts))
    }

    interrupts = {**config["interrupts"]["list"], **ext_int_list}

    if mem_config is None:
        raise RuntimeError("No memory configuration found")
    if bus_config is None:
        raise RuntimeError("No bus type configuration found")
    if interrupts is None:
        raise RuntimeError("No interrupts configuration found")

    system = XHeep(BusType(bus_config))
    memory_ss = MemorySS()
    system.add_interrupts_from_config_dict(dict(interrupts))

    load_ram_configuration(memory_ss, mem_config)

    if linker_config is not None:
        load_linker_config(memory_ss, linker_config)

    system.set_memory_ss(memory_ss)

    if cpu_config is not None:
        if cpu_config == "cv32e20":
            cpu = cv32e20(cve2_rv32e_config, cve2_rv32m_config)
        else:
            cpu = CPU(cpu_config)
        system.set_cpu(cpu)

    return system


def load_cfg_file(f: PurePath) -> XHeep:
    """
    Load the Configuration by extension type. It currently supports .hjson and .py

    :param PurePath f: path of the configuration
    :return: the object representing the mcu configuration
    :rtype: XHeep
    :raise RuntimeError: when and invalid configuration is passed or when the sanity checks failed
    """
    if not isinstance(f, PurePath):
        raise TypeError("parameter should be of type PurePath")

    if f.suffix == ".hjson":
        with open(f, "r") as file:
            return load_cfg_hjson(file.read())

    elif f.suffix == ".py":
        # The python script should have a function config() that takes no parameters and
        # returns an instance of the XHeep type.
        spec = importlib.util.spec_from_file_location("configs._config", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.config()

    else:
        raise RuntimeError(f"unsupported file extension {f.suffix}")


def load_pad_cfg(f: PurePath) -> PadRing:
    """
    Load the Configuration by extension type. It currently supports .hjson and .py

    :param PurePath f: path of the configuration
    :return: the object representing the mcu configuration
    :rtype: XHeep
    :raise RuntimeError: when and invalid configuration is passed or when the sanity checks failed
    """
    if not isinstance(f, PurePath):
        raise TypeError("parameter should be of type PurePath")

    if f.suffix == ".hjson":
        with open(f, "r") as file:
            try:
                srcfull = file.read()
                pad_cfg = hjson.loads(srcfull, use_decimal=True)
                pad_cfg = JsonRef.replace_refs(pad_cfg)
                pad_group = PadGroup.build_pad_group(pad_cfg, "x_heep_top")

                if pad_group is None:
                    raise ValueError(
                        "PadGroup could not be created from configuration."
                    )
                pad_ring = PadRing(pad_group)
                if pad_ring is None:
                    raise ValueError("PadRing could not be created from configuration.")
                return pad_ring
            except ValueError:
                raise SystemExit(sys.exc_info()[1])

    elif f.suffix == ".py":
        # The python script should have a function config() that takes no parameters and
        # returns an instance of the XHeep type.
        spec = importlib.util.spec_from_file_location("configs._config", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.config()

    else:
        raise RuntimeError(f"unsupported file extension {f.suffix}")
