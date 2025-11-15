# pad_cfg.py (OOP version)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple, Mapping, Any

VALID_TYPES = {
    "input",
    "output",
    "inout",
    "bypass_input",
    "bypass_output",
    "bypass_inout",
}
VALID_MAPPING = {"top", "right", "bottom", "left"}

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
    width: int
    height: int
    
    def __post_init__(self):
        if self.width < 0 or self.height < 0:
            raise ValidationError(
                f"Dimension: width and height must be positive. Got width={self.width}, height={self.height}"
            )

@dataclass(frozen=True)
class PadDef:
    name: str
    type: str
    mapping: str
    bond_pad: Optional[Dimension] = None
    die_pad: Optional[Dimension] = None
    layers: Optional[List[str]] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _assert_type(self.type, f"PadDef '{self.name}'")
        _assert_mapping(self.mapping, f"PadDef '{self.name}'")
        
@dataclass(frozen=False)
class RangePads(PadDef):
    start_index: int
    end_index: int
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
                    bond_pad=self.bond_pad,
                    die_pad=self.die_pad,
                    layers=self.layers,
                    properties=self.properties.copy(),
                )
            )
        self.pad_defs = pad_defs  # store generated pad defs
class MultiplexedPads(PadDef):
    alts: List[Tuple[str, str]]  # List of (alt_name, alt_type)

    def __post_init__(self):
        super().__post_init__()
        for alt_name, alt_type in self.alts:
            _assert_type(alt_type, f"MultiplexedPads '{self.name}' alt '{alt_name}'")
            
@dataclass(frozen=False)
class PadGroup:
    name: str
    pads: List[PadDef] = field(default_factory=list)
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    
    def add_pad(self, pad: PadDef) -> None:
        if any(existing_pad.name == pad.name for existing_pad in self.pads):
            raise ValidationError(f"PadGroup '{self.name}': pad with name '{pad.name}' already exists.")
        if isinstance(pad, RangePads):
            self.pads.extend(pad.pad_defs)
        else:
            self.pads.append(pad)
    def get_multiplexed_pads(self) -> List[MultiplexedPads]:
        return [pad for pad in self.pads if isinstance(pad, MultiplexedPads)]
            
            
        

    
