"""
Pad Configuration Module (PadDef.py)

This module defines the configuration-time representation of pads and pad groups.
It provides classes and enums for describing pads in both Python and HJSON configurations.

Key classes:
    - PadDef: Configuration-time pad description
    - PadGroup: System-level pad configuration
    - RangePad: Generates multiple similar pads
    - MultiplexedPad: Pad with multiple mux options
    - Layout: Physical layout attributes
    - Dimension: Physical dimension specification

Key enums:
    - PadType: Direction and behavior (input/output/inout/etc.)
    - PadMapping: Physical location on die (top/bottom/left/right)
    - Orientation: Physical rotation (R0/R90/R180/R270/MX/MY)
    - PadActive: Active level (high/low)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple, Mapping, Any
from enum import Enum


class PadType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    BYPASS_INPUT = "bypass_input"
    BYPASS_OUTPUT = "bypass_output"
    BYPASS_INOUT = "bypass_inout"
    SUPPLY = "supply"


class PadMapping(Enum):
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


class Orientation(Enum):
    """
    Physical orientation/rotation of pad cell.

    Values:
        R0: No rotation (0 degrees)
        R90: 90 degree rotation
        R180: 180 degree rotation
        R270: 270 degree rotation
        MX: Mirror around X axis
        MY: Mirror around Y axis
        MX90: Mirror X + 90 degree rotation
        MY90: Mirror Y + 90 degree rotation
    """

    R0 = "R0"
    R90 = "R90"
    R180 = "R180"
    R270 = "R270"
    MX = "MX"
    MY = "MY"
    MX90 = "MX90"
    MY90 = "MY90"


class PadActive(Enum):
    HIGH = "high"
    LOW = "low"


VALID_TYPES = {t.value for t in PadType}

VALID_ORIENTATIONS = {o.value for o in Orientation}.union({None})
VALID_MAPPINGS = {m.value for m in PadMapping}

VALID_ACTIVES = {a.value for a in PadActive}

# -------------------------- Base model ---------------------------------------


class ValidationError(ValueError):
    """Exception raised when pad configuration validation fails."""

    pass


def _assert_type(t: str, where: str) -> None:
    """
    Validate that a value is a PadType enum.

    :param t: Value to validate
    :param str where: Context for error message
    :raises ValidationError: If validation fails
    """
    if not isinstance(t, PadType):
        raise ValidationError(f"{where}: invalid orientation is of type '{type(t)}'")


def _assert_mapping(m: str, where: str) -> None:
    """
    Validate that a value is a PadMapping enum or None.

    :param m: Value to validate
    :param str where: Context for error message
    :raises ValidationError: If validation fails
    """
    # is instance if PadMapping enum
    if m is not None and not isinstance(m, PadMapping):
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {list(PadMapping)}"
        )


def _assert_orientation(o: Any, where: str) -> None:
    """
    Validate that a value is an Orientation enum or None.

    :param o: Value to validate
    :param str where: Context for error message
    :raises ValidationError: If validation fails
    """
    if o is not None and not isinstance(o, Orientation):
        raise ValidationError(f"{where}: invalid orientation is of type '{type(o)}'")


@dataclass(frozen=True)
class Dimension:
    """
    Physical dimension specification for pads.

    Attributes:
        width: Width in micrometers (required)
        name: Optional name identifier for this dimension
        length: Optional length in micrometers

    Raises:
        ValidationError: If width or length are negative
    """

    width: int
    name: Optional[str] = None
    length: Optional[int] = None

    def __post_init__(self):
        if self.width < 0 or (self.length and self.length < 0):
            raise ValidationError(
                f"Dimension: width and length must be positive. Got width={self.width}, length={self.length}"
            )


@dataclass
class Layout:
    """
    Physical layout attributes for a pad.

    Attributes:
        bond_pad: Optional bond pad dimensions
        cell_pad: Optional cell pad dimensions
        offset: Optional offset from edge in micrometers
        skip: Optional spacing to next pad in micrometers
    """

    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    offset: Optional[float] = None
    skip: Optional[float] = None

    def copy(self) -> Layout:
        """
        Create a shallow copy of this Layout.

        :return: New Layout instance with same attributes
        :rtype: Layout
        """
        return Layout(
            bond_pad=self.bond_pad,
            cell_pad=self.cell_pad,
            offset=self.offset,
            skip=self.skip,
        )


@dataclass(frozen=False)
class PadDef:
    """
    Configuration-time pad description.

    This is the user-facing representation of a pad, containing logical
    information about the pad's purpose, direction, and configuration.
    Physical details (indices, banks) are computed later by PadRing.

    Attributes:
        name: Unique pad name (required)
        type: Pad type/direction (required)
        mapping: Physical edge placement (top/bottom/left/right)
        layout_index: Index for ordering pads on same edge
        layout: Physical layout attributes
        layers: Optional list of metal layers
        properties: Additional key-value properties
        active: Active level (high/low)
        orient: Physical orientation
        driven_manually: Whether pad is manually driven (not auto-generated)
        keep_internal: Whether to keep internal signals
        skip: Whether to skip this pad
        constant_attribute: Whether pad has constant attributes

    Raises:
        ValidationError: If validation fails (invalid type, mapping, orientation,
                        or if bond_pad defined without cell_pad)
    """

    name: str
    type: PadType
    mapping: Optional[PadMapping] = None
    layout_index: Optional[int] = 0
    layout: Optional[Layout] = None
    layers: Optional[List[str]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    active: Optional[str] = PadActive.HIGH.value
    orient: Optional[Orientation] = None
    driven_manually: Optional[bool] = False
    keep_internal: Optional[bool] = None
    skip: Optional[bool] = None
    constant_attribute: Optional[bool] = None

    def __post_init__(self):
        _assert_type(self.type, f"PadDef '{self.name}'")
        _assert_mapping(self.mapping, f"PadDef '{self.name}'")
        _assert_orientation(self.orient, f"PadDef '{self.name}'")
        if self.layout is not None:
            self.layout = (
                self.layout.copy() if isinstance(self.layout, Layout) else None
            )
        if (
            self.layout is not None
            and self.layout.bond_pad is not None
            and self.layout.cell_pad is None
        ):
            raise ValidationError(
                f"PadDef '{self.name}': bond_pad is defined but cell_pad is not."
            )

    def is_bond_pad_defined(self) -> bool:
        """Check if bond pad dimensions are defined."""
        return self.layout.bond_pad is not None

    def is_cell_pad_defined(self) -> bool:
        """Check if cell pad dimensions are defined."""
        return self.layout.cell_pad is not None


@dataclass(frozen=False)
class RangePad(PadDef):
    """
    Generates multiple similar pads with indexed names.

    Used for creating groups of pads like gpio_0, gpio_1, gpio_2, etc.
    Automatically expands into individual PadDef instances.

    Attributes:
        num: Number of pads to generate
        offset: Starting index for naming

    Example:
        RangePad(name="gpio", type=PadType.INOUT, num=8, offset=0)
        generates: gpio_0, gpio_1, ..., gpio_7

    Raises:
        ValidationError: If offset is negative
    """

    num: int = 1
    offset: Optional[int] = 0

    def __post_init__(self):
        super().__post_init__()
        if self.offset < 0:
            raise ValidationError(
                f"RangePads '{self.name}': invalid range parameters. Got start_index={self.offset}"
            )
        # create list of pad defs based on range
        pad_defs = []
        for i in range(self.offset, self.offset + self.num):
            pad_name = f"{self.name}_{i}"
            pad_defs.append(
                PadDef(
                    name=pad_name,
                    type=self.type,
                    mapping=self.mapping,
                    layout_index=self.layout_index,
                    layout=self.layout.copy() if self.layout is not None else None,
                    layers=self.layers,
                    properties=self.properties.copy(),
                    orient=self.orient,
                )
            )
        self.pad_defs = pad_defs  # store generated pad defs


class SinglePad(PadDef):
    """
    A simple single pad with no special behavior.

    This is a convenience class to make the type hierarchy explicit,
    but functionally identical to PadDef.
    """

    pass


@dataclass(frozen=False)
class MultiplexedPad(PadDef):
    """
    Pad with multiple mux options.

    Allows a single physical pad to be configured for different functions
    at runtime via multiplexing.

    Attributes:
        alts: List of (alternative_name, alternative_PadDef) tuples

    Example:
        MultiplexedPad(
            name="pad_mux_0",
            type=PadType.INOUT,
            alts=[("spi_mosi", spi_pad), ("gpio_5", gpio_pad)]
        )
    """

    alts: Optional[List[Tuple[str, PadDef]]] = None  # List of (alt_name, alt_type)


@dataclass(frozen=False)
class PadGroup:
    """
    System-level pad configuration containing all pads and global settings.

    This is the top-level configuration object that holds:
    - Individual pad definitions (PadDef instances)
    - Physical/layout properties (dimensions, offsets, spacing)
    - Shared dimension definitions

    Both HJSON and Python configurations are loaded into a PadGroup, ensuring
    a common internal representation regardless of configuration format.

    Attributes:
        name: Name of this pad group
        physical_properties: Global physical properties dictionary
        pad_edge_offset: Offset from die edge to pad cells
        bondpad_edge_offset: Offset from die edge to bond pads
        fp_dim: Floorplan dimensions (die size)
        bp_spacing: Bond pad spacing
        cell_spacing: Cell pad spacing
        pad_attribute: Pad attribute configuration
        bits: Attribute bit range specification
        pads: List of pad definitions (populated via add_pad)
        dimensions: Dictionary of shared dimension definitions

    Note:
        If any required physical properties are missing, all physical
        properties are set to None with a warning.
    """

    name: str = ""
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    pad_edge_offset: Optional[float] = None
    bondpad_edge_offset: Optional[float] = None
    fp_dim: Optional[Dimension] = None
    bp_spacing: Optional[float] = None
    cell_spacing: Optional[float] = None
    pad_attribute: Optional[Dict[str, Any]] = None
    # could be a better type than str
    bits: Optional[str] = None

    # internal state – user CANNOT pass these in __init__
    pads: List[PadDef] = field(default_factory=list, init=False)
    dimensions: Dict[str, Dimension] = field(default_factory=dict, init=False)

    def __post_init__(self):

        # --- check global physical fields ---
        global_missing = (
            self.pad_edge_offset is None
            or self.bondpad_edge_offset is None
            or self.fp_dim is None
        )
        if global_missing:
            # ANSI bright yellow warning
            warning = (
                "\033[93m[PadGroup WARNING] One or more physical attributes or "
                "layout dimensions are missing. All physical properties are "
                "being set to None.\033[0m"
            )

            # print all that are missing
            if self.pad_edge_offset is None:
                warning += "\033[93m\n - pad_edge_offset is missing\033[0m"
            if self.bondpad_edge_offset is None:
                warning += "\033[93m\n - bondpad_edge_offset is missing\033[0m"
            if self.fp_dim is None:
                warning += "\033[93m\n - fp_dim is missing\033[0m"

            print(warning)
            # wipe globals
            self.pad_edge_offset = None
            self.bondpad_edge_offset = None
            self.fp_dim = None
            self.bp_spacing = None
            self.cell_spacing = None
            # (optional) also wipe physical_properties
            self.physical_properties = {}

    def add_pad(self, pad: PadDef) -> None:
        """
        Add a pad definition to this group.

        Handles RangePad expansion and layout dimension registration.

        :param PadDef pad: Pad definition to add
        :raises ValidationError: If a pad with the same name already exists
        """
        if any(existing_pad.name == pad.name for existing_pad in self.pads):
            raise ValidationError(
                f"PadGroup '{self.name}': pad with name '{pad.name}' already exists."
            )

        if pad.layout is not None:
            self.add_layout(pad)
        if isinstance(pad, RangePad):
            pads = pad.pad_defs
            self.pads.extend(pads)
        else:
            self.pads.append(pad)

    def get_physical_attributes(self):
        """
        Build physical attributes dictionary for template generation.

        Returns None if no floorplan dimensions are defined, otherwise
        returns a dictionary with floorplan_dimensions, edge_offset,
        spacing, and dimensions.

        :return: Physical attributes dictionary or None
        :rtype: dict or None
        """

        if self.fp_dim is None:
            return None

        def get_dim_dict(dim: Dimension) -> Dict[str, Any]:
            return {
                key: value
                for key, value in (("width", dim.width), ("length", dim.length))
                if value is not None
            }

        dimensions: Dict[str, Dict[str, Any]] = {}

        def add_dim_entry(
            dimensions: Dict[str, Dict[str, Any]], key: str, dim: Dimension | None
        ) -> None:
            if dim is None:
                return
            d = get_dim_dict(dim)
            if d:
                dimensions[key] = d

        for name, dimension in self.dimensions.items():
            # Use the dimension name directly from the Dimension object
            add_dim_entry(dimensions, dimension.name, dimension)

        pa = {
            "floorplan_dimensions": {
                "width": self.fp_dim.width,
                "length": self.fp_dim.length,
            },
            "edge_offset": {
                "bondpad": self.bondpad_edge_offset,
                "pad": self.pad_edge_offset,
            },
            "spacing": {
                "bondpad": self.bp_spacing,
            },
            "dimensions": dimensions,
        }

        if self.cell_spacing is not None:
            pa["spacing"]["cell"] = self.cell_spacing

        return pa

    def get_multiplexed_pads(self) -> List[MultiplexedPad]:
        """
        Get all multiplexed pads in this group.

        :return: List of MultiplexedPad instances
        :rtype: List[MultiplexedPad]
        """
        return [pad for pad in self.pads if isinstance(pad, MultiplexedPad)]

    def get_pads(self) -> List[PadDef]:
        """
        Get all pads.

        :return: List of all pads
        :rtype: List[PadDef]
        """
        return self.pads

    def add_layout(self, padDef: PadDef) -> None:
        """Add dimensions from a PadDef's layout to the dimensions dictionary."""
        if padDef.layout is None:
            return

        # Add cell_pad dimension if present
        if (
            padDef.layout.cell_pad is not None
            and padDef.layout.cell_pad.name is not None
        ):
            cell_name = padDef.layout.cell_pad.name
            if cell_name in self.dimensions:
                if self.dimensions[cell_name] != padDef.layout.cell_pad:
                    raise ValidationError(
                        f"PadGroup '{self.name}': dimension with name '{cell_name}' already exists."
                    )
            else:
                self.dimensions[cell_name] = padDef.layout.cell_pad

        # Add bond_pad dimension if present
        if (
            padDef.layout.bond_pad is not None
            and padDef.layout.bond_pad.name is not None
        ):
            bond_name = padDef.layout.bond_pad.name
            if bond_name in self.dimensions:
                if self.dimensions[bond_name] != padDef.layout.bond_pad:
                    raise ValidationError(
                        f"PadGroup '{self.name}': dimension with name '{bond_name}' already exists."
                    )
            else:
                self.dimensions[bond_name] = padDef.layout.bond_pad

    def _to_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return bool(v)

    def _build_dimensions(
        dimensions: Mapping[str, Mapping[str, Any]],
    ) -> Dict[str, Dimension]:
        """
        Build Dimension objects from HJSON dimensions subsection.

        Converts HJSON dimension specifications into Dimension objects
        with embedded names for later reference.

        :param dimensions: Dictionary mapping dimension names to their specs
        :return: Dictionary of Dimension objects
        :rtype: Dict[str, Dimension]

        Example input:
            {"PAD1": {"width": 75, "length": 75},
             "BONDPAD1": {"width": 70}}
        """
        dims: Dict[str, Dimension] = {}

        for name, dim in dimensions.items():
            # Create Dimension with name embedded
            dims[name] = Dimension(
                width=dim["width"], length=dim.get("length"), name=name
            )

        return dims

    def build_pad_group(cfg: Mapping[str, Any], name: str = "x_heep_top") -> PadGroup:
        """
        Build a PadGroup from HJSON configuration dictionary.

        This is the main entry point for loading pad configurations from HJSON.
        It constructs a PadGroup with all pads and physical properties.

        :param cfg: HJSON configuration dictionary
        :param str name: Name for the pad group
        :return: Constructed PadGroup with all pads configured
        :rtype: PadGroup

        Configuration structure expected:
            {
                "physical_attributes": {
                    "floorplan_dimensions": {"width": ..., "length": ...},
                    "edge_offset": {"pad": ..., "bondpad": ...},
                    "spacing": {"bondpad": ..., "cell": ...},
                    "dimensions": {"PAD1": {...}, "BONDPAD1": {...}}
                },
                "pads": {
                    "pad_name": {
                        "type": "input/output/inout/...",
                        "mapping": "top/bottom/left/right",
                        "layout_attributes": {...},
                        "mux": {...}  // optional for multiplexed pads
                    }
                }
            }
        """
        # -------------------------------------------------------------------------
        # Physical attributes (SAFE)
        # -------------------------------------------------------------------------
        pa = cfg.get("physical_attributes", {})

        attributes = cfg.get("attributes", None)

        attribute_bits = (
            attributes.get("bits") if isinstance(attributes, dict) else None
        )

        # ---- floorplan dimensions ----
        fp = pa.get("floorplan_dimensions")
        if fp is not None:
            fp_dim = Dimension(width=fp.get("width", 0), length=fp.get("length"))
        else:
            fp_dim = None  # <-- safe default

        # ---- edge offsets ----
        edge_offset = pa.get("edge_offset", {})
        pad_edge_offset = edge_offset.get("pad")
        bondpad_edge_offset = edge_offset.get("bondpad")

        # ---- spacing ----
        spacing = pa.get("spacing", {})
        bp_spacing = spacing.get("bondpad")
        cell_spacing = spacing.get("cell")

        # ---- dimensions from "dimensions" ----
        dims = pa.get("dimensions")

        if dims is not None:
            dimensions = PadGroup._build_dimensions(dims)
        else:
            dimensions = {}  # no dimensions defined

        # -------------------------------------------------------------------------
        # Build the PadGroup with safe defaults
        # -------------------------------------------------------------------------
        pad_group = PadGroup(
            name=name,
            pad_edge_offset=pad_edge_offset,
            bondpad_edge_offset=bondpad_edge_offset,
            bp_spacing=bp_spacing,
            cell_spacing=cell_spacing,
            fp_dim=fp_dim,
            pad_attribute=attributes,
            bits=attribute_bits,
        )
        if pad_group is None:
            raise ValueError("PadGroup could not be created.")

        # pre-register dimensions only if present
        if dimensions:
            pad_group.dimensions.update(dimensions)

        # -------------------------------------------------------------------------
        # Pads section (SAFE)
        # -------------------------------------------------------------------------
        pads_cfg = cfg.get("pads", {})

        for pad_name, pad_info in pads_cfg.items():
            pad_type = PadType(pad_info.get("type", None))
            mapping_str = pad_info.get("mapping", None)
            mapping = PadMapping(mapping_str) if mapping_str is not None else None

            la = pad_info.get("layout_attributes", {})
            layout_index = la.get("index", 0)
            cell_name = la.get("cell")
            constant_attribute = PadGroup._to_bool(
                pad_info.get("constant_attribute", False)
            )

            # Build layout from dimensions
            if cell_name in dimensions:
                cell_dim = dimensions[cell_name]
                # Check for corresponding bond pad
            else:
                cell_dim = None

            bond_name = la.get("bondpad")
            if bond_name in dimensions:
                bond_dim = dimensions[bond_name]
            else:
                bond_dim = None

            pad_layout = (
                Layout(cell_pad=cell_dim, bond_pad=bond_dim)
                if (cell_dim or bond_dim)
                else None
            )

            pad_orient = (
                Orientation(la.get("orient").upper())
                if la.get("orient") is not None
                else None
            )

            active = pad_info.get("active", "high")
            driven_manually = PadGroup._to_bool(pad_info.get("driven_manually", False))
            keep_internal = PadGroup._to_bool(pad_info.get("keep_internal", False))

            base_kwargs = dict(
                name=pad_name,
                layout_index=layout_index,
                type=pad_type,
                mapping=mapping,
                layout=pad_layout,
                orient=(
                    Orientation(pad_orient) if pad_orient is not None else pad_orient
                ),
                active=active,
                driven_manually=driven_manually,
                keep_internal=keep_internal,
                constant_attribute=constant_attribute,
            )

            # ----------------- multiplexer case -----------------
            if "mux" in pad_info:
                alts_cfg = pad_info["mux"]
                alts = []
                for alt_name, alt_spec in alts_cfg.items():
                    alt_type = PadType(alt_spec.get("type", pad_type.value))
                    alts.append(
                        (
                            alt_name,
                            SinglePad(
                                name=alt_name,
                                layout_index=layout_index,
                                type=alt_type,
                                mapping=mapping,
                                layout=pad_layout,
                                orient=pad_orient,
                            ),
                        )
                    )

                pad_group.add_pad(MultiplexedPad(alts=alts, **base_kwargs))
                continue

            # ----------------- range pad case -----------------
            num = pad_info.get("num")
            if isinstance(num, int) and num > 1:
                offset = pad_info.get("num_offset", 0)
                pad_group.add_pad(RangePad(num=num, offset=offset, **base_kwargs))
                continue

            # ----------------- simple pad case -----------------
            pad_group.add_pad(SinglePad(**base_kwargs))

        return pad_group
