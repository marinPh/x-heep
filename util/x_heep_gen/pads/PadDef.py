# pad_cfg.py (OOP version)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple, Mapping, Any
from .Pad import PadMapping

VALID_TYPES = {
    "input",
    "output",
    "inout",
    "bypass_input",
    "bypass_output",
    "bypass_inout",
}
VALID_MAPPING = {"top", "right", "bottom", "left"}

VALID_ORIENTATIONS = {
    "R0",
    "R90",
    "R180",
    "R270",
    "MX",
    "MY",
    "MX90",
    "MY90",
}

# -------------------------- Base model ---------------------------------------


class ValidationError(ValueError):
    pass


def _assert_type(t: str, where: str) -> None:
    if t not in VALID_TYPES:
        raise ValidationError(
            f"{where}: invalid type '{t}'. Valid: {sorted(VALID_TYPES)}"
        )


def _assert_mapping(m: str, where: str) -> None:
    if m not in VALID_MAPPING:
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {sorted(VALID_MAPPING)}"
        )


@dataclass(frozen=True)
class Dimension:
    name: Optional[str] = None
    width: int
    height: int

    def __post_init__(self):
        if self.width < 0 or self.height < 0:
            raise ValidationError(
                f"Dimension: width and height must be positive. Got width={self.width}, height={self.height}"
            )


@dataclass(frozen=True)
class Layout:
    name: Optional[str] = None
    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    orientation: Optional[str] = None
    index: Optional[int] = None
    offset: Optional[float] = None
    skip: Optional[float] = None

    def set_index(self, index: int) -> None:
        self.index = index


@dataclass(frozen=True)
class PadDef:
    name: str
    type: str
    mapping: PadMapping
    layout: Layout = field(default_factory=Layout)
    layers: Optional[List[str]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    driven_manually: bool = False
    index: Optional[int] = None

    def __post_init__(self):
        _assert_type(self.type, f"PadDef '{self.name}'")
        _assert_mapping(self.mapping, f"PadDef '{self.name}'")
        if self.bond_pad is not None and self.cell_pad is None:
            raise ValidationError(
                f"PadDef '{self.name}': bond_pad is defined but cell_pad is not."
            )

    def is_bond_pad_defined(self) -> bool:
        return self.bond_pad is not None

    def is_cell_pad_defined(self) -> bool:
        return self.cell_pad is not None

    def set_index(self, index: int) -> None:
        self.index = index


@dataclass(frozen=False)
class RangePads(PadDef):
    start_index: int = 0
    end_index: int = 1
    step: int = 1

    def __post_init__(self):
        super().__post_init__()
        if self.start_index < 0 or self.end_index < self.start_index or self.step <= 0:
            raise ValidationError(
                f"RangePads '{self.name}': invalid range parameters. Got start_index={self.start_index}, end_index={self.end_index}, step={self.step}"
            )
        # create list of pad defs based on range
        pad_defs = []
        for i in range(self.start_index, self.end_index + 1, self.step):
            pad_name = f"{self.name}_{i}"
            pad_defs.append(
                PadDef(
                    name=pad_name,
                    type=self.type,
                    mapping=self.mapping,
                    layout=self.layout,
                    layers=self.layers,
                    properties=self.properties.copy(),
                )
            )
        self.pad_defs = pad_defs  # store generated pad defs

    def set_index(self, offset: int) -> List[PadDef]:
        for i, pad in enumerate(self.pad_defs):
            pad.set_index(offset + i)
        return self.pad_defs


class MultiplexedPad(PadDef):
    alts: List[Tuple[str, str]]  # List of (alt_name, alt_type)

    def __post_init__(self):
        super().__post_init__()
        for alt_name, alt_type in self.alts:
            _assert_type(alt_type, f"MultiplexedPads '{self.name}' alt '{alt_name}'")


@dataclass(frozen=False)
class PadGroup:
    name: str = ""
    pads: List[PadDef] = field(default_factory=list)
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    edge_to_bp: Optional[float] = None
    edge_to_pad: Optional[float] = None
    fp_dim: Optional[Dimension] = None
    bp_spacing: Optional[float] = None
    bits: Optional[str] = None

    def add_pad(self, pad: PadDef) -> None:
        if any(existing_pad.name == pad.name for existing_pad in self.pads):
            raise ValidationError(
                f"PadGroup '{self.name}': pad with name '{pad.name}' already exists."
            )
        self.add_layout(pad)
        if isinstance(pad, RangePads):
            pads = pad.set_index(len(self.pads))
            self.pads.extend(pads)
        else:
            pad.set_index(len(self.pads))
            self.pads.append(pad)

    def get_multiplexed_pads(self) -> List[MultiplexedPad]:
        return [pad for pad in self.pads if isinstance(pad, MultiplexedPad)]

    def add_layout(self, padDef: PadDef) -> None:
        for k, v in self.layouts:
            if k == padDef.layout.name:
                if v != padDef.layout:
                    raise ValidationError(
                        f"PadGroup '{self.name}': layout with name '{padDef.layout.name}' already exists."
                    )
                else:
                    return
        padDef.layout.set_index(len(self.layouts))
        self.layouts[padDef.layout.name] = padDef.layout
