"""
Pin-Pad Architecture Module (pin.py)

This module implements the Pin → Pad model where:
- Pins are logical signals with physical properties (layout, type)
- Pads are physical IO cells that inherit from their assigned pins
- Pins specify which pad(s) they connect to via global indices

Flow:
    1. Define pins with their pad assignments: Input("clk", [1], {})
    2. Generate blank pads: generate_padlist(pins, PAD_QTY)
    3. Pads inherit properties from assigned pins
    4. Assign sides by index ranges: assign_to_side(pads[1:24], LEFT)
    5. Calculate spacing: space_by_pitch(...)

Key classes:
    - Pin base classes: PinDigital, PinSupply, PinAnalog
    - Concrete pins: Input, Output, Inout, DVdd, DVss, AVdd, AVss, Asignal
    - Pad: Container that inherits from assigned pins
    - Physical: Non-signal pad ring components (PRCUTs, corners)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from enum import Enum
from collections import Counter

if TYPE_CHECKING:
    from .PadDef import Layout, Dimension


# =============================================================================
# Enums
# =============================================================================

class PadType(Enum):
    """Pad direction and behavior."""
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    BYPASS_INPUT = "bypass_input"
    BYPASS_OUTPUT = "bypass_output"
    BYPASS_INOUT = "bypass_inout"
    SUPPLY = "supply"


class PadMapping(Enum):
    """Physical side of the die."""
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


class Orientation(Enum):
    """Physical orientation/rotation of pad cell."""
    R0 = "R0"
    R90 = "R90"
    R180 = "R180"
    R270 = "R270"
    MX = "MX"
    MY = "MY"
    MX90 = "MX90"
    MY90 = "MY90"


class PadActive(Enum):
    """Active level for signals."""
    HIGH = "high"
    LOW = "low"


# =============================================================================
# Dimension and Layout (duplicated here for self-contained module)
# =============================================================================

@dataclass(frozen=True)
class Dimension:
    """Physical dimension specification."""
    width: float
    length: Optional[float] = None
    name: Optional[str] = None

    def __post_init__(self):
        if self.width < 0 or (self.length is not None and self.length < 0):
            raise ValueError(f"Dimensions must be positive: width={self.width}, length={self.length}")


@dataclass
class Layout:
    """Physical layout attributes for a pad."""
    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    offset: Optional[float] = None
    skip: Optional[float] = None
    bp_spacing: Optional[float] = None

    def copy(self) -> "Layout":
        return Layout(
            bond_pad=self.bond_pad,
            cell_pad=self.cell_pad,
            offset=self.offset,
            skip=self.skip,
            bp_spacing=self.bp_spacing,
        )


# =============================================================================
# Default Dimensions (configurable per technology)
# =============================================================================

class PadDimensions:
    """
    Container for technology-specific pad dimensions.

    Override these for your specific pad library/technology.
    """
    # Bond pads
    bp_analog = Dimension(width=50, length=71, name="BP_ANALOG")
    bp_digital = Dimension(width=50, length=71, name="BP_DIGITAL")
    bp_skip = Dimension(width=50, length=71, name=None)  # No bondpad

    # Digital pad cells
    pad_digital = Dimension(width=55, length=75, name="PAD_DIGITAL")
    pad_clock = Dimension(width=55, length=75, name="PAD_CLOCK")
    pad_dvdd = Dimension(width=55, length=75, name="PAD_DVDD")
    pad_iovdd = Dimension(width=55, length=75, name="PAD_IOVDD")
    pad_iopoc = Dimension(width=55, length=75, name="PAD_IOPOC")
    pad_dvss = Dimension(width=55, length=75, name="PAD_DVSS")

    # Analog pad cells
    pad_analog = Dimension(width=50, length=75, name="PAD_ANALOG")
    pad_avdd = Dimension(width=50, length=75, name="PAD_AVDD")
    pad_avss = Dimension(width=50, length=75, name="PAD_AVSS")

    # Physical structures
    prcut_analog = Dimension(width=25, length=75, name="PRCUT_ANALOG")
    prcut_digital = Dimension(width=25, length=75, name="PRCUT_DIGITAL")
    corner_analog = Dimension(width=75, length=75, name="CORNER_ANALOG")
    corner_digital = Dimension(width=75, length=75, name="CORNER_DIGITAL")

    # Skip placeholders
    pad_skip = Dimension(width=55, length=75, name=None)


# Global instance - users can replace or modify
dims = PadDimensions()


# =============================================================================
# Pin Base Classes
# =============================================================================

class Pin:
    """
    Base class for all pins.

    A Pin represents a logical signal with:
    - name: Signal name
    - pads: List of global pad indices this pin connects to
    - type: Direction (INPUT/OUTPUT/INOUT/SUPPLY)
    - layout: Physical dimensions (bond_pad, cell_pad)
    - Additional attributes (active, driven_manually, priority, etc.)
    """

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any]):
        self.name = name
        self.pads = pads
        self.properties: Dict[str, Any] = {}

        # Apply additional attributes
        for key, value in attr.items():
            setattr(self, key, value)

    @property
    def pad_cell(self) -> str:
        """RTL path to the pad cell instance."""
        return f"u_pad_cell_{self.type.value}/pad_{self.type.value}_i"


class PinDigital(Pin):
    """Digital signal pin (Input, Output, or Inout)."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any]):
        self.layout = Layout(bond_pad=dims.bp_digital, cell_pad=dims.pad_digital)
        super().__init__(name, pads, attr)
        self._pad_cell = f"u_pad_cell_{self.type.value}/pad_{self.type.value}_i"

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


class Input(PinDigital):
    """Digital input pin."""
    type = PadType.INPUT

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        super().__init__(name, pads, attr or {})


class Output(PinDigital):
    """Digital output pin."""
    type = PadType.OUTPUT

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        super().__init__(name, pads, attr or {})


class Inout(PinDigital):
    """Digital bidirectional pin."""
    type = PadType.INOUT

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        super().__init__(name, pads, attr or {})


# =============================================================================
# Supply Pin Classes
# =============================================================================

class PinSupply(Pin):
    """Power supply pin (VDD, VSS)."""
    type = PadType.SUPPLY

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any]):
        self.properties = {}
        super().__init__(name, pads, attr)
        if not hasattr(self, '_pad_cell'):
            self._pad_cell = "u_pad_cell_supply/pad_supply_i"

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


class DVdd(PinSupply):
    """Digital core VDD supply."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_digital, cell_pad=dims.pad_dvdd)
        super().__init__(name, pads, attr or {})


class DVddIO(PinSupply):
    """Digital IO VDD supply."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_digital, cell_pad=dims.pad_iovdd)
        super().__init__(name, pads, attr or {})


class DVddPOC(PinSupply):
    """Digital IO VDD with power-on-control."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_digital, cell_pad=dims.pad_iopoc)
        super().__init__(name, pads, attr or {})


class DVss(PinSupply):
    """Digital VSS (ground) supply."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_digital, cell_pad=dims.pad_dvss)
        super().__init__(name, pads, attr or {})


# =============================================================================
# Analog Pin Classes
# =============================================================================

class PinAnalog(Pin):
    """Analog signal or supply pin."""
    type = PadType.SUPPLY  # Analog pins are typically not driven by digital logic

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any]):
        self.properties = {}
        self.driven_manually = True  # Analog pins are always manually driven
        super().__init__(name, pads, attr)


class AVdd(PinAnalog):
    """Analog VDD supply."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_analog, cell_pad=dims.pad_avdd)
        self._pad_cell = "u_pad_cell_analog_vdd"
        super().__init__(name, pads, attr or {})

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


class AVss(PinAnalog):
    """Analog VSS (ground) supply."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_analog, cell_pad=dims.pad_avss)
        self._pad_cell = "u_pad_cell_analog_vss"
        super().__init__(name, pads, attr or {})

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


class Asignal(PinAnalog):
    """Analog signal pin."""

    def __init__(self, name: str, pads: List[int], attr: Dict[str, Any] = None):
        self.layout = Layout(bond_pad=dims.bp_analog, cell_pad=dims.pad_analog)
        self._pad_cell = "u_pad_cell_analog"
        super().__init__(name, pads, attr or {})

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


# =============================================================================
# Physical Components (non-signal pad ring elements)
# =============================================================================

class Physical:
    """
    Physical pad ring component (PRCUT, filler, etc.).

    These are not signals - they're structural elements in the pad ring.
    """
    type = PadType.SUPPLY
    driven_manually = True

    def __init__(
        self,
        name: str,
        layout: Layout,
        side: PadMapping,
        orient: Orientation,
        layout_index: float,
        offset: Optional[float] = None,
        space: Optional[float] = None,
        bp_space: Optional[float] = None,
    ):
        self.name = name
        self.layout = layout
        self.mapping = side
        self.orient = orient
        self.layout_index = layout_index
        self.global_index = 0  # Assigned later
        self.alts: List[Tuple[str, Pin]] = []
        self.offset = offset
        self.space = space
        self.bp_space = bp_space
        self._pad_cell = "u_pad_cell_supply/pad_supply_i"

    @property
    def pad_cell(self) -> str:
        return self._pad_cell


# =============================================================================
# Pad Class (container that inherits from pins)
# =============================================================================

class Pad:
    """
    Physical pad that inherits properties from assigned pins.

    Pads start as blank containers with just a global_index.
    When pins are assigned, pads inherit their properties.
    """

    def __init__(self, global_index: int):
        self.global_index = global_index
        self.alts: List[Tuple[str, Pin]] = []  # (name, pin) pairs
        self.offset: Optional[float] = None
        self.space: Optional[float] = None
        self.bp_space: Optional[float] = None

        # These are set during fix_assignment
        self.name: Optional[str] = None
        self.type: Optional[PadType] = None
        self.layout: Optional[Layout] = None
        self.mapping: Optional[PadMapping] = None
        self.layout_index: Optional[int] = None
        self.orient: Optional[Orientation] = None
        self._pad_cell: Optional[str] = None

    def fix_assignment(self, default_pin: Pin) -> None:
        """
        Finalize pad assignment by inheriting from assigned pins.

        If no pins assigned, uses default_pin.
        If multiple pins, becomes a MultiplexedPad.
        """
        # Handle unassigned pads
        if len(self.alts) == 0:
            self.alts.append((default_pin.name, default_pin))
            print(f"\033[33mFloating pad:\033[0m {self.global_index}, assigning to {default_pin.name}")

        # Sort by priority (higher priority first)
        self.alts = sorted(
            self.alts,
            key=lambda pin: getattr(pin[1], 'priority', 0),
            reverse=True
        )

        # Inherit attributes from primary pin
        self._flatten_attr(self.alts[0][1])

        # Determine pad type
        if self.alts and all(p[1].type == self.alts[0][1].type for p in self.alts):
            self.type = self.alts[0][1].type
        else:
            self.type = PadType.INOUT  # Mixed types default to INOUT

        # Set pad_cell for digital pins
        if isinstance(self.alts[0][1], PinDigital):
            self._pad_cell = f"u_pad_cell_{self.type.value}/pad_{self.type.value}_i"

        print(f"{self.global_index}: {[a[0] for a in self.alts]} | {self.type.value}")

    def _flatten_attr(self, pin: Pin) -> None:
        """Copy attributes from pin to pad."""
        # Get list of properties defined on Pad class to avoid conflicts
        pad_properties = {name for name in dir(Pad)
                         if isinstance(getattr(Pad, name, None), property)}

        for key, value in vars(pin).items():
            if not key.startswith('_') and key not in pad_properties:
                setattr(self, key, value)

    @property
    def pad_cell(self) -> str:
        return self._pad_cell or "u_pad_cell_unknown"

    @property
    def cell_name(self) -> str:
        """Pad cell instance name for templates."""
        return f"pad_{self.name}_i" if self.name else "pad_unknown_i"

    @property
    def signal_name(self) -> str:
        """Signal name for RTL generation."""
        if self.name:
            # Check for active_low attribute
            active_low = getattr(self, 'active_low', False) or (
                hasattr(self, 'active') and getattr(self, 'active', 'high') == 'low'
            )
            suffix = "n_" if active_low else "_"
            return f"{self.name}{suffix}"
        return "unknown_"

    @property
    def io_interface(self) -> str:
        """IO interface signal name."""
        return f"{self.signal_name}io"

    @property
    def pad_type(self) -> str:
        """Pad type as string for templates."""
        if self.type:
            return self.type.value
        return "unknown"

    @property
    def is_muxed(self) -> bool:
        return len(self.alts) > 1

    @property
    def attribute_bits(self) -> str:
        """Attribute bits for pad configuration."""
        # Default to empty attributes if not specified
        return getattr(self, '_attribute_bits', '0:0')

    @property
    def has_attribute(self) -> bool:
        """Whether this pad has attributes."""
        return hasattr(self, '_attribute_bits') and self._attribute_bits != '0:0'

    @property
    def localparam(self) -> str:
        """SystemVerilog localparam name."""
        return f"PAD_{self.name.upper()}" if self.name else "PAD_UNKNOWN"

    @property
    def pad_mapping(self):
        """Alias for mapping (template compatibility)."""
        return self.mapping

    # -------------------------------------------------------------------------
    # Properties for multiplexed pads (template compatibility)
    # -------------------------------------------------------------------------

    @property
    def pad_type_drive(self) -> List[str]:
        """List of pad types for each alternative pin."""
        if self.alts:
            return [pin.type.value for _, pin in self.alts]
        return [self.pad_type]

    @property
    def signal_name_drive(self) -> List[str]:
        """List of signal names for each alternative pin."""
        if self.alts:
            result = []
            for name, pin in self.alts:
                # Check for active_low
                active_low = getattr(pin, 'active_low', False) or (
                    hasattr(pin, 'active') and getattr(pin, 'active', 'high') == 'low'
                )
                suffix = "n_" if active_low else "_"
                result.append(f"{name}{suffix}")
            return result
        return [self.signal_name]

    @property
    def driven_manually(self) -> List[bool]:
        """List of driven_manually flags for each alternative pin."""
        if self.alts:
            return [getattr(pin, 'driven_manually', False) for _, pin in self.alts]
        return [False]  # Fallback (shouldn't happen - alts always has at least default)

    @property
    def skip_declaration(self) -> List[bool]:
        """List of skip_declaration flags for each alternative pin."""
        if self.alts:
            # Check both 'skip_declaration' and 'skip' attributes
            result = []
            for _, pin in self.alts:
                skip = getattr(pin, 'skip_declaration', getattr(pin, 'skip', False))
                result.append(skip)
            return result
        return [False]  # Fallback (shouldn't happen - alts always has at least default)


# =============================================================================
# Pad Generation Functions
# =============================================================================

def generate_padlist(
    pins: Dict[str, Pin],
    pad_qty: int,
    default_pin: Pin
) -> List[Optional[Pad]]:
    """
    Generate a list of pads from pin definitions.

    Args:
        pins: Dictionary of pin_name -> Pin object
        pad_qty: Total number of pads
        default_pin: Pin to use for unassigned pads

    Returns:
        List of Pad objects, with index 0 = None (so pads[1] is pad #1)
    """
    # Create pad list with None at index 0 for 1-based indexing
    pads: List[Optional[Pad]] = [None]
    for global_index in range(1, pad_qty + 1):
        pads.append(Pad(global_index))

    # Assign pins to pads
    for pin in pins.values():
        if not pin.pads:
            print(f"\033[33mUnconnected pin:\033[0m {pin.name}")
        else:
            for pad_idx in pin.pads:
                if 1 <= pad_idx <= pad_qty:
                    pads[pad_idx].alts.append((pin.name, pin))

    # Finalize assignments
    for pad in pads[1:]:
        pad.fix_assignment(default_pin)

    # Handle duplicate names
    _rename_duplicate_pads(pads[1:])

    return pads


def _rename_duplicate_pads(pads: List[Pad]) -> None:
    """Rename pads with duplicate names by adding _1, _2, etc."""
    # Ensure all pads have names
    for pad in pads:
        if not hasattr(pad, 'name') or pad.name is None:
            pad.name = f"NC_{getattr(pad, 'global_index', 'unknown')}"

    # Count name frequencies
    counts = Counter(pad.name for pad in pads)

    # Apply indexing to duplicates
    seen: Dict[str, int] = {}
    for pad in pads:
        original_name = pad.name
        if counts[original_name] > 1:
            seen[original_name] = seen.get(original_name, 0) + 1
            pad.name = f"{original_name}_{seen[original_name]}"


def assign_to_side(pads: List[Pad], side: PadMapping) -> None:
    """
    Assign a list of pads to a die side with appropriate orientation.

    Layout indexes are assigned sequentially (0, 1, 2, ...).
    Orientation is set based on side (standard counter-clockwise convention).
    """
    orientations = {
        PadMapping.TOP: Orientation.R0,
        PadMapping.RIGHT: Orientation.R270,
        PadMapping.BOTTOM: Orientation.R180,
        PadMapping.LEFT: Orientation.R90,
    }

    for idx, pad in enumerate(pads):
        pad.mapping = side
        pad.layout_index = idx
        pad.orient = orientations.get(side, Orientation.R0)


def space_by_pitch(
    pads: List[Pad],
    margins: List[float],
    space_from_corner: float,
    pitch: float
) -> None:
    """
    Calculate pad spacing based on bondpad pitch.

    Args:
        pads: List of pads on one side
        margins: Ring margins [0, sealring, CDU, bondpad, pad]
        space_from_corner: Extra space from corner cell
        pitch: Bondpad pitch
    """
    if not pads:
        return

    # Sort by layout_index
    pads_sorted = sorted(pads, key=lambda x: x.layout_index)

    side_io_margin = margins[4]  # Pad margin
    side_bp_margin = margins[3]  # Bondpad margin

    # Assume corner length equals pad length
    corner_length = pads_sorted[0].layout.cell_pad.length

    # First pad spacing from corner
    pads_sorted[0].space = space_from_corner
    pads_sorted[0].pc_center_from_ring = (
        corner_length + space_from_corner + pads_sorted[0].layout.cell_pad.width / 2
    )

    # Calculate spacing for remaining pads
    for i, pad in enumerate(pads_sorted[1:], start=1):
        prev_pad = pads_sorted[i - 1]

        if hasattr(pad, 'pc_center_from_ring'):
            # Hardcoded position - calculate space from it
            space = (
                pad.pc_center_from_ring - prev_pad.pc_center_from_ring
                - prev_pad.layout.cell_pad.width / 2
                - pad.layout.cell_pad.width / 2
            )
        elif "PRCUT" in getattr(pad, 'name', ''):
            space = 0
        elif "PRCUT" in getattr(prev_pad, 'name', ''):
            # After PRCUT, maintain pitch from last non-PRCUT
            space = max(pitch - prev_pad.layout.cell_pad.width - pad.layout.cell_pad.width / 2, 0)
        else:
            space = pitch - prev_pad.layout.cell_pad.width / 2 - pad.layout.cell_pad.width / 2

        pad.space = space
        pad.pc_center_from_ring = (
            prev_pad.pc_center_from_ring
            + prev_pad.layout.cell_pad.width / 2
            + space
            + pad.layout.cell_pad.width / 2
        )

    # Calculate bondpad positions
    margin_diff = side_io_margin - side_bp_margin
    width_diff = pads_sorted[0].layout.cell_pad.width - pads_sorted[0].layout.bond_pad.width
    first_bp_offset = margin_diff + corner_length + space_from_corner + width_diff / 2

    pads_sorted[0].offset = first_bp_offset
    pads_sorted[0].bp_space = 0
    pads_sorted[0].bp_center_from_ring = first_bp_offset + pads_sorted[0].layout.bond_pad.width / 2

    last_bp = 0
    for i, pad in enumerate(pads_sorted[1:], start=1):
        pad_cell_center = pad.pc_center_from_ring
        bond_pad_center = pad_cell_center + margin_diff
        pad.bp_center_from_ring = bond_pad_center

        if pad.layout.bond_pad.name is not None:
            distance = bond_pad_center - pads_sorted[last_bp].bp_center_from_ring
            space = (
                distance
                - pads_sorted[last_bp].layout.bond_pad.width / 2
                - pad.layout.bond_pad.width / 2
            )
            pad.bp_space = space
            last_bp = i


# =============================================================================
# Debug/Visualization Functions
# =============================================================================

def print_pad_frame(pads: List[Pad]) -> None:
    """Print ASCII art representation of pad ring."""
    print("\n")

    top = sorted([p for p in pads if p.mapping == PadMapping.TOP], key=lambda x: x.layout_index, reverse=True)
    bottom = sorted([p for p in pads if p.mapping == PadMapping.BOTTOM], key=lambda x: x.layout_index)
    left = sorted([p for p in pads if p.mapping == PadMapping.LEFT], key=lambda x: x.layout_index)
    right = sorted([p for p in pads if p.mapping == PadMapping.RIGHT], key=lambda x: x.layout_index, reverse=True)

    height = max(len(left), len(right))

    def fmt(pad):
        return f"[{pad.global_index:3}]" if pad else "     "

    # Top row
    print("      " + "".join(fmt(p) for p in top))

    # Middle rows
    for i in range(height):
        l_pad = left[i] if i < len(left) else None
        r_pad = right[i] if i < len(right) else None
        middle_gap = "     " * len(top)
        print(f"{fmt(l_pad)}{middle_gap}{fmt(r_pad)}")

    # Bottom row
    print("      " + "".join(fmt(p) for p in bottom))
    print("\n")


def print_pad_table(pads: List[Pad]) -> None:
    """Print table of pad assignments by side and layout index."""
    print("\n")

    rows: Dict[int, Dict[PadMapping, str]] = {}
    for pad in pads:
        idx = pad.layout_index
        if idx not in rows:
            rows[idx] = {PadMapping.LEFT: '', PadMapping.BOTTOM: '', PadMapping.RIGHT: '', PadMapping.TOP: ''}

        pin_names = f"({pad.global_index}) " + ", ".join([a[0] for a in pad.alts]) if pad.alts else f"({pad.global_index}) {pad.name}"
        rows[idx][pad.mapping] = pin_names

    # Header
    header = f"{'Idx':<4} | {'left':<40} | {'bottom':<40} | {'right':<40} | {'top':<40}"
    print(header)
    print("-" * len(header))

    # Rows
    for idx in sorted(rows.keys()):
        r = rows[idx]
        print(f"{idx:<4} | {r[PadMapping.LEFT]:<40} | {r[PadMapping.BOTTOM]:<40} | {r[PadMapping.RIGHT]:<40} | {r[PadMapping.TOP]:<40}")
    print("\n")


# =============================================================================
# PadConfig - High-level configuration interface
# =============================================================================

class PadConfig:
    """
    High-level interface for configuring pad assignments (logical placement).

    PadConfig handles LOGICAL placement - which pins go where on each side.
    Physical spacing (offset, space, bp_space) is calculated separately using
    space_by_pitch() after build().

    Separation of concerns:
    - PadConfig: Logical placement (side + position assignment)
    - space_by_pitch(): Physical layout (spacing, margins, pitch)
    - Pin classes: Physical properties (bondpad dims, cell pad dims)
    - Pad class: Container that inherits everything

    Usage:
        cfg = PadConfig(pad_qty=92, sides=[23, 23, 23, 23])

        # Create pins with physical attributes
        clk = Input("clk", [], {"driven_manually": True})
        vss = DVss("VSS", [], {"default": True})

        # Place pins (logical)
        cfg.place(clk, side="left", position=0)
        cfg.place_multiple(vss, side="left", positions=[2, 5, 10])
        cfg.place_peripheral(uart, pins_dict, side="bottom")

        # Set default and build
        cfg.set_default(vss)
        pads = cfg.build()

        # Calculate physical spacing (separate step)
        left_pads = [p for p in pads[1:] if p.mapping == PadMapping.LEFT]
        space_by_pitch(left_pads, margins=[...], space_from_corner=20, pitch=65)
    """

    def __init__(self, pad_qty: int, sides: List[int]):
        """
        Initialize pad configuration.

        Args:
            pad_qty: Total number of pads on the die
            sides: [left_count, bottom_count, right_count, top_count]
        """
        if sum(sides) != pad_qty:
            raise ValueError(f"Side counts {sides} don't sum to pad_qty {pad_qty}")

        self.pad_qty = pad_qty
        self.sides = sides
        self.side_ranges = self._calculate_side_ranges()

        # Track all pins that have been placed
        self.pins: Dict[str, Pin] = {}

        # Track next available position per side (for "auto")
        self.next_position = {
            PadMapping.LEFT: 0,
            PadMapping.BOTTOM: 0,
            PadMapping.RIGHT: 0,
            PadMapping.TOP: 0,
        }

        self.default_pin: Optional[Pin] = None

    def _calculate_side_ranges(self) -> Dict[PadMapping, Tuple[int, int]]:
        """Calculate global index ranges for each side (counter-clockwise from left)."""
        start = 1
        ranges = {}
        ranges[PadMapping.LEFT] = (start, start + self.sides[0] - 1)
        start += self.sides[0]
        ranges[PadMapping.BOTTOM] = (start, start + self.sides[1] - 1)
        start += self.sides[1]
        ranges[PadMapping.RIGHT] = (start, start + self.sides[2] - 1)
        start += self.sides[2]
        ranges[PadMapping.TOP] = (start, start + self.sides[3] - 1)
        return ranges

    def _side_to_global(self, side: PadMapping, position: int) -> int:
        """Convert side + local position to global pad index."""
        start, end = self.side_ranges[side]
        global_idx = start + position
        if global_idx > end:
            raise ValueError(f"Position {position} exceeds {side.value} side capacity (max {end - start})")
        return global_idx

    def place(self, pin: Pin, side: PadMapping, position: Any = "auto") -> None:
        """
        Place a single pin on a die side.

        Args:
            pin: Pin object to place
            side: Die side (LEFT/BOTTOM/RIGHT/TOP)
            position: Exact position (0-based on side) or "auto" for next available
        """
        # Handle position="auto"
        if position == "auto":
            position = self.next_position[side]
            self.next_position[side] += 1

        # Convert to global index
        global_idx = self._side_to_global(side, position)

        # Update pin's pads list
        if global_idx not in pin.pads:
            pin.pads.append(global_idx)

        # Track pin in our dictionary
        if pin.name not in self.pins:
            self.pins[pin.name] = pin

    def place_multiple(self, pin: Pin, side: PadMapping, positions: List[int]) -> None:
        """
        Place a single pin at multiple positions (useful for supply pins).

        Args:
            pin: Pin object to place (typically a supply)
            side: Die side
            positions: List of exact positions on that side
        """
        for pos in positions:
            self.place(pin, side, position=pos)

    def place_peripheral(
        self,
        peripheral,
        pins_dict: Dict[str, Pin],
        side: PadMapping,
        start_position: Optional[int] = None
    ) -> None:
        """
        Place all pins from a peripheral sequentially on a side.

        Args:
            peripheral: Peripheral object with get_pins() method
            pins_dict: Dictionary of pin_name -> Pin objects
            side: Die side to place on
            start_position: Starting position (defaults to next available)
        """
        if start_position is None:
            start_position = self.next_position[side]

        current_pos = start_position
        for pin_name in peripheral.get_pins():
            if pin_name in pins_dict:
                self.place(pins_dict[pin_name], side, position=current_pos)
                current_pos += 1
            else:
                print(f"Warning: Peripheral pin '{pin_name}' not found in pins_dict")

    def set_default(self, pin: Pin) -> None:
        """Set default pin for unassigned pads."""
        self.default_pin = pin
        if pin.name not in self.pins:
            self.pins[pin.name] = pin

    def get_free_positions(self, side: PadMapping) -> List[int]:
        """
        Get list of free (unassigned) positions on a side.

        Returns:
            List of available positions (0-based on that side)
        """
        start, end = self.side_ranges[side]

        # Collect all used global indices on this side
        used_global = set()
        for pin in self.pins.values():
            for idx in pin.pads:
                if start <= idx <= end:
                    used_global.add(idx)

        # Convert to local positions
        free_positions = []
        for local_pos in range(end - start + 1):
            global_idx = start + local_pos
            if global_idx not in used_global:
                free_positions.append(local_pos)

        return free_positions

    def validate(self) -> bool:
        """Check for configuration issues."""
        issues = []

        if self.default_pin is None:
            issues.append("No default pin set (use cfg.set_default())")

        # Check for unconnected pins
        for pin in self.pins.values():
            if not pin.pads and pin != self.default_pin:
                issues.append(f"Pin '{pin.name}' has no pad assignments")

        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        return True

    def print_summary(self) -> None:
        """Print summary of current configuration."""
        print("\n" + "="*70)
        print("Pad Configuration Summary")
        print("="*70)
        print(f"Total pads: {self.pad_qty}")
        print(f"Side distribution: LEFT={self.sides[0]}, BOTTOM={self.sides[1]}, "
              f"RIGHT={self.sides[2]}, TOP={self.sides[3]}")
        print(f"Total pins: {len(self.pins)}")
        print(f"Default pin: {self.default_pin.name if self.default_pin else 'NOT SET'}")

        print("\nPins per side:")
        for side in [PadMapping.LEFT, PadMapping.BOTTOM, PadMapping.RIGHT, PadMapping.TOP]:
            start, end = self.side_ranges[side]
            count = sum(1 for pin in self.pins.values() for idx in pin.pads if start <= idx <= end)
            free = len(self.get_free_positions(side))
            print(f"  {side.value.upper():<8}: {count} assigned, {free} free")

        print("="*70 + "\n")

    def build(self) -> List[Optional[Pad]]:
        """
        Generate final pad list compatible with PadRing.

        Returns:
            List of Pad objects with index 0 = None (1-based indexing)
        """
        if not self.validate():
            raise ValueError("Configuration validation failed - cannot build pads")

        # Generate pads using existing infrastructure
        pads = generate_padlist(self.pins, self.pad_qty, self.default_pin)

        # Assign sides using calculated ranges
        for side in [PadMapping.LEFT, PadMapping.BOTTOM, PadMapping.RIGHT, PadMapping.TOP]:
            start, end = self.side_ranges[side]
            assign_to_side(pads[start:end+1], side)

        return pads
