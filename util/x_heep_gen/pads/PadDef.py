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

VALID_ORIENTATIONS = {o.value for o in Orientation}

VALID_MAPPINGS = {m.value for m in PadMapping}

VALID_ACTIVES = {a.value for a in PadActive}

# -------------------------- Base model ---------------------------------------


class ValidationError(ValueError):
    pass


def _assert_type(t: str, where: str) -> None:
    if t not in VALID_TYPES:
        raise ValidationError(
            f"{where}: invalid type '{t}'. Valid: {sorted(VALID_TYPES)}"
        )


def _assert_mapping(m: str, where: str) -> None:
    # is instance if PadMapping enum
    if not isinstance(m, PadMapping):
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {list(PadMapping)}"
        )
def _assert_orientation(o: str, where: str) -> None:
    if o not in VALID_ORIENTATIONS:
        raise ValidationError(
            f"{where}: invalid orientation '{o}'. Valid: {sorted(VALID_ORIENTATIONS)}"
        )


@dataclass(frozen=True)
class Dimension:
    width: int
    length: Optional[int] = None

    def __post_init__(self):
        if self.width < 0 or (self.length and self.length < 0):
            raise ValidationError(
                f"Dimension: width and length must be positive. Got width={self.width}, length={self.length}"
            )


@dataclass
class Layout:
    name: Optional[str] = None
    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    offset: Optional[float] = None
    skip: Optional[float] = None
    
    def copy(self) -> Layout:
        return Layout(
            name=self.name,
            bond_pad=self.bond_pad,
            cell_pad=self.cell_pad,
            offset=self.offset,
            skip=self.skip,
        )


@dataclass(frozen=False)
class PadDef:
    name: str
    type: str
    mapping: PadMapping
    layout_index: int = 0
    layout: Layout = field(default_factory=Layout)
    layers: Optional[List[str]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    active: str = "high"
    orient: Optional[str] = None
    driven_manually: bool = False
    keep_internal: Optional[bool] = None
    skip: Optional[bool] = None
    constant_attribute: Optional[bool] = None

    def __post_init__(self):
        _assert_type(self.type, f"PadDef '{self.name}'")
        _assert_mapping(self.mapping, f"PadDef '{self.name}'")
        _assert_orientation(self.orient, f"PadDef '{self.name}'")
        if self.layout is not None:
            self.layout = self.layout.copy()
        if self.layout.bond_pad is not None and self.layout.cell_pad is None:
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
                    layout=self.layout.copy(),
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
    pads: List[PadDef] = field(default_factory=list)
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    pad_edge_offset: Optional[float] = None
    bondpad_edge_offset: Optional[float] = None
    fp_dim: Optional[Dimension] = None
    bp_spacing: Optional[float] = None
    cell_spacing: Optional[float] = None
    pad_attribute: Optional[Dict[str, Any]] = None
    # could be a better type than str
    bits: Optional[str] = None
    layouts: Dict[str, Layout] = field(default_factory=dict)  # <-- FIXED

    def _post_init__(self):
        self.layouts: Optional[Dict[str, Layout]] = {}

    def add_pad(self, pad: PadDef) -> None:
        if any(existing_pad.name == pad.name for existing_pad in self.pads):
            raise ValidationError(
                f"PadGroup '{self.name}': pad with name '{pad.name}' already exists."
            )
        self.add_layout(pad)
        if isinstance(pad, RangePad):
            pads = pad.pad_defs
            self.pads.extend(pads)
        else:
            self.pads.append(pad)

    def get_physical_attributes(self):
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

        for name, layout in self.layouts.items():
            add_dim_entry(dimensions, name, layout.cell_pad)
            add_dim_entry(dimensions, f"BOND{name}", layout.bond_pad)

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
    
    def get_pads(self) -> Dict[str, List[PadDef]]:
        return sorted(self.pads, key=lambda pad: pad.layout_index)
        

    def add_layout(self, padDef: PadDef) -> None:
        print(self.layouts)
        for k, v in self.layouts.items():
            if k == padDef.layout.name:
                if v != padDef.layout:
                    raise ValidationError(
                        f"PadGroup '{self.name}': layout with name '{padDef.layout.name}' already exists."
                    )
                else:
                    return
        self.layouts[padDef.layout.name] = padDef.layout
