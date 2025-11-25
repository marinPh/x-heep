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
    #is instance if PadMapping enum
    if not isinstance(m, PadMapping):
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {list(PadMapping)}"
        )


@dataclass(frozen=True)
class Dimension:
    width: int
    name: Optional[str] = None
    height: Optional[int] = None
    
    

    def __post_init__(self):
        if self.width < 0 or (self.height and self.height < 0):
            raise ValidationError(
                f"Dimension: width and height must be positive. Got width={self.width}, height={self.height}"
            )


@dataclass
class Layout:
    name: Optional[str] = None
    bond_pad: Optional[Dimension] = None
    cell_pad: Optional[Dimension] = None
    index: Optional[int] = None
    offset: Optional[float] = None
    skip: Optional[float] = None
    

    def set_index(self, index: int) -> None:
        self.index = index


@dataclass(frozen=False)
class PadDef:
    name: str
    type: str
    mapping: PadMapping
    layout: Layout = field(default_factory=Layout)
    layers: Optional[List[str]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    orient: Optional[str] = None
    driven_manually: bool = False
    index: Optional[int] = None
    keep_internal: Optional[bool] = None
    skip : Optional[bool] = None
    constant_attribute: Optional[bool] = None

    def __post_init__(self):
        _assert_type(self.type, f"PadDef '{self.name}'")
        _assert_mapping(self.mapping, f"PadDef '{self.name}'")
        if self.layout.bond_pad is not None and self.layout.cell_pad is None:
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
class RangePad(PadDef):
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
    
class SinglePad(PadDef):
    # No additional fields needed for SinglePad
    pass


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
    cell_spacing: Optional[float] = None
    pad_attribute: Optional[Dict[str,Any]] = None
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
            pads = pad.set_index(len(self.pads))
            self.pads.extend(pads)
        else:
            pad.set_index(len(self.pads))
            self.pads.append(pad)
            
    def get_physical_attributes(self):
        pa = {"floorplan_dimensions": {"width": self.fp_dim.width, "length": self.fp_dim.height},
              "edge_offset": {"bondpad": self.edge_to_bp, "pad": self.edge_to_pad}, 
              "spacing": {"bondpad": self.bp_spacing,"pad":self.cell_spacing},
              "dimensions":{bondname:bonvalue
                            for name,layout in self.layouts.items()
                            for bondname,bonvalue in ((name,{
                                "width":layout.cell_pad.width,
                                "length":layout.cell_pad.height
                                }),(
                                    f"BOND{name}",{
                                "width":layout.cell_pad.width,
                                "length":layout.cell_pad.height
                                }))}
              }
        
        return pa


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
