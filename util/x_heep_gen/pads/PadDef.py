# pad_cfg.py (OOP version)
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
    pass


def _assert_type(t: str, where: str) -> None:
    if not isinstance(t, PadType):
        raise ValidationError(f"{where}: invalid orientation is of type '{type(t)}'")


def _assert_mapping(m: str, where: str) -> None:
    # is instance if PadMapping enum
    if m is not None and not isinstance(m, PadMapping):
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {list(PadMapping)}"
        )


def _assert_orientation(o: Any, where: str) -> None:
    if o is not None and not isinstance(o, Orientation):
        raise ValidationError(f"{where}: invalid orientation is of type '{type(o)}'")


@dataclass(frozen=True)
class Dimension:
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
    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    offset: Optional[float] = None
    skip: Optional[float] = None

    def copy(self) -> Layout:
        return Layout(
            bond_pad=self.bond_pad,
            cell_pad=self.cell_pad,
            offset=self.offset,
            skip=self.skip,
        )


@dataclass(frozen=False)
class PadDef:
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
        return self.layout.bond_pad is not None

    def is_cell_pad_defined(self) -> bool:
        return self.layout.cell_pad is not None


@dataclass(frozen=False)
class RangePad(PadDef):
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
    # No additional fields needed for SinglePad
    pass


@dataclass(frozen=False)
class MultiplexedPad(PadDef):
    alts: Optional[List[Tuple[str, PadDef]]] = None  # List of (alt_name, alt_type)


@dataclass(frozen=False)
class PadGroup:
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
        return [pad for pad in self.pads if isinstance(pad, MultiplexedPad)]

    def get_pads(self) -> List[PadDef]:
        return sorted(self.pads, key=lambda pad: pad.layout_index)

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
        Build Dimension objects from the 'dimensions' subsection.

        Expects things like:
          PAD1, BONDPAD1, PAD2, BONDPAD2, ...
        Each dimension gets its name embedded in the Dimension object.
        """
        dims: Dict[str, Dimension] = {}

        for name, dim in dimensions.items():
            # Create Dimension with name embedded
            dims[name] = Dimension(
                width=dim["width"], length=dim.get("length"), name=name
            )

        return dims

    def build_pad_group(cfg: Mapping[str, Any], name: str = "x_heep_top") -> PadGroup:
        # -------------------------------------------------------------------------
        # Physical attributes (SAFE)
        # -------------------------------------------------------------------------
        pa = cfg.get("physical_attributes", {})

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
