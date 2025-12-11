"""
Peripheral Configuration Loader Module

This module provides functionality for loading and configuring peripheral devices
from HJSON configuration files into the X-HEEP system.

ARCHITECTURAL RATIONALE:
=======================

This module was created to separate peripheral-specific configuration loading
logic from the general system configuration loader. This separation provides
several architectural benefits:

1. SINGLE RESPONSIBILITY PRINCIPLE
   - This module has ONE job: transform peripheral configuration data into
     peripheral domain objects
   - load_config.py handles system-wide configuration orchestration
   - Each module has a clear, focused purpose

2. COHESION
   - All peripheral loading logic is co-located with peripheral domain classes
   - Peripheral-specific knowledge (DMA complexity, factory patterns) stays
     within the peripheral subsystem
   - Reduces cognitive load: developers working on peripherals find all
     related code in one place

3. ENCAPSULATION
   - Peripheral loading details are hidden from the main system configuration
   - Changes to peripheral loading (e.g., new peripheral types) don't affect
     the main configuration loader
   - Factory pattern implementation is encapsulated here

4. TESTABILITY
   - Peripheral loading can be tested independently from system configuration
   - Mock XHeep objects can be used without loading entire system configs
   - Unit tests can focus on peripheral-specific logic

5. EXTENSIBILITY
   - Adding new peripheral types requires changes only to this module
   - New peripheral factories can be added without touching load_config.py
   - Supports future plugin architectures for custom peripherals

6. DEPENDENCY MANAGEMENT
   - Reduces coupling between system configuration and peripheral subsystem
   - load_config.py depends on this module, not vice versa
   - Clear dependency direction: System -> Peripherals (not bidirectional)

DESIGN PATTERNS USED:
=====================

1. FACTORY PATTERN
   - Peripheral factories map peripheral names to constructor functions
   - Abstracts peripheral instantiation from configuration logic
   - Allows for flexible peripheral creation strategies

2. STRATEGY PATTERN
   - Different peripheral types use different creation strategies
   - DMA uses complex configuration strategy
   - Standard peripherals use simple strategy
   - Strategy is selected based on peripheral type

3. TEMPLATE METHOD PATTERN
   - _load_domain_peripherals provides template for loading any domain
   - Subclasses/callers provide domain-specific parameters
   - Common workflow enforced, customization points provided

USAGE:
======

from x_heep_gen.peripherals.peripheral_config_loader import load_peripherals_config
from x_heep_gen.xheep import XHeep

system = XHeep(bus_type=BusType.NtoM)
load_peripherals_config(system, 'path/to/peripherals.hjson')

The loader will:
1. Parse the HJSON configuration file
2. Create peripheral factory maps for base and user peripherals
3. Instantiate peripheral objects using the factories
4. Organize peripherals into their respective domains
5. Add configured domains to the system object

:author: X-HEEP Team
:date: 2024
"""

import os
import sys
import hjson
from jsonref import JsonRef

# Import peripheral domain classes
from .base_peripherals_domain import BasePeripheralDomain
from .user_peripherals_domain import UserPeripheralDomain

# Import base peripheral classes
from .base_peripherals.SOC_ctrl import SOC_ctrl
from .base_peripherals.Bootrom import Bootrom
from .base_peripherals.SPI_flash import SPI_flash
from .base_peripherals.SPI_memio import SPI_memio
from .base_peripherals.DMA import DMA
from .base_peripherals.Power_manager import Power_manager
from .base_peripherals.RV_timer_ao import RV_timer_ao
from .base_peripherals.Fast_intr_ctrl import Fast_intr_ctrl
from .base_peripherals.Ext_peripheral import Ext_peripheral
from .base_peripherals.Pad_control import Pad_control
from .base_peripherals.GPIO_ao import GPIO_ao

# Import user peripheral classes
from .user_peripherals.RV_plic import RV_plic
from .user_peripherals.SPI_host import SPI_host
from .user_peripherals.GPIO import GPIO
from .user_peripherals.I2C import I2C
from .user_peripherals.RV_timer import RV_timer
from .user_peripherals.SPI2 import SPI2
from .user_peripherals.PDM2PCM import PDM2PCM
from .user_peripherals.I2S import I2S
from .user_peripherals.UART import UART


def _create_dma_peripheral(peripheral_config, offset, length):
    """
    Create DMA peripheral with its complex configuration.

    DMA peripherals require special handling because they have extensive
    configuration parameters beyond just memory offset and length. This
    factory function encapsulates all DMA-specific configuration logic.

    Configuration Parameters:
    -------------------------
    - is_included: Whether DMA is enabled (default: "yes")
    - addr_mode_en: Enable address mode (yes/no)
    - subaddr_mode_en: Enable subaddress mode (yes/no)
    - hw_fifo_mode_en: Enable hardware FIFO mode (yes/no)
    - zero_padding_en: Enable zero padding (yes/no)
    - ch_length: Length of each DMA channel (hex string)
    - num_channels: Number of DMA channels (hex string)
    - num_master_ports: Number of master ports (hex string)
    - num_channels_per_master_port: Channels per master port (hex string)
    - fifo_depth: Depth of FIFO buffer (hex string)

    When DMA is not included (is_included="no"), minimal default values
    are used to ensure the system can still be generated with a stubbed
    DMA peripheral.

    :param dict peripheral_config: DMA configuration dictionary
    :param int offset: Memory address offset for DMA peripheral
    :param int length: Memory length allocated to DMA peripheral
    :return: Configured DMA peripheral instance
    :rtype: DMA
    :raises ValueError: If mode parameters are not "yes" or "no"
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
        # Use minimal defaults when DMA is not included
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
    Create a peripheral instance from configuration using the factory pattern.

    This function acts as a dispatcher that:
    1. Extracts common parameters (offset, length) from config
    2. Validates the peripheral type exists
    3. Selects the appropriate factory function
    4. Invokes the factory with appropriate parameters

    The factory pattern allows for flexible peripheral creation:
    - Standard peripherals: factory(offset, length)
    - Complex peripherals (DMA): factory(config, offset, length)

    This design makes it easy to add new peripheral types without modifying
    the loading logic - just add a new entry to the factory map.

    :param str peripheral_name: Name of the peripheral (e.g., "uart", "dma")
    :param dict peripheral_config: Configuration dictionary for the peripheral
    :param dict peripheral_factory_map: Mapping of names to factory functions
    :return: Configured peripheral instance
    :rtype: BasePeripheral subclass
    :raises ValueError: If peripheral name doesn't exist in factory map
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

    This function implements the Template Method pattern, providing a common
    workflow for loading any peripheral domain while allowing customization
    through parameters.

    Workflow:
    ---------
    1. Create domain object (if not already configured)
    2. Iterate through peripheral configurations
    3. Skip metadata fields (address, length)
    4. Skip already-added peripherals (programmatic configuration)
    5. Check inclusion flags
    6. Create peripheral instances via factories
    7. Add peripherals to domain
    8. Add domain to system

    Special Rules:
    --------------
    - Base domain: DMA is always included (even if marked "no")
    - User domain: Peripherals marked "no" are skipped
    - Programmatic config takes precedence over file config

    This design supports both file-based and programmatic configuration,
    with programmatic taking priority. This is useful for:
    - Testing with mock peripherals
    - Runtime peripheral customization
    - Conditional peripheral inclusion

    :param XHeep system: The system object to populate
    :param dict fields: Configuration fields for the domain
    :param str domain_type: Type of domain ('base' or 'user')
    :param dict peripheral_factory_map: Mapping of names to factory functions
    :param callable domain_constructor: Constructor for the domain object
    :param callable are_configured_check: Function to check if domain exists
    :param callable get_domain_attr: Function to get domain from system
    :return: None (modifies system object in place)
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


def load_peripherals_config(system, config_path: str):
    """
    Load peripheral configuration from HJSON file into X-HEEP system.

    This is the main entry point for peripheral configuration loading.
    It orchestrates the entire loading process:

    1. File Loading and Parsing
       - Validates file existence
       - Parses HJSON (human-friendly JSON with comments)
       - Resolves JSON references ($ref pointers)

    2. Factory Map Definition
       - Creates base peripheral factories (always-on domain)
       - Creates user peripheral factories (user domain)
       - Maps peripheral names to constructor functions

    3. Domain Processing
       - Processes "ao_peripherals" (always-on/base domain)
       - Processes "peripherals" (user domain)
       - Delegates to _load_domain_peripherals for each

    Configuration File Structure:
    -----------------------------
    {
      "ao_peripherals": {
        "address": "0x20000000",
        "length": "0x10000",
        "soc_ctrl": { "offset": "0x0", "length": "0x1000" },
        "dma": { "offset": "0x1000", "length": "0x1000", ... }
      },
      "peripherals": {
        "address": "0x30000000",
        "length": "0x10000",
        "uart": { "offset": "0x0", "length": "0x1000" },
        "gpio": { "offset": "0x1000", "length": "0x1000" }
      }
    }

    Factory Pattern Benefits:
    ------------------------
    - Decouples peripheral creation from configuration logic
    - Easy to add new peripheral types
    - Supports different construction strategies per peripheral
    - Enables testing with mock factories

    Error Handling:
    --------------
    - File not found: ValueError with clear message
    - Parse errors: SystemExit with parse error details
    - Invalid peripherals: ValueError from factory lookup

    :param XHeep system: The system object to populate with peripherals
    :param str config_path: Path to the HJSON peripheral configuration file
    :return: None (modifies system object in place)
    :raises ValueError: If config file doesn't exist or peripheral invalid
    :raises SystemExit: If HJSON parsing fails
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
    # Base peripherals are always-on peripherals in the AO (Always On) domain
    base_peripheral_factories = {
        "soc_ctrl": lambda o, l: SOC_ctrl(o, l),
        "bootrom": lambda o, l: Bootrom(o, l),
        "spi_flash": lambda o, l: SPI_flash(o, l),
        "spi_memio": lambda o, l: SPI_memio(o, l),
        "dma": _create_dma_peripheral,  # Special handling for complex config
        "power_manager": lambda o, l: Power_manager(o, l),
        "rv_timer_ao": lambda o, l: RV_timer_ao(o, l),
        "fast_intr_ctrl": lambda o, l: Fast_intr_ctrl(o, l),
        "ext_peripheral": lambda o, l: Ext_peripheral(o, l),
        "pad_control": lambda o, l: Pad_control(o, l),
        "gpio_ao": lambda o, l: GPIO_ao(o, l),
    }

    # User peripherals are peripherals in the user-controllable domain
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
        # Base Peripherals (Always-On Domain)
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

        # User Peripherals (User Domain)
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
